import subprocess
from dotenv import load_dotenv
from os import environ
from pathlib import Path
from tomllib import load as loadToml

from typing import Literal


def launch(backend:Literal["TouchDesigner", "TouchPlayer"]):
    with Path("pyproject.toml").open("rb") as projectFile:
        projectData = loadToml( projectFile )
    
    tdSearchPaths = [ "C:\\Program Files\\Derivative" ] + environ.get("TD_INSTALLSEARCHPATH", "").split(":")
    tdVersion = Path(".touchdesigner-version").read_text()
    executeableName = f"{backend}.exe"
    projectFile = projectData.get("project", {}).get("projectfile", "Project.toe")

    load_dotenv()

    for searchPath in tdSearchPaths:
        tdExecuteable = Path(searchPath, f"TouchDesigner.{tdVersion}", "bin", executeableName)
        if tdExecuteable.is_file():
            print( tdExecuteable )
            tdProcess = subprocess.Popen([str(tdExecuteable),  projectFile])
            print( tdProcess.wait() )
            break
        raise Exception(f"TD-Installation for veruon {tdVersion} not found!")

def designer():
    launch("TouchDesigner")

def editor():
    launch("TouchDesigner")

def player():
    launch("TouchPlayer")
