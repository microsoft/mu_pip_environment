
==============
MU Environment
==============

.. |build_status_windows| image:: https://dev.azure.com/projectmu/mu%20pip/_apis/build/status/Environment/Mu%20Pip%20Environment%20-%20PR%20Gate%20(Windows)?branchName=master
.. |build_status_linux| image:: https://dev.azure.com/projectmu/mu%20pip/_apis/build/status/Environment/Mu%20Pip%20Environment%20-%20PR%20Gate%20(Linux%20-%20Ubuntu%201604)?branchName=master

|build_status_windows| Current build status for master on Windows

|build_status_linux| Current build status for master on Linux

About
=====

Entry point into Self Describing Environment (SDE). Sets up and parses state of workspace before calling into build.
Please see Project Mu for details https://microsoft.github.io/mu

Version History
===============

0.3.6
-----

Main Changes:

- Documentation added for Omnicache tool
- Completed isolation of ShellEnviornment as a functional singleton. This allows for behaviors like updating PATHs programatically during setup while maintaining APIs like GetBuildVars().
    - Add replace_path_element and replace_pypath_element, which will find an element on the PATH/PYPATH, replace it with a different element, and publish the newly modified path
    - Add remove_pypath_element and remove_path_element, which will find an element on the PATH/PYPATH, remove it, and publish the newly modified path
- Added "host_specific" flag to allow ext_deps to have different tool versions for different OS's, architectures, and bit sizes. For more information about how the selection process is made, refer [here](https://microsoft.github.io/mu/dyn/mu_basecore/BaseTools/NugetPublishing/ReadMe).

Bug Fixes:

- Git submodules are now initialized correctly when using a reference. It was failing silently previously.
- Logging output is now handled correct (handlers were being created incorrectly and extra output was going to the console)

0.3.5
-----

Main changes:

- In ConfMgmt, change FindWithVsWhere() to a static method.
- PYTHON_HOME environment variable will automatically be set to the dir path of the Python (sys.executable).

Bug fixes:

- Removing Git submodule VersionAggregation, as this information is contained in the Git commit history. Removing this step cuts several seconds from the beginning of the build.
- You can't have a reference path when doing a clone and saying --recurse-submodules. While it makes zero sense, git throws an error. The retry should be catching this once it goes through as it will try to reclone without the reference path. This does it correctly the first time.

0.3.4
-----

Main changes:

- N/A

Bug fixes:

- Fix for incorrectly using the omnicache even when it wasn't specified. This would cause problems in a server or shallow cloned environment

0.3.3
-----

Main changes:

- Omnicache is a single cache database as a --reference for git repo initialization. See feature_omnicache.md for more information.
- Based on TOOL_CHAIN_TAG, ConfMgmt will attempt to locate a .vs or .gcc conf file before loading the .ms conf file.
- In ConfMgmt __init__, we will now throw an error if WORKSPACE or EDK2_BASE_TOOLS_DIR is not populated yet.
- Significant restructure of MuLogging API surface. Now using named loggers rather than root logger so pieces can be filtered using MuFilter. More info in feature_MuLogging.md.

Bug fixes:

- Linted code base, enforcing a 120 character per line limit.
- Added /.eggs to .gitignore. This directory is only generated when using a local installation of a pip module.

0.3.2
-----

Enabled IntermediateArgParser in CommonBuildEntry, which only scrapes the expected arguments from argparser and stores the rest back in sys.argv to be used later.

0.3.1
-----

- Check submodule.head for type None before reporting it.
- Removing `--name-only` from the `_get_submodule_list` function and retrieving the path instead.

0.3.0
-----

Updated documentation and release process.  Transition to Beta.

< 0.3.0
-------

Alpha development