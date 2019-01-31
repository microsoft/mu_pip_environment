# @file CommonBuildEntry.py
# This module contains code that is shared between all the entry points for PlatformBUild
# scripts.
#
##
# Copyright (c) 2017, Microsoft Corporation
#
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##

import os
import sys
import re
import logging
import subprocess
import argparse
import pkg_resources
from datetime import datetime
from MuEnvironment import SelfDescribingEnvironment
from MuEnvironment import MuLogging
from MuEnvironment import PluginManager
from MuEnvironment import VersionAggregator
from MuPythonLibrary.UtilityFunctions import RunCmd

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

PIP_PACKAGES_LIST = ["mu_environment", "mu_python_library", "PyYaml"]

#
# Pass in a list of pip package names and they will be printed as well as
# reported to the global VersionAggregator


def display_pip_package_info(package_list):
    for package in package_list:
        version = pkg_resources.get_distribution(package).version
        logging.info("{0} version: {1}".format(package, version))
        VersionAggregator.GetVersionAggregator().ReportVersion(package, version, VersionAggregator.VersionTypes.TOOL)

# Simplified Comparison Function borrowed from StackOverflow...
# https://stackoverflow.com/questions/1714027/version-number-comparison
# With Python 3.0 help from:
# https://docs.python.org/3.0/whatsnew/3.0.html#ordering-comparisons


def version_compare(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    (a, b) = (normalize(version1), normalize(version2))
    return (a > b) - (a < b)


#
# Shell Command with Output Helper
# This helper will attempt to run a shell command and return the results.
# Will raise an error if return code is non-zero.


def cmd_with_output(cmd_string, cwd):
    c = subprocess.Popen(cmd_string, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, cwd=cwd, shell=True)
    c.wait()

    # Get the data.
    # Have to .decode because the stdout read gets bytes().
    cmd_result = c.stdout.read().decode()

    # Check for errors.
    if c.returncode != 0:
        raise RuntimeError(cmd_result)

    return cmd_result


#
# minimum_env_init() will attempt to follow all of the steps
# necessary to get this process off the ground.


def minimum_env_init(my_workspace_path, my_project_scope):
    # TODO: Check the Git version against minimums.

    # Check the Python version against minimums.
    cur_py = "%d.%d.%d" % sys.version_info[:3]
    VersionAggregator.GetVersionAggregator().ReportVersion("Python", cur_py, VersionAggregator.VersionTypes.TOOL)

    soft_min_py = "3.7"
    hard_min_py = "3.6"

    if version_compare(hard_min_py, cur_py) > 0:
        raise RuntimeError(
            "Please upgrade Python! Current version is %s. Minimum is %s." % (cur_py, hard_min_py))
    if version_compare(soft_min_py, cur_py) > 0:
        logging.error("Please upgrade Python! Current version is %s. Recommended minimum is %s." % (
            cur_py, soft_min_py))

    return_buffer = StringIO()
    RunCmd("git", "--version", outstream=return_buffer)
    git_version = return_buffer.getvalue().strip()
    return_buffer.close()
    VersionAggregator.GetVersionAggregator().ReportVersion("Git", git_version, VersionAggregator.VersionTypes.TOOL)
    min_git = "2.11.0"
    # This code is highly specific to the return value of "git version"...
    cur_git = ".".join(git_version.split(' ')[2].split(".")[:3])
    if version_compare(min_git, cur_git) > 0:
        raise RuntimeError("Please upgrade Git! Current version is %s. Minimum is %s." % (cur_git, min_git))

    # Initialized the build environment.
    return SelfDescribingEnvironment.BootstrapEnvironment(my_workspace_path, my_project_scope)


#
# configure_base_logging() sets up only the logging that will
# be used by all commands. (ie. doesn't configure any logging files)


def configure_base_logging(mode="standard", sections=[]):
    # Initialize logging.
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)

    # Adjust console mode depending on mode.
    MuLogging.setup_section_level()

    for section in sections:
        MuLogging.get_mu_filter().addSection(section)

    if mode == "vs":
        console = MuLogging.setup_console_logging(use_color=False, formatter="%(message)s", logging_level=logging.DEBUG)
    elif mode == 'verbose':
        console = MuLogging.setup_console_logging(logging_level=logging.DEBUG)
    elif mode == 'simple':
        console = MuLogging.setup_console_logging(logging_level=logging.INFO)
    else:
        console = MuLogging.setup_console_logging(logging_level=logging.WARNING)

    # Add the console as a logger, now that it's configured.
    logger.addHandler(console)

#
# setup_process() automates all of the processes that should be unique
# to each platform build. It will attempt to set up the repos and
# anything else that's important.


def setup_process(my_workspace_path, my_project_scope, my_required_repos, force_it=False, cache_path=None):
    def log_lines(level, lines):
        for line in lines.split("\n"):
            if line != "":
                logging.log(level, line)

    # Pre-setup cleaning if "--force" is specified.
    if force_it:
        try:
            # Clean and reset the main repo.
            MuLogging.log_progress("## Cleaning the root repo...")
            cmd_with_output('git reset --hard', my_workspace_path)
            log_lines(logging.INFO, cmd_with_output('git clean -xffd', my_workspace_path))
            MuLogging.log_progress("Done.\n")

            # Clean any submodule repos.
            if my_required_repos:
                for required_repo in my_required_repos:
                    MuLogging.log_progress("## Cleaning Git repository: %s..." % required_repo)
                    required_repo_path = os.path.normpath(os.path.join(my_workspace_path, required_repo))
                    cmd_with_output('git reset --hard', required_repo_path)
                    log_lines(logging.INFO, cmd_with_output('git clean -xffd', required_repo_path))
                    MuLogging.log_progress("Done.\n")

        except RuntimeError as e:
            logging.error("FAILED!\n")
            logging.error("Error while trying to clean the environment!")
            log_lines(logging.ERROR, str(e))
            return

    # Grab the remaining Git repos.
    if my_required_repos:
        # Git Repos: STEP 1 --------------------------------------
        # Make sure that the repos are all synced.
        try:
            MuLogging.log_progress("## Syncing Git repositories: %s..." % ", ".join(my_required_repos))
            cmd_with_output('git submodule sync -- ' + " ".join(my_required_repos), my_workspace_path)
            MuLogging.log_progress("Done.\n")
        except RuntimeError as e:
            logging.error("FAILED!\n")
            logging.error("Error while trying to synchronize the environment!")
            log_lines(logging.ERROR, str(e))
            return

        # Git Repos: STEP 2 --------------------------------------
        # Iterate through all repos and see whether they should be fetched.
        for required_repo in my_required_repos:
            try:
                MuLogging.log_progress("## Checking Git repository: %s..." % required_repo)

                # Git Repos: STEP 2a ---------------------------------
                # Need to determine whether to skip this repo.
                required_repo_path = os.path.normpath(os.path.join(my_workspace_path, required_repo))
                skip_repo = False
                # If the repo exists (and we're not forcing things) make
                # sure that it's not in a "dirty" state.
                if os.path.exists(required_repo_path) and not force_it:
                    git_data = cmd_with_output('git diff ' + required_repo, my_workspace_path)

                    # If anything was returned, we should skip processing the repo.
                    # It is either on a different commit or it has local changes.
                    if git_data != "":
                        logging.info("-- NOTE: Repo currently exists and appears to have local changes!")
                        logging.info("-- Skipping fetch!")
                        skip_repo = True

                # Git Repos: STEP 2b ---------------------------------
                # If we're not skipping, grab it.
                if not skip_repo or force_it:
                    logging.info("## Fetching repo.")
                    # Using RunCmd for this one because the c.wait blocks incorrectly somehow.
                    cmd_string = "submodule update --init --recursive --progress"
                    if cache_path is not None:
                        cmd_string += " --reference " + cache_path
                    cmd_string += " " + required_repo
                    RunCmd('git', cmd_string, workingdir=my_workspace_path)

                MuLogging.log_progress("Done.\n")

            except RuntimeError as e:
                logging.error("FAILED!\n")
                logging.error("Failed to fetch required repository!\n")
                log_lines(logging.ERROR, str(e))

    # Now that we should have all of the required code,
    # we're ready to build the environment and fetch the
    # dependencies for this project.
    MuLogging.log_progress("## Fetching all external dependencies...")
    (build_env, shell_env) = minimum_env_init(
        my_workspace_path, my_project_scope)
    SelfDescribingEnvironment.UpdateDependencies(
        my_workspace_path, my_project_scope)
    MuLogging.log_progress("Done.\n")

    # TODO: Install any certs any other things that might be required.


def update_process(my_workspace_path, my_project_scope):
    # Get the environment set up.
    logging.log(MuLogging.SECTION, "Bootstrapping Enviroment")
    logging.info("## Parsing environment...")
    (build_env, shell_env) = minimum_env_init(
        my_workspace_path, my_project_scope)
    logging.info("Done.\n")

    # Update the environment.
    logging.info("## Updating environment...")
    SelfDescribingEnvironment.UpdateDependencies(
        my_workspace_path, my_project_scope)
    logging.info("Done.\n")


def build_process(my_workspace_path, my_project_scope, my_module_pkg_paths, logging_mode="standard"):
    #
    # Initialize file-based logging.
    #
    log_directory = os.path.join(my_workspace_path, "Build")

    # TODO get the logging mode to determine the log level we should output at?
    logfile, filelogger = MuLogging.setup_txt_logger(log_directory, "BUILDLOG", logging.DEBUG)
    mdfile, mdlogger = MuLogging.setup_markdown_logger(log_directory, "BUILDLOG", logging.DEBUG)

    logging.info("Log Started: " + datetime.strftime(datetime.now(), "%A, %B %d, %Y %I:%M%p"))
    logging.info("Running Python version: " + str(sys.version_info))

    display_pip_package_info(PIP_PACKAGES_LIST)

    #
    # Next, get the environment set up.
    #
    try:
        (build_env, shell_env) = minimum_env_init(
            my_workspace_path, my_project_scope)
        if not SelfDescribingEnvironment.VerifyEnvironment(my_workspace_path, my_project_scope):
            raise RuntimeError("Validation failed.")
    except:
        raise RuntimeError(
            "Environment is not in a state to build! Please run '--UPDATE'.")

    # Load plugins
    logging.log(MuLogging.SECTION, "Loading Plugins")
    pluginManager = PluginManager.PluginManager()
    failedPlugins = pluginManager.SetListOfEnvironmentDescriptors(
        build_env.plugins)
    if failedPlugins:
        logging.critical("One or more plugins failed to load. Halting build.")
        for a in failedPlugins:
            logging.error("Failed Plugin: {0}".format(a["name"]))
        raise Exception("One or more plugins failed to load.")

    helper = PluginManager.HelperFunctions()
    if(helper.LoadFromPluginManager(pluginManager) > 0):
        raise Exception("One or more helper plugins failed to load.")

    # NOTE: This implicitly assumes that the PlatformBuild script path is in PYTHONPATH.
    from PlatformBuildWorker import PlatformBuilder

    #
    # Now we can actually kick off a build.
    #
    logging.log(MuLogging.SECTION, "Kicking off build")
    PB = PlatformBuilder(my_workspace_path, my_module_pkg_paths,
                         pluginManager, helper, sys.argv)
    retcode = PB.Go()

    logging.log(MuLogging.SECTION, "Summary")
    if(retcode != 0):
        MuLogging.log_progress("Error")
    else:
        MuLogging.log_progress("Success")
    # always output the location of the log file
    MuLogging.log_progress("Log file at " + logfile)

    # get all vars needed as we can't do any logging after shutdown otherwise our log is cleared.
    # Log viewer
    ep = PB.env.GetValue("LaunchBuildLogProgram")
    LogOnSuccess = PB.env.GetValue("LaunchLogOnSuccess")
    LogOnError = PB.env.GetValue("LaunchLogOnError")

    # end logging
    logging.shutdown()
    # no more logging

    if(ep is not None):
        cmd = ep + " " + logfile

    #
    # Conditionally launch the shell to show build log
    #
    #
    if(((retcode != 0) and (LogOnError.upper() == "TRUE")) or (LogOnSuccess.upper() == "TRUE")):
        subprocess.Popen(cmd, shell=True)

    sys.exit(retcode)


def build_entry(my_script_path, my_workspace_path, my_required_repos, my_project_scope,
                my_module_pkgs, my_module_pkg_paths):
    # This should live somewhere else as soon as someone else needs the logic.
    # I just don't want to introduce a version dependency at this exact moment.
    class IntermediateArgParser(argparse.ArgumentParser):
        def parse_known_args(self, args=None, namespace=None):
            # Explicitly pass sys.argv so that the script path isn't stripped off.
            return super(IntermediateArgParser, self).parse_known_args(args if args else sys.argv, namespace)

        def error(self, message):
            raise RuntimeError(message)

    # We will disable the help on this parser, because it's only for convenience.
    parser = IntermediateArgParser(add_help=False, usage=None)
    parser.add_argument('--andupdate', '--ANDUPDATE', '--AndUpdate', dest='update_first',
                        action='store_true', default=False)
    parser.add_argument('--force', '--FORCE', '--Force', action='store_true', default=False)
    parser.add_argument('--omnicache', '--OMNICACHE', '--Omnicache', dest='omnicache_path',
                        default=os.environ.get('OMNICACHE_PATH'))
    # Could do these also as a mutually exclusive thing, but why bother.
    parser.add_argument('--vsmode', '--VSMODE', '--VsMode', action='store_true', default=False)
    parser.add_argument('-v', '-V', '--verbose', '--VERBOSE', '--Verbose', dest='verbose',
                        action='store_true', default=False)
    parser.add_argument("--log", "--include-log", dest="log_sections", action='append', default=[])

    # Operational modes.
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--update', '--UPDATE', '--Update', dest='script_process',
                            action='store_const', const='update')
    mode_group.add_argument('--setup', '--SETUP', '--Setup', dest='script_process',
                            action='store_const', const='setup')

    try:
        # Skim off the args we care about and leave the rest in sys.argv
        (args, sys.argv) = parser.parse_known_args(namespace=argparse.Namespace(script_process='build'))
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    logging_mode = "standard"
    # Change logging modes, if necessary.
    if args.verbose:
        logging_mode = 'verbose'
    elif args.vsmode:
        logging_mode = 'vs'
    elif args.script_process in ('setup', 'update'):
        logging_mode = 'simple'

    # Turn on logging for the remainder of the process.
    configure_base_logging(logging_mode, args.log_sections)

    # Execute the requested process.
    if args.script_process == "setup":
        setup_process(my_workspace_path, my_project_scope,
                      my_required_repos, force_it=args.force, cache_path=args.omnicache_path)
    elif args.script_process == "update":
        update_process(my_workspace_path, my_project_scope)
    else:
        if args.update_first:
            update_process(my_workspace_path, my_project_scope)
        build_process(my_workspace_path, my_project_scope, my_module_pkg_paths, logging_mode)
