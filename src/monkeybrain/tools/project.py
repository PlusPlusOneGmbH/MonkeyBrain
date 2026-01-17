
from functools import cache
from pathlib import Path
from tomllib import load as loadToml
from typing import Union


@cache
def load_project_config():
    with Path("pyproject.toml").open("rb") as project_file:
        return loadToml( project_file )

def get_tool_config( project_data:Union[dict, None] = None ):
    _project_data = project_data or load_project_config()
    return {
        **_project_data.get("tool", {}).get("touchdesigner", {}),
        **_project_data.get("tool", {}).get("monkeybrain", {})
    }

def get_project_touchdesigner_version():
    project_settings = get_tool_config()
    td_version = project_settings.get("touchdesigner-version", Path(".touchdesigner-version").read_text() )
    return td_version 
