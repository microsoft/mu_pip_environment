# @file NugetDependency.py
# This module implements ExternalDependency for NuGet packages.
#
##
# Copyright (c) 2017-2018, Microsoft Corporation
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
import logging
import shutil
from io import StringIO
from MuEnvironment.ExternalDependency import ExternalDependency
from MuPythonLibrary.UtilityFunctions import RunCmd
from MuPythonLibrary.UtilityFunctions import GetHostInfo
import pkg_resources


class NugetDependency(ExternalDependency):
    TypeString = "nuget"
    global_cache_path = None

    ####
    # Add mono to front of command and resolve full path of exe for mono,
    # Used to add nuget support on posix platforms.
    # https://docs.microsoft.com/en-us/nuget/install-nuget-client-tools
    #
    # @return list containing either ["nuget.exe"] or ["mono", "/PATH/TO/nuget.exe"]
    ####
    @staticmethod
    def GetNugetCmd():
        file = "NuGet.exe"
        cmd = []
        if GetHostInfo().os == "Linux":
            cmd += ["mono"]
        # TODO Find the Nuget rom our bin file
        requirement = pkg_resources.Requirement.parse("mu-environment")
        nuget_file_path = os.path.join("MuEnvironment", "bin", file)
        nuget_path = pkg_resources.resource_filename(requirement, nuget_file_path)

        # check if we don't have it, look for nuget in the path
        if not os.path.isfile(nuget_path):
            for env_var in os.getenv("PATH").split(os.pathsep):
                env_var = os.path.join(os.path.normpath(env_var), file)
                if os.path.isfile(env_var):
                    nuget_path = '"' + env_var + '"'
                    break
        # we've probably found something by now?
        cmd += [nuget_path]
        # if we're still hosed
        if not os.path.isfile(nuget_path):
            logging.error("We weren't able to find Nuget! Please reinstall your pip environment")
            return None
        return cmd

    @staticmethod
    def normalize_version(version):
        version_parts = tuple(int(num) for num in version.split('.'))
        if len(version_parts) > 4:
            raise RuntimeError("Unparsable version '%s'!")

        # Remove extra trailing zeros (beyond 3 elements).
        if len(version_parts) == 4 and version_parts[3] == 0:
            version_parts = version_parts[0:2]

        # Add missing trailing zeros (below 3 elements).
        if len(version_parts) < 3:
            version_parts = version_parts + (0,) * (3 - len(version_parts))

        # Return reformed version.
        return ".".join((str(num) for num in version_parts))

    def _fetch_from_cache(self, package_name):
        result = False

        #
        # We still need to use Nuget to figure out where the
        # "global-packages" cache is on this machine.
        #
        if NugetDependency.global_cache_path is None:
            cmd = NugetDependency.GetNugetCmd()
            cmd += ["locals", "global-packages", "-list"]
            return_buffer = StringIO()
            if (RunCmd(cmd[0], " ".join(cmd[1:]), outstream=return_buffer) == 0):
                # Seek to the beginning of the output buffer and capture the output.
                return_buffer.seek(0)
                return_string = return_buffer.read()
                NugetDependency.global_cache_path = return_string.strip().strip("global-packages: ")

        #
        # If the path couldn't be found, we can't do anything else.
        #
        if not os.path.isdir(NugetDependency.global_cache_path):
            logging.info(
                "Could not determine Nuget global packages cache location.")
            return False

        #
        # Now, try to locate our actual cache path
        nuget_version = NugetDependency.normalize_version(self.version)
        cache_search_path = os.path.join(
            NugetDependency.global_cache_path, package_name.lower(), nuget_version, package_name)
        if os.path.isdir(cache_search_path):
            logging.info(
                "Local Cache found for Nuget package '%s'. Skipping fetch.", package_name)
            shutil.copytree(cache_search_path, self.contents_dir)
            self.update_state_file()
            result = True

        return result

    def fetch(self):
        package_name = self.name
        #
        # Before trying anything with Nuget feeds,
        # check to see whether the package is already in
        # our local cache. If it is, we avoid a lot of
        # time and network cost by copying it directly.
        #
        if self._fetch_from_cache(package_name):
            # We successfully found the package in the cache.
            # The published path may change now that the package has been unpacked.
            # Bail.
            self.published_path = self.compute_published_path()
            return

        #
        # If we are still here, the package wasn't in the cache.
        # We need to ask Nuget to find it.
        #

        #
        # First, fetch the contents of the package.
        #
        temp_directory = self.get_temp_dir()
        cmd = NugetDependency.GetNugetCmd()
        cmd += ["install", package_name]
        cmd += ["-Source", self.source]
        cmd += ["-ExcludeVersion"]
        cmd += ["-Version", self.version]
        cmd += ["-Verbosity", "detailed"]
        cmd += ["-OutputDirectory", '"' + temp_directory + '"']
        RunCmd(cmd[0], " ".join(cmd[1:]))

        #
        # Next, copy the contents of the package to the
        # final resting place.
        #
        # Depending on packaging, the package content will be in one of two
        # possible locations:
        # 1. temp_directory\package_name\package_name\
        # 2. temp_directory\package_name\
        #
        source_dir = os.path.join(temp_directory, package_name, package_name)
        if not os.path.isdir(source_dir):
            source_dir = os.path.join(temp_directory, package_name)
        shutil.move(source_dir, self.contents_dir)

        #
        # Add a file to track the state of the dependency.
        #
        self.update_state_file()

        #
        # Finally, delete the temp directory.
        #
        self._clean_directory(temp_directory)

        # The published path may change now that the package has been unpacked.
        self.published_path = self.compute_published_path()

    def get_temp_dir(self):
        return self.contents_dir + "_temp"

    def clean(self):
        super(NugetDependency, self).clean()
        if os.path.isdir(self.get_temp_dir()):
            self._clean_directory(self.get_temp_dir())
