import subprocess
from dotenv import load_dotenv
from os import environ, listdir
from pathlib import Path
from tomllib import load as loadToml

import logging

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

from typing import Literal

from enum import Enum



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
        logger.info( f"Searching in {search_path}" )
        for child in listdir( search_path ):
            logger.info( f"checking {child}")
            if Path(search_path, child).is_file(): 
                logger.info("Is a file and not a dir.")
                continue
            if not child.startswith(("touchdesigner", "TouchDesigner")): 
                logger.info("Does not start with TouchDesigner, so not a valid install folder.")
                continue
            if len( split_elements := child.split(".")) != 3: 
                logger.info("Name needs to follow TouchDesigner.Version.Build")
                continue
            version, build = split_elements[1], split_elements[2]
            td_folder.append(
                ( version, build, f"{version}.{build}", Path( search_path, child ) )
            )
    logger.info(f"Found the follwowing potential folder, {td_folder}")
    if not td_folder: raise Exception("Could not find any valid TouchDesigner installfolder. Make sure the correct version is installed.")

    if mode == SearchMode.STRICT.value:
        for element in td_folder:
            logger.info(f"Checking required {td_version} against {element[2]}")
            if td_version == element[2]: return element[3]
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
    
    raise Exception("Could not find a fitting installation to satisify {td_version} in {mode} mode.")

def launch(backend:Literal["TouchDesigner", "TouchPlayer"]):
    with Path("pyproject.toml").open("rb") as project_file:
        projectData = loadToml( project_file )


    executeableName = f"{backend}.exe" # Sorry mac lol.
    tool_config = projectData.get("tool", {}).get("touchdesigner", {})
    project_file = tool_config.get("projectfile", "Project.toe")
    search_mode = tool_config.get("enforce-version", "latest-build")
    tdFolder = search_touchdesigner_folder(search_mode)
    logger.info(f"Found installation {tdFolder}")
    load_dotenv()
    tdExecuteable = Path(tdFolder, "bin", executeableName)
    logger.info(f"Executing {tdExecuteable} with {project_file}")
    tdProcess = subprocess.Popen([str(tdExecuteable),  project_file])
    logger.info(f"Process Terminated. Exiting. ReturnCode { tdProcess.wait() }")
   

def designer():
    
    launch("TouchDesigner")

def editor():
    environ["NODE_ENV"] = "production"
    launch("TouchDesigner")

def player():
    environ["NODE_ENV"] = "production"
    launch("TouchPlayer")
