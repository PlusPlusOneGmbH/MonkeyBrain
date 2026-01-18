
from pathlib import Path
from os import environ
from typing import Literal


import logging
logger = logging.getLogger()
log_level = getattr(logging, environ.get("TOUCHLAUNCH_LOGLEVEL", "INFO"), None) or logging.INFO
logging.basicConfig(level=log_level)




def read_packagefolder_file():
    import os, re
    def replace_var(match):
        var_name = match.group(1)
        if len( env_naming := var_name.split("||") ) == 2:
            return os.environ.get( env_naming[0], env_naming[1] )
        else:
            return os.environ[env_naming[0]]
        
    result = []
    if Path( ".packagefolder" ).is_file():
        with open(".packagefolder", "a+t") as package_folder_file:
            package_folder_file.seek(0)
            for _line in reversed( package_folder_file.readlines() ):
                line = _line.strip()
                if line.startswith("#"): continue # skip comments
                try:
                    enved_line = re.sub(r"\$\{([^}]+)\}", replace_var, line) # Repalce ENV-Variables.
                except KeyError:
                    continue
                if not enved_line: continue 
                result.append(enved_line)
    return result

import json
from .search import TouchdesignerInstall
from .project import get_tool_config

def setup_vs_code_config(install_definition:TouchdesignerInstall):
    Path(".vscode").mkdir(parents=True, exist_ok=True)

    with Path(".vscode/settings.json").open("a+t") as config_file:
        config_file.seek(0)
        try:
            current_config = json.load( config_file )
        except json.JSONDecodeError as e:
            logger.info("Creating new empty config for vscode. ")
            current_config = {}
        current_config["python.defaultInterpreterPath"] = str( install_definition["executeable"] ) # Note that we are being windows exclusive here...
        current_extra_paths = current_config.setdefault("python.analysis.extraPaths", []) 

        for extra_path in read_packagefolder_file() + get_tool_config().get("TDPyEnvManagerContext", {}).get("extraPaths", []):
            if extra_path in current_extra_paths: continue
            current_extra_paths.insert(0, extra_path)
        current_config["python.analysis.extraPaths"] = current_extra_paths
        config_file.truncate(0)
        json.dump( current_config, config_file, indent=4 )


def get_latest_td_version( td_branch:Literal["stable", "experimental"]):
    try:
        link = "http://www.derivative.ca/099/Downloads/Files/history.txt"
        response = urllib.request.urlopen(link)
        responsetext = response.read().decode()
        stable, experimental = responsetext.strip().split("\n")
        versioninfo = experimental if td_branch == "experimental" else stable

        return versioninfo.split("\t")[3]

    except Exception as e:
        logger.info(f"Could not fetch data. Writing 2025.32050. {e}")
        # If not, lets just write a version I know works. 
        return "2025.32050"

from typing import Literal
def setup_project_files( td_branch:Literal["stable", "experimental"] = "stable"):
    td_version = sorted( list_touchdesigner_installs() or [{"string_value" : "", "numeric_value" : -1000}] , key = lambda value: value["numeric_value"], reverse=True )
    target_td_version:str =  td_version[0]["string_value"] or get_latest_td_version(td_branch) # pyright: ignore[reportAssignmentType]
    logger.info(f"setup projectfile with target TD_Version {target_td_version}")
    if float( target_td_version ) > 2025.32050:
        # This branch will only make sense once everything can live nicely inside the pyproject.toml. Sooon!
        return setup_project_files_v2( target_td_version )
    return setup_project_files_v1( target_td_version )


import urllib.request
def setup_project_files_v1( td_version:str ):
    """
    Generates a .packagefolder and .touchdesigner-version file. Yaih!
    
    """
    if not (packagefolderfile:=Path(".packagefolder")).is_file():
        packagefolderfile.touch()
        packagefolderfile.write_text("""
# Lines starting with # will be ignored as comments.

# ${ gets converted in to ENV-Variable. } use || to define a default value
${UV_PROJECT_ENVIRONMENT||.venv}/Lib/site-packages
project_packages
                                     """.strip())
        
    if not (touchdesignerversionfle:=Path(".touchdesigner-version")).is_file():
        touchdesignerversionfle.touch()
        # Lets fetch the latest version from http://www.derivative.ca/099/Downloads/Files/history.txt
        touchdesignerversionfle.write_text( td_version )


import toml
from .search import list_touchdesigner_installs
from os import listdir
def setup_project_files_v2(td_version:str):
    """
    Generates a .packagefolder and .touchdesigner-version file. Yaih!
    
    """

    pyproject = Path( "pyproject.toml" )
    current_pyproject:dict = toml.loads( pyproject.read_text() )

    monkeybrain_settingsdict = current_pyproject.setdefault("tool", {}).setdefault("monkeybrain", {})
    monkeybrain_settingsdict.setdefault("touchdesigner-version",  td_version )
    monkeybrain_settingsdict.setdefault("enfore-version", "strict")
    projectfile = "Project.toe"
    for item in listdir("."):
        if item.endswith(".toe"): projectfile = item
    monkeybrain_settingsdict.setdefault("projectfile", projectfile )

    env_manager_settingsdict = current_pyproject.setdefault("tool", {}).setdefault("touchdesigner", {}).setdefault("TDPyEnvManagerContext", {})
    env_manager_settingsdict["mode"] = "Python vEnv"
    env_manager_settingsdict["envName"] = ".venv"
    env_manager_settingsdict["installPath"] = "."
    env_manager_settingsdict["extraPaths"] = [
        "src", "${UV_PROJECT_ENVIRONMENT}/Lib/site-packages", ".venv/Lib/site-packages"
    ]

    pyproject.write_text( toml.dumps( current_pyproject ))
