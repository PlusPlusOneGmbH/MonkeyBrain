A commandline utility that allows management of TouchDesigner from UV.

Windows Only. (PR welcome)

## Install
use ```uv add git+https://github.com/PlusPlusOneGmbH/MonkeyBrain``` to add to project.

## Commands
It searches the best installed TouchDesigner version and allows for the following commands.
To run the project use 

```uv run mb edit``` to launch TouchDesigner

```uv run mb designer``` to launch TouchDesigner and set NODE_ENV to production

```uv run mb player``` to launch TouchPlayer and set NODE_ENV to production

To create the base of required files (.packagefolder and .touchdesigner-version) run ```uv run mb init.files```.

To setup a good vscode settings, run ```uv run mb init.code``` which will create links to all important libs defined in the .packagefolder and set the defaultInterpreter.

Both functions are combined in ```uv run mb init```

Default .packagefolder file looks like this.
```
# Lines starting with # will be ignored as comments.

# ${ gets converted in to ENV-Variable. }
${UV_PROJECT_ENVIRONMENT}/Lib/site-packages

project_packages
.venv/Lib/site-packages
```

## PyProject.toml 
The touchlauncher package will use the .touchdesigner-version file to determin the correct TouchDesigner-Installation and path.
The behavior can be defined via the pyproject.toml
```toml
[tool.touchdesigner]
# Define the projectfile. Should sit in the root-dir of the project.
projectfile = "Project.toe"

# Defines the behaviour how the TD-Install should be searched for 
enforce-version="closest-build"
# Options: ( for example we use the following: Set Version: 2300.12000. Available Version [2025.1000, 2023.2000, 2023.4000]
# strict : looks for the exact version set in the .touchdesigner-version file. 
# closest-build : looks for the closes build to the set version while ignoring other versions. - Example: Will pick 2023.2000
# latest-build : looks for the latest build in the same version. - Example: Will pick 2023.4000
# latest-version : simply takes the latest available installed version. Def not suggestes! - Example: Will pick 2025.1000

```

## ENV-Variables
You can supply additional search paths by setting ```TD_INSTALLSEARCHPATH``` as a : delimited string. 
.env files will be mounted before TouchDesigner starts.







