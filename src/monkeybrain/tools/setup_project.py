
from pathlib import Path
from os import environ
from typing import Literal


from .log import use_logger
logger = use_logger()




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
                    enved_line = re.sub(r"\$\{([^}]+)\}", replace_var, line) # pyright: ignore[reportArgumentType] # Repalce ENV-Variables.
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
        current_config["python.defaultInterpreterPath"] = str( Path( install_definition["executeable"].parent, "python.exe" ) ) # Note that we are being windows exclusive here...
        current_extra_paths = current_config.setdefault("python.analysis.extraPaths", []) 

        for extra_path in read_packagefolder_file() + get_tool_config().get("TDPyEnvManagerContext", {}).get("extraPaths", []):
            if extra_path in current_extra_paths: continue
            current_extra_paths.insert(0, extra_path)


        env_name = get_tool_config().get("TDPyEnvManagerContext", {}).get("envName", [])
        current_extra_paths.append(
            f"{env_name}/Lib/site-packages"
        )
        
        current_config["python.analysis.extraPaths"] = list(set(current_extra_paths))
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




import toml
from .search import search_touchdesigner_folder
from os import listdir
from pathlib import Path
from shutil import copy

def setup_project_files():
    """
    Setup all files required to work with monkeybrain for a fullfledged project.
    
    """
    

    td_install = search_touchdesigner_folder(
            get_tool_config().get("enforce-version", "latest-version")
    ) 

    pyproject = Path( "pyproject.toml" )
    current_pyproject:dict = toml.loads( pyproject.read_text() )

    projectfile = f"{current_pyproject['project']['name']}.toe"


    monkeybrain_settingsdict = current_pyproject.setdefault("tool", {}).setdefault("monkeybrain", {})
    monkeybrain_settingsdict.setdefault("touchdesigner-version",  td_install["string_value"] )
    monkeybrain_settingsdict.setdefault("enforce-version", "strict")
    
    if not Path(monkeybrain_settingsdict.get("projectfile", "")).is_file():
        # If the projectfile does not exist, we will overwrite it to an existing one or create one.
        logger.warning(f"Did not find a valid .toe file in settings.")
        for item in listdir("."):
            # Search for a toefile
            if item.endswith(".toe"): 
                projectfile = item
                logger.warning(f"Found existing .toe file, will use {item}.")
                break
        else:
            # if no toefiles are found, create one from the template.
            if not Path( projectfile ).is_file():
                template_source_path = Path(td_install["folder"], "Samples", "Setup", "Base", "NewProject.toe")
                copy( template_source_path, projectfile )
                logger.warning(f"Did not find a valid .toe in project, will generate empty from {template_source_path}")

        monkeybrain_settingsdict["projectfile"] = projectfile 

    env_manager_settingsdict = current_pyproject.setdefault("tool", {}).setdefault("touchdesigner", {}).setdefault("TDPyEnvManagerContext", {})

    env_manager_settingsdict["mode"] = "Python vEnv"
    env_manager_settingsdict["envName"] = ".venv"
    env_manager_settingsdict["installPath"] = "."
    env_manager_settingsdict["extraPaths"] = [
        "src"
    ]

    pyproject.write_text( toml.dumps( current_pyproject ))
