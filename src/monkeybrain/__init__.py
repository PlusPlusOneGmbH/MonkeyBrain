


from typing import Literal

from functools import cache
import subprocess
from os import environ
from dotenv import load_dotenv

from pathlib import Path

from .tools.project import get_tool_config, load_project_config
from .tools.search import search_touchdesigner_folder

from .tools.log import use_logger
logger = use_logger()


import logging
logger = logging.getLogger()
log_level = getattr(logging, environ.get("TOUCHLAUNCH_LOGLEVEL", "INFO"), None) or logging.INFO
logging.basicConfig(level=log_level)

from typing import Optional

def launch(backend:Literal["TouchDesigner", "TouchPlayer"], _project_file:Optional[str], gpuperform_index:Optional[int] ):
    project_data        = load_project_config()
    executeableName     = f"{backend}.exe" # Sorry mac lol.
    tool_config         = get_tool_config( project_data = project_data )
    project_file        = _project_file or tool_config.get("projectfile", "Project.toe")
    search_mode         = tool_config.get("enforce-version", "latest-build")
    td_installation     = search_touchdesigner_folder(search_mode)

    logger.info(f"Found installation {td_installation}.")

    envLoaded = load_dotenv()
    if envLoaded: logger.info("Loaded .env file.")

    tdExecuteable = Path(td_installation["folder"], "bin", executeableName)
    arguments = [project_file]
    if gpuperform_index is not None:
        arguments = ["-gpuformonitor", gpuperform_index] + arguments
    logger.info(f"Executing {tdExecuteable} with {project_file}")
    tdProcess = subprocess.Popen([str(tdExecuteable)] + arguments) 
    logger.info(f"Process Terminated. Exiting. ReturnCode { tdProcess.wait() }")



# calls

import argparse
def entry():
    parser = argparse.ArgumentParser(
                    prog='Monkeybrain',
                    description='Manage TD installations.',
                    epilog='Makes setting projects up bearable..')
    
    parser.add_argument('command', choices = ["init", "init.code", "init.files", "edit", "designer", "player"])
    parser.add_argument("--gpuformonitor", help= "Passes gpu affinty as an integer of the screen.", required=False )
    parser.add_argument("--file", "-f", help = "Pass optional file")
    
    parsed_arguments = parser.parse_args()
    
    command = "TouchDesigner"

    try:
        match parsed_arguments.command:
            case "init":
                return init()
            case "init.code":
                return setup_code()
            case "init.files":
                return setup_files()
            case "edit":
                command = "TouchDesigner"
            case "designer"                 :
                environ["NODE_ENV"] = "production"
                command = "TouchDesigner"
            case "player":
                environ["NODE_ENV"] = "production"
                command = "TouchPlayer"
        return launch(
            command, 
            parsed_arguments.file, 
            parsed_arguments.gpuformonitor
        )
    except Exception as e:
        print("\n")
        logger.critical( f"Failed to run {parsed_arguments.command} for the following reason:\n{e}" )


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