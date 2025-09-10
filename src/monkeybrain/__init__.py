from typing import Literal, Union
from enum import Enum
from functools import cache

import subprocess
from os import environ, listdir

from dotenv import load_dotenv

from pathlib import Path
from tomllib import load as loadToml

import logging
logger = logging.getLogger()
log_level = getattr(logging, environ.get("TOUCHLAUNCH_LOGLEVEL", "INFO"), None) or logging.INFO
logging.basicConfig(level=log_level)

class SearchMode(Enum):
    STRICT          = "strict"
    CLOSESTBUILD    = "closest-build"
    LATESTBUILD     = "latest-build"
    LATESTVERSION   = "latest-version"


def search_touchdesigner_folder(mode:SearchMode) -> Path:
    logger.info(f"Searching for TouchDesigner Installs in mode {mode}")

    td_search_paths = [ "C:\\Program Files\\Derivative" ] + environ.get("TD_INSTALLSEARCHPATH", "").split(":")
    td_version = Path(".touchdesigner-version").read_text()
    td_folder = []
    
    for search_path in [search_path for search_path in td_search_paths if search_path and Path(search_path).is_dir()]:
        
        logger.debug( f"Searching in {search_path}" )
        for child in listdir( search_path ):
            logger.debug( f"checking {child}")
            if Path(search_path, child).is_file(): 
                logger.debug("Is a file and not a dir.")
                continue
            if not child.startswith(("touchdesigner", "TouchDesigner")): 
                logger.debug("Does not start with TouchDesigner, so not a valid install folder.")
                continue
            if len( split_elements := child.split(".")) != 3: 
                logger.debug("Name needs to follow TouchDesigner.Version.Build")
                continue
            version, build = split_elements[1], split_elements[2]
            td_folder.append(
                ( version, build, f"{version}.{build}", Path( search_path, child ) )
            )
    logger.debug(f"Found the follwowing potential folder, {td_folder}")
    if not td_folder: raise Exception("Could not find any valid TouchDesigner installfolder. Make sure the correct version is installed.")

    if mode == SearchMode.STRICT.value:
        for element in td_folder:
            logger.debug(f"Checking required {td_version} against {element[2]}")
            if td_version == element[2]: return element[3]
            logger.error(f"Could not find path for {td_version} in strict mode. Install specific version or change mode.")
            raise Exception(f"Could not find path for {td_version} in strict mode. Install specific version or change mode.")
    
    required_version, reuquired_build = td_version.split(".")
    
    if mode == SearchMode.CLOSESTBUILD.value:
        return sorted(
            [ folder for folder 
             in td_folder 
             if folder[0] == required_version 
             and float(folder[1]) >= float(reuquired_build) ],
             key = lambda value: float( value[2] ),
             reverse = False
        )[0][3]

    if mode == SearchMode.LATESTBUILD.value:
        return sorted(
            [ folder for folder 
             in td_folder 
             if folder[0] == required_version 
             and float(folder[1]) >= float(reuquired_build) ],
             key = lambda value: float( value[2] ),
             reverse = True
        )[0][3]
    
    if mode == SearchMode.LATESTVERSION.value:
        logger.info("Searching for latest version.")
        return sorted(
            [ folder for folder 
             in td_folder 
             if float(folder[1]) >= float(reuquired_build) ],
             key = lambda value: float( value[2] ),
             reverse = True
        )[0][3]
    
    logger.error(f"Could not find a fitting installation to satisify {td_version} in {mode} mode.")
    raise Exception(f"Could not find a fitting installation to satisify {td_version} in {mode} mode.")

@cache
def load_project_config():
    with Path("pyproject.toml").open("rb") as project_file:
        return loadToml( project_file )

def get_tool_config( project_data:Union[dict, None] = None):
    _project_data = project_data or load_project_config()
    return _project_data.get("tool", {}).get("touchdesigner", {})

def launch(backend:Literal["TouchDesigner", "TouchPlayer"]):
    project_data        = load_project_config()
    executeableName     = f"{backend}.exe" # Sorry mac lol.
    tool_config         = get_tool_config( project_data= project_data )
    project_file        = tool_config.get("projectfile", "Project.toe")
    search_mode         = tool_config.get("enforce-version", "latest-build")
    tdFolder            = search_touchdesigner_folder(search_mode)

    logger.info(f"Found installation {tdFolder}.")

    envLoaded = load_dotenv()
    if envLoaded: logger.info("Loaded .env file.")

    tdExecuteable = Path(tdFolder, "bin", executeableName)
    logger.info(f"Executing {tdExecuteable} with {project_file}")
    tdProcess = subprocess.Popen([str(tdExecuteable),  project_file])
    logger.info(f"Process Terminated. Exiting. ReturnCode { tdProcess.wait() }")


def read_packagefolder_file():
    import os, re
    def replace_var(match):
        var_name = match.group(1)
        
        return os.environ[var_name] 
        
    result = []
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
def setup_vs_code_config(install_folder:str):
    Path(".vscode").mkdir(parents=True, exist_ok=True)

    with Path(".vscode/settings.json").open("a+t") as config_file:
        config_file.seek(0)
        try:
            current_config = json.load( config_file )
        except json.JSONDecodeError as e:
            logger.info("Creating new empty config for vscode. ")
            current_config = {}
        current_config["python.defaultInterpreterPath"] = str( Path( install_folder, "bin", "python.exe")) # Note that we are being windows exclusive here...
        current_extra_paths = current_config.setdefault("python.analysis.extraPaths", []) 
        for extra_path in read_packagefolder_file():
            
            if extra_path in current_extra_paths: continue
            current_extra_paths.insert(0, extra_path)
        current_config["python.analysis.extraPaths"] = current_extra_paths
        config_file.truncate(0)
        json.dump( current_config, config_file, indent=4 )


import urllib.request

def setup_project_files(td_branch = "stable"):
    if not (packagefolderfile:=Path(".packagefolder")).is_file():
        packagefolderfile.touch()
        packagefolderfile.write_text("""
# Lines starting with # will be ignored as comments.

# ${ gets converted in to ENV-Variable. }
${UV_PROJECT_ENVIRONMENT}/Lib/site-packages

project_packages
.venv/Lib/site-packages
                                     """.strip())
        
    if not (touchdesignerversionfle:=Path(".touchdesigner-version")).is_file():
        touchdesignerversionfle.touch()
        # Lets fetch the latest version from http://www.derivative.ca/099/Downloads/Files/history.txt
        try:
            link = "http://www.derivative.ca/099/Downloads/Files/history.txt"
            response = urllib.request.urlopen(link)
            responsetext = response.read().decode()
            stable, experimental = responsetext.strip().split("\n")
            versioninfo = experimental if td_branch == "experimental" else stable

            touchdesignerversionfle.write_text( versioninfo.split("\t")[3] )

        except Exception as e:
            logger.info(f"Could not fetch data. Writing 2023.1200. {e}")
            # If not, lets just write a version I know works. 
            touchdesignerversionfle.write_text("2023.12000")


# calls

import argparse
def entry():
    parser = argparse.ArgumentParser(
                    prog='Monkeybrain',
                    description='Manage TD installations.',
                    epilog='Makes setting projects up bearable..')
    
    parser.add_argument('command', choices = ["init", "init.code", "init.files", "edit", "designer", "player"])
    parsed_arguments = parser.parse_args()
    match parsed_arguments.command:
        case "init":
            init()
        case "init.code":
            setup_code()
        case "init.files":
            setup_files()
        case "edit":
            editor()
        case "designer":
            designer()
        case "player":
            player()

def designer():
    environ["NODE_ENV"] = "production"
    launch("TouchDesigner")

def editor():
    launch("TouchDesigner")

def player():
    environ["NODE_ENV"] = "production"
    launch("TouchPlayer")

def setup_code():
    setup_vs_code_config( 
        str( 
            search_touchdesigner_folder(
                get_tool_config().get("enforce-version", "latest-build")
                ) 
            )
    )

def setup_files():
    setup_project_files()

def init():
    setup_files()
    setup_code()