# @file NuGet.py
# This module contains code that knows how to download nuget
#
# Copyright (c), Microsoft Corporation
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
import urllib.error
import urllib.request
import logging

# Update this when you want a new version of NuGet
VERSION = "5.1.0"
URL = "https://dist.nuget.org/win-x86-commandline/v{}/nuget.exe".format(VERSION)
SHA256 = "0ace4f53493332c9a75291ee96acd76b371b4e687175e4852bf85948176d7152"


def DownloadNuget(unpack_folder=None):
    if unpack_folder is None:
        unpack_folder = os.path.dirname(__file__)

    out_file_name = os.path.join(unpack_folder, "NuGet.exe")
    # check if we have the nuget file already downloaded
    if not os.path.isfile(out_file_name):
        try:
            # Download the file and save it locally under `temp_file_name`
            with urllib.request.urlopen(URL) as response, open(out_file_name, 'wb') as out_file:
                out_file.write(response.read())
        except urllib.error.HTTPError as e:
            logging.error(f"We ran into an issue when getting NuGet")
            raise e

    # do the hash to make sure the file is good
    with open(out_file_name, "rb") as file:
        import hashlib
        temp_file_sha256 = hashlib.sha256(file.read()).hexdigest()
    if temp_file_sha256 != SHA256:
        os.remove(out_file_name)
        raise RuntimeError(f"Nuget - sha256 does not match\n\tdownloaded:\t{temp_file_sha256}\n\t")
