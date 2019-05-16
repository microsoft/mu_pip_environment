## @file test_ShellEnvironment.py
# Unit test suite for the ShellEnvironment class.
#
##
# Copyright (c) 2019, Microsoft Corporation
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
import unittest
import logging
import shutil
import tarfile
import zipfile
import tempfile
from MuEnvironment import EnvironmentDescriptorFiles as EDF
from MuEnvironment.WebDependency import WebDependency

test_dir = None
bad_json_file = '''
{
  "scope": "global",
  "type": "web",
  "name": "mu-pip",
  "source": "https://github.com/microsoft/mu_pip_environment/archive/0.tar.gz",
  "version": "7.2.1",
  "flags": ["set_path"],
  "internal_path": "/mu_pip_environment-0.3.7",
  "compression_type":"tar",
  "sha256":"68f2335344c3f7689f8d69125d182404a3515b8daa53a9c330f115739889f998"
}
'''


def prep_workspace():
    global test_dir
    # if test temp dir doesn't exist
    if test_dir is None or not os.path.isdir(test_dir):
        test_dir = tempfile.mkdtemp()
        logging.debug("temp dir is: %s" % test_dir)
    else:
        shutil.rmtree(test_dir)
        test_dir = tempfile.mkdtemp()


def clean_workspace():
    global test_dir
    if test_dir is None:
        return

    if os.path.isdir(test_dir):
        shutil.rmtree(test_dir)
        test_dir = None


