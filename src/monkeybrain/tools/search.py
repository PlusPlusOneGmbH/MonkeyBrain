
from pathlib import Path
from os import environ, listdir

import logging
logger = logging.getLogger()
log_level = getattr(logging, environ.get("TOUCHLAUNCH_LOGLEVEL", "INFO"), None) or logging.INFO
logging.basicConfig(level=log_level)


from enum import Enum

class SearchMode(Enum):
    STRICT          = "strict"
    CLOSESTBUILD    = "closest-build"
    LATESTBUILD     = "latest-build"
    LATESTVERSION   = "latest-version"


from typing import TypedDict, List
class TouchdesignerInstall(TypedDict):
    version:int
    build:int
    numeric_value:float
    string_value:str
    folder:Path
    executeable:Path

from .file_meta import get_file_metadata

def list_touchdesigner_installs() -> List[TouchdesignerInstall]:
    td_search_paths = [ "C:\\Program Files\\Derivative" ] + [ pathstring.strip() for pathstring in environ.get("TD_INSTALLSEARCHPATH", "").split(";") ]
    td_installations:List[TouchdesignerInstall] = []
    for search_location in [Path(_search_location) for _search_location in td_search_paths]:
        if not search_location.is_dir(): continue
        for install_location in [ Path(search_location, _install_location) for _install_location in listdir( search_location )]:
            if not install_location.is_dir(): continue
            exeucteable = Path( install_location, "bin", "TouchDesigner.exe")
            version_meta_data = get_file_metadata( exeucteable, ["Product version"]).get("Product version", "0.0.0.0")
            if version_meta_data == "0.0.0.0": continue
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

from .project import get_project_touchdesigner_version

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