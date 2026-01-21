A commandline utility that allows management of TouchDesigner from UV.

Windows Only. (PR welcome)

## Install
use ```uv add git+https://github.com/PlusPlusOneGmbH/MonkeyBrain``` or ```uv add monkeybrain``` to add to project.

https://docs.derivative.ca/Palette:tdPyEnvManager

Should use "2025.32260" or later for optimal experience!

## Commands
It searches the best installed TouchDesigner version and allows for the following commands.
To run the project use 

```uv run mb edit``` to launch TouchDesigner

```uv run mb designer``` to launch TouchDesigner and set NODE_ENV to production

```uv run mb player``` to launch TouchPlayer and set NODE_ENV to production

To set up a correct pyproject.toml use ```uv run mb init.files```. It will search for the latest installed TD version if not already specified, as for the first .TOE file it finds and add the specified values to the pyproject.toml.

If the defined version does support it, it will also add the correct settings for the EnvHelper to autoload the correct environment. So convinient!

To setup a good vscode settings, run ```uv run mb init.code``` which will create links to all important libs defined in the env-settings. and set the defaultInterpreter.

Both functions are combined in ```uv run mb init```

```toml
[tool.monkeybrain]
touchdesigner-version = "2025.32260"
projectfile = "Example.toe"
enforce-version = "strict"

[tool.touchdesigner.TDPyEnvManagerContext]
mode = "Python vEnv"
envName = ".venv"
installPath = "."
extraPaths = [ "src", "${UV_PROJECT_ENVIRONMENT}/Lib/site-packages", ".venv/Lib/site-packages"]

```
## PyProject.toml 
The touchlauncher package will use the pyproject.toml file to determin the correct TouchDesigner-Installation and path.

```toml
[tool.touchdesigner]
touchdesigner-version = "2025.32260"
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


__.env files will be mounted before TouchDesigner starts.__

You can supply additional search paths by setting ```TD_INSTALLSEARCHPATH``` as a ; delimited string. 

( i.E. TD_INSTALLSEARCHPATH = "D:/TouchDesigner; E:/TouchDsigner")









