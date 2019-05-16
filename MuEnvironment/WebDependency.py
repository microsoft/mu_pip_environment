# @file WebDependency.py
# This module implements ExternalDependency for files that are available for download online.
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
import tarfile
import zipfile
import urllib
from MuEnvironment.ExternalDependency import ExternalDependency


class WebDependency(ExternalDependency):
    '''
    ext_dep fields:
    - internal_path: Describes layout of what we're downloading. Include / at the beginning
                     if the ext_dep is a directory. Item located at internal_path will
                     unpacked into the ext_dep folder and this is what the path/shell vars
                     will point to when compute_published_path is run.
    - compression_type: optional. supports zip and tar. If the file isn't compressed, do not include this field.
    - sha256: optional. hash of downloaded file to be checked against.
    '''

    TypeString = "web"

    def __init__(self, descriptor):
        super().__init__(descriptor)
        self.internal_path = descriptor['internal_path']
        self.compression_type = descriptor.get('compression_type', None)
        self.sha256 = descriptor.get('sha256', None)

        # If the internal path starts with a / that means we are downloading a directory
        self.download_is_directory = self.internal_path.startswith("/")

        # Now we can get rid of the leading /
        self.internal_path = self.internal_path.strip("/")

    def linuxize_path(path):
        '''
        path: path that uses os.sep, to be replaced with / for compatibility with zipfile
        '''
        return "/".join(path.split("\\"))

    def unpack(compressed_file_path, destination, internal_path, compression_type):
        '''
        compressed_file_path: name of compressed file to unpack.
        destination: directory you would like it unpacked into.
        internal_path: internal structure of the compressed volume that you would like extracted.
        compression_type: type of compression. tar and zip supported.
        '''

        # First, we will open the file depending on the type of compression we're dealing with.

        # tarfile and zipfile both use the Linux path seperator / instead of using os.sep
        linux_internal_path = WebDependency.linuxize_path(internal_path)

        if compression_type == "zip":
            logging.info(f"{compressed_file_path} is a zip file, trying to unpack it.")
            _ref = zipfile.ZipFile(compressed_file_path, 'r')
            files_in_volume = _ref.namelist()

        elif compression_type and "tar" in compression_type:
            logging.info(f"{compressed_file_path} is a tar file, trying to unpack it.")
            # r:* tells tarfile to look at the header and figure out how to extract it
            _ref = tarfile.open(compressed_file_path, "r:*")
            files_in_volume = _ref.getnames()

        else:
            raise RuntimeError(f"{compressed_file_path} was labeled as {compression_type}, which is not supported.")

        # Filter the files inside to only the ones that are inside the important folder
        files_to_extract = [name for name in files_in_volume if linux_internal_path in name]

        for file in files_to_extract:
            _ref.extract(member=file, path=destination)
        _ref.close()

    def get_internal_path_root(outer_dir, internal_path):
        temp_path_root = os.path.split(internal_path)[0] if os.sep in internal_path else internal_path
        unzip_root = os.path.join(outer_dir, temp_path_root)
        return unzip_root

    def fetch(self):
        url = self.source
        temp_file_name = os.path.join(self.descriptor_location, f"{self.name}_{self.version}")

        try:
            # Download the file and save it locally under `temp_file_name`
            with urllib.request.urlopen(url) as response, open(temp_file_name, 'wb') as out_file:
                out_file.write(response.read())
        except urllib.error.HTTPError as e:
            logging.error(f"ran into an issue when resolving ext_dep {self.name} at {self.source}")
            raise e

        # check if file hash is as expected, if it was provided in the ext_dep.json
        if self.sha256:
            with open(temp_file_name, "rb") as file:
                import hashlib
                temp_file_sha256 = hashlib.sha256(file.read()).hexdigest()
            if temp_file_sha256 != self.sha256:
                raise RuntimeError(f"{self.name} - sha256 does not match\n\tdownloaded:"
                                   f"\t{temp_file_sha256}\n\tin json:\t{self.sha256}")

        if os.path.isfile(temp_file_name) is False:
            raise RuntimeError(f"{self.name} did not download")

        # Next, we will look at what's inside it and pull out the parts we need.
        if self.compression_type:
            WebDependency.unpack(temp_file_name, self.descriptor_location, self.internal_path, self.compression_type)

        # internal_path points to the "important" part of the ext_dep we're unpacking
        complete_internal_path = os.path.join(self.descriptor_location, self.internal_path)

        # # If we're unpacking a directory, we can copy the important parts into
        # # a directory named self.contents_dir
        if self.download_is_directory:
            # The root of the internal path is the folder we will see populated in descriptor_location
            unzip_root = WebDependency.get_internal_path_root(self.descriptor_location, self.internal_path)

            logging.info(f"Copying directory from {complete_internal_path} to {self.contents_dir}")
            if os.path.isdir(complete_internal_path) is False:
                # internal_path was not accurate, delete temp_file and exit
                os.remove(temp_file_name)
                raise RuntimeError(f"{self.name} was expecting {complete_internal_path} to exist after unpacking")

            # Move the important folder out and rename it to contents_dir
            shutil.move(complete_internal_path, self.contents_dir)

            # If the unzipped directory still exists, delete it.
            if os.path.isdir(unzip_root):
                shutil.rmtree(unzip_root)

        # If we just downloaded a file, we need to create a directory named self.contents_dir,
        # copy the file inside, and name it self.internal_path
        else:
            logging.info(f"Copying file to {complete_internal_path}")
            shutil.move(temp_file_name, complete_internal_path)

        # delete temp download file
        if os.path.isfile(temp_file_name):
            os.remove(temp_file_name)

        # Add a file to track the state of the dependency.
        self.update_state_file()

        # The published path may change now that the package has been unpacked.
        self.published_path = self.compute_published_path()