class TestWebDependency(unittest.TestCase):
    def setUp(self):
        prep_workspace()

    @classmethod
    def setUpClass(cls):
        logger = logging.getLogger('')
        logger.addHandler(logging.NullHandler())
        unittest.installHandler()

    @classmethod
    def tearDownClass(cls):
        clean_workspace()

    # throw in a bad url and test that it throws an exception.
    def test_fail_with_bad_url(self):
        ext_dep_file_path = os.path.join(test_dir, "bad_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(bad_json_file)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = WebDependency(ext_dep_descriptor)
        with self.assertRaises(Exception):
            ext_dep.fetch()
            self.fail("should have thrown an Exception")

    # Test that get_internal_path_root works the way we expect with a flat directory structure.
    # test_dir\inner_dir - test_dir\inner_dir should be the root.
    def test_get_internal_path_root_flat(self):
        outer_dir = test_dir
        inner_dir_name = "inner_dir"
        inner_dir_path = os.path.join(outer_dir, inner_dir_name)
        self.assertEqual(WebDependency.get_internal_path_root(outer_dir, inner_dir_name), inner_dir_path)

    # Test that get_internal_path_root works the way we expect with a flat directory structure
    # test_dir\first_dir\second_dir - test_dir\first_dir should be the root
    def test_get_internal_path_root_with_subfolders(self):
        outer_dir = test_dir
        first_level_dir_name = "first_dir"
        second_level_dir_name = "second_dir"
        inner_dir_path = os.path.join(outer_dir, first_level_dir_name)
        self.assertEqual(WebDependency.get_internal_path_root(outer_dir,
                         os.path.join(first_level_dir_name, second_level_dir_name)), inner_dir_path)

    # Test that a single file zipped is able to be processed by unpack.
    def test_unpack_zip_file(self):
        compressed_file_path = os.path.join(test_dir, "bad_ext_dep_zip.zip")
        destination = test_dir
        internal_path = "bad_ext_dep.json"
        compression_type = "zip"

        file_path = os.path.join(test_dir, internal_path)

        with open(file_path, "w+") as ext_dep_file:
            ext_dep_file.write(bad_json_file)

        with zipfile.ZipFile(compressed_file_path, 'w') as _zip:
            _zip.write(file_path, arcname=os.path.basename(file_path))

        os.remove(file_path)
        self.assertFalse(os.path.isfile(file_path))

        WebDependency.unpack(compressed_file_path, destination, internal_path, compression_type)
        self.assertTrue(os.path.isfile(file_path))

    # Test that a single file tar volume is able to be processed by unpack.
    def test_unpack_tar_file(self):
        compressed_file_path = os.path.join(test_dir, "bad_ext_dep_zip.tar.gz")
        destination = test_dir
        internal_path = "bad_ext_dep.json"
        compression_type = "tar"

        file_path = os.path.join(test_dir, internal_path)

        with open(file_path, "w+") as ext_dep_file:
            ext_dep_file.write(bad_json_file)

        with tarfile.open(compressed_file_path, "w:gz") as _tar:
            _tar.add(file_path, arcname=os.path.basename(file_path))

        os.remove(file_path)
        self.assertFalse(os.path.isfile(file_path))

        WebDependency.unpack(compressed_file_path, destination, internal_path, compression_type)
        self.assertTrue(os.path.isfile(file_path))

    # Test that a zipped directory is processed correctly by unpack.
    # If internal_path is first_dir\second_dir...
    # Files in test_dir\first_dir\second_dir should be located.
    # Files in test_dir\first_dir should not be unpacked.
    def test_unpack_zip_directory(self):

        first_level_dir_name = "first_dir"
        second_level_dir_name = "second_dir"
        first_level_path = os.path.join(test_dir, first_level_dir_name)
        second_level_path = os.path.join(first_level_path, second_level_dir_name)
        os.makedirs(second_level_path)

        compressed_file_path = os.path.join(test_dir, "bad_ext_dep_zip.zip")
        destination = test_dir
        internal_path = os.path.join(first_level_dir_name, second_level_dir_name)
        compression_type = "zip"

        # only files inside internal_path should be there after unpack
        # (file path, is this file expected to be unpacked?)
        test_files = [(os.path.join(test_dir, internal_path, "bad_json_file.json"), True),
                      (os.path.join(test_dir, first_level_dir_name, "json_file.json"), False)]

        for test_file in test_files:
            with open(test_file[0], "w+") as ext_dep_file:
                ext_dep_file.write(bad_json_file)

        with zipfile.ZipFile(compressed_file_path, 'w') as _zip:
            for test_file in test_files:
                _zip.write(test_file[0], arcname=test_file[0].split(test_dir)[1])

        shutil.rmtree(first_level_path)
        self.assertFalse(os.path.isdir(first_level_path))

        WebDependency.unpack(compressed_file_path, destination, internal_path, compression_type)

        for test_file in test_files:
            if test_file[1]:
                self.assertTrue(os.path.isfile(test_file[0]))
            else:
                self.assertFalse(os.path.isfile(test_file[0]))

    # Test that a tar directory is processed correctly by unpack.
    # If internal_path is first_dir\second_dir...
    # Files in test_dir\first_dir\second_dir should be located.
    # Files in test_dir\first_dir should not be unpacked.
    def test_unpack_tar_directory(self):
        first_level_dir_name = "first_dir"
        second_level_dir_name = "second_dir"
        first_level_path = os.path.join(test_dir, first_level_dir_name)
        second_level_path = os.path.join(first_level_path, second_level_dir_name)
        os.makedirs(second_level_path)

        compressed_file_path = os.path.join(test_dir, "bad_ext_dep_zip.zip")
        destination = test_dir
        internal_path = os.path.join(first_level_dir_name, second_level_dir_name)
        compression_type = "tar"

        # only files inside internal_path should be there after unpack
        # (file path, is this file expected to be unpacked?)
        test_files = [(os.path.join(test_dir, internal_path, "bad_json_file.json"), True),
                      (os.path.join(test_dir, first_level_dir_name, "json_file.json"), False)]

        for test_file in test_files:
            with open(test_file[0], "w+") as ext_dep_file:
                ext_dep_file.write(bad_json_file)

        with tarfile.open(compressed_file_path, "w:gz") as _tar:
            for test_file in test_files:
                _tar.add(test_file[0], arcname=test_file[0].split(test_dir)[1])

        shutil.rmtree(first_level_path)
        self.assertFalse(os.path.isdir(first_level_path))

        WebDependency.unpack(compressed_file_path, destination, internal_path, compression_type)

        for test_file in test_files:
            if test_file[1]:
                self.assertTrue(os.path.isfile(test_file[0]))
            else:
                self.assertFalse(os.path.isfile(test_file[0]))

    # Test that zipfile uses / internally and not os.sep.
    # This is not exactly a test of WebDependency, more an assertion of an assumption
    # the code is making concerning the functionality of zipfile.
    def test_zip_uses_linux_path_sep(self):
        first_level_dir_name = "first_dir"
        second_level_dir_name = "second_dir"
        first_level_path = os.path.join(test_dir, first_level_dir_name)
        second_level_path = os.path.join(first_level_path, second_level_dir_name)
        os.makedirs(second_level_path)

        compressed_file_path = os.path.join(test_dir, "bad_ext_dep_zip.zip")
        internal_path = os.path.join(first_level_dir_name, second_level_dir_name)
        internal_path_win = "\\".join((first_level_dir_name, second_level_dir_name))

        test_file = os.path.join(test_dir, internal_path, "bad_json_file.json")

        with open(test_file, "w+") as ext_dep_file:
            ext_dep_file.write(bad_json_file)

        with zipfile.ZipFile(compressed_file_path, 'w') as _zip:
            _zip.write(test_file, arcname=test_file.split(test_dir)[1])

        with zipfile.ZipFile(compressed_file_path, 'r') as _zip:
            namelist = _zip.namelist()

        self.assertTrue(len(namelist) == 1)
        self.assertFalse(internal_path_win in namelist[0])
        self.assertTrue(WebDependency.linuxize_path(internal_path_win) in namelist[0])

    # Test that tarfile uses / internally and not os.sep.
    # This is not exactly a test of WebDependency, more an assertion of an assumption
    # the code is making concerning the functionality of tarfile.
    def test_tar_uses_linux_path_sep(self):
        first_level_dir_name = "first_dir"
        second_level_dir_name = "second_dir"
        first_level_path = os.path.join(test_dir, first_level_dir_name)
        second_level_path = os.path.join(first_level_path, second_level_dir_name)
        os.makedirs(second_level_path)

        compressed_file_path = os.path.join(test_dir, "bad_ext_dep_zip.zip")
        internal_path = os.path.join(first_level_dir_name, second_level_dir_name)
        internal_path_win = "\\".join((first_level_dir_name, second_level_dir_name))

        test_file = os.path.join(test_dir, internal_path, "bad_json_file.json")

        with open(test_file, "w+") as ext_dep_file:
            ext_dep_file.write(bad_json_file)

        with tarfile.open(compressed_file_path, "w:gz") as _tar:
            _tar.add(test_file, arcname=test_file.split(test_dir)[1])

        with tarfile.open(compressed_file_path, "r:*") as _tar:
            namelist = _tar.getnames()

        self.assertTrue(len(namelist) == 1)
        self.assertFalse(internal_path_win in namelist[0])
        self.assertTrue(WebDependency.linuxize_path(internal_path_win) in namelist[0])


if __name__ == '__main__':
    unittest.main()
