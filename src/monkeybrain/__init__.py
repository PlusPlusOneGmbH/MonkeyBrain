


from typing import Literal

from functools import cache
import subprocess
from os import environ
from dotenv import load_dotenv

from pathlib import Path

from .tools.project import get_tool_config, load_project_config
from .tools.search import search_touchdesigner_folder

import logging
logger = logging.getLogger()
log_level = getattr(logging, environ.get("TOUCHLAUNCH_LOGLEVEL", "INFO"), None) or logging.INFO
logging.basicConfig(level=log_level)



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