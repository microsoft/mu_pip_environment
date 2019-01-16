
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