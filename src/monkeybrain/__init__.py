


from typing import Literal, Union, TypedDict, List
from enum import Enum

from functools import cache
import subprocess
from os import environ, listdir

from dotenv import load_dotenv

from pathlib import Path

from .tools.project import get_project_touchdesigner_version, get_tool_config, load_project_config

import logging
logger = logging.getLogger()
log_level = getattr(logging, environ.get("TOUCHLAUNCH_LOGLEVEL", "INFO"), None) or logging.INFO
logging.basicConfig(level=log_level)

class SearchMode(Enum):
    STRICT          = "strict"
    CLOSESTBUILD    = "closest-build"
    LATESTBUILD     = "latest-build"
    LATESTVERSION   = "latest-version"



class TouchdesignerInstall(TypedDict):
    version:int
    build:int
    numeric_value:float
    string_value:str
    folder:Path
    executeable:Path

from .tools.file_meta import get_file_metadata
def list_touchdesigner_installs() -> List[TouchdesignerInstall]:
    td_search_paths = [ "C:\\Program Files\\Derivative" ] + [ pathstring.strip() for pathstring in environ.get("TD_INSTALLSEARCHPATH", "").split(";") ]
    td_installations:List[TouchdesignerInstall] = []
    for search_location in [Path(_search_location) for _search_location in td_search_paths]:
        if not search_location.is_dir(): continue
        for install_location in [ Path(search_location, _install_location) for _install_location in listdir( search_location )]:
            if not install_location.is_dir(): continue
            exeucteable = Path( install_location, "bin", "TouchDesigner.exe")
            version_meta_data = get_file_metadata( exeucteable, ["Product version"]).get("Product version", "0.0.0.0")
            _, __, version, build = version_meta_data.split(".")
            td_installations.append({
                "version" : int(version),
                "build" : int( build ),
                "numeric_value" : float(f"{version}.{build}"),
                "string_value" : f"{version}.{build}",
                "executeable" : exeucteable,
                "folder" : install_location
            })
    return td_installations



def search_touchdesigner_folder(mode:SearchMode) -> TouchdesignerInstall:
    logger.info(f"Searching for TouchDesigner Installs in mode {mode}")

    td_installs = list_touchdesigner_installs()
    
    target_td_version = get_project_touchdesigner_version()

    if not td_installs: raise Exception("""
                                        Could not find any valid TouchDesigner installfolder. 
                                        Make sure the correct version is installed. 
                                        You can add additional search paths using TD_INSTALLSEARCHPATH as ; seperated paths.
                                        """)

    if mode == SearchMode.STRICT.value:
        for element in td_installs:
            logger.debug(f"Checking required {target_td_version} against {element}")
            if target_td_version == element["string_value"]: return element
            logger.error(f"Could not find path for {target_td_version} in strict mode. Install specific version or change mode.")
            raise Exception(f"Could not find path for {target_td_version} in strict mode. Install specific version or change mode.")
    
    _required_version, _reuquired_build = target_td_version.split(".")
    required_version = int(_required_version)
    reuquired_build = int( _reuquired_build )

    _sorted = []

    if mode == SearchMode.CLOSESTBUILD.value:
        _sorted =  sorted(
            [ installation for installation 
             in td_installs 
             if installation["version"] == required_version
             and installation["build"] >= reuquired_build ],
             key = lambda value: float( value["numeric_value"] ),
             reverse = False
        )

    if mode == SearchMode.LATESTBUILD.value:
        _sorted = sorted(
            [ installation for installation 
             in td_installs 
             if installation["version"] == required_version 
             and installation["build"] >= reuquired_build ],
             key = lambda value: float( value["numeric_value"] ),
             reverse = True
        )
    
    if mode == SearchMode.LATESTVERSION.value:
        logger.info("Searching for latest version.")
        _sorted = sorted(
            [ installation for installation 
             in td_installs 
             if installation["build"] >= reuquired_build ],
             key = lambda value: float( value["numeric_value"] ),
             reverse = True
        )
    if not _sorted:
        logger.error(f"Could not find a fitting installation to satisify {target_td_version} in {mode} mode.")
        raise Exception(f"Could not find a fitting installation to satisify {target_td_version} in {mode} mode.")
    
    return _sorted[0]


def launch(backend:Literal["TouchDesigner", "TouchPlayer"]):
    project_data        = load_project_config()
    executeableName     = f"{backend}.exe" # Sorry mac lol.
    tool_config         = get_tool_config( project_data = project_data )
    project_file        = tool_config.get("projectfile", "Project.toe")
    search_mode         = tool_config.get("enforce-version", "latest-build")
    td_installation     = search_touchdesigner_folder(search_mode)

    logger.info(f"Found installation {td_installation}.")

    envLoaded = load_dotenv()
    if envLoaded: logger.info("Loaded .env file.")

    tdExecuteable = Path(td_installation["folder"], "bin", executeableName)
    logger.info(f"Executing {tdExecuteable} with {project_file}")
    tdProcess = subprocess.Popen([str(tdExecuteable),  project_file])
    logger.info(f"Process Terminated. Exiting. ReturnCode { tdProcess.wait() }")



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


from .tools.setup_project import setup_vs_code_config, setup_project_files
def setup_code():
    setup_vs_code_config( 
        search_touchdesigner_folder(
            get_tool_config().get("enforce-version", "latest-build")
        ) 
    )

def setup_files():
    setup_project_files()

def init():
    setup_files()
    setup_code()