## @file test_GitDependency.py
# Unit test suite for the GitDependency class.
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
import stat
import tempfile
from MuEnvironment import EnvironmentDescriptorFiles as EDF
from MuEnvironment.GitDependency import GitDependency

test_dir = None
uptodate_version = "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"
behind_one_version = "762941318ee16e59dabbacb1b4049eec22f0d303"
invalid_version = "762941318ee16e59d123456789049eec22f0d303"

hw_json_template = '''
{
  "scope": "global",
  "type": "git",
  "name": "HelloWorld",
  "source": "https://github.com/octocat/Hello-World.git",
  "version": "%s",
  "flags": []
}
'''


def prep_workspace():
    global test_dir
    # if test temp dir doesn't exist
    if test_dir is None or not os.path.isdir(test_dir):
        test_dir = tempfile.mkdtemp()
        logging.debug("temp dir is: %s" % test_dir)
    else:
        clean_workspace()
        test_dir = tempfile.mkdtemp()


def clean_workspace():
    global test_dir
    if test_dir is None:
        return

    if os.path.isdir(test_dir):

        def dorw(action, name, exc):
            os.chmod(name, stat.S_IWRITE)
            if(os.path.isdir(name)):
                os.rmdir(name)
            else:
                os.remove(name)

        shutil.rmtree(test_dir, onerror=dorw)
        test_dir = None


class TestGitDependency(unittest.TestCase):
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

    # good case
    def test_fetch_verify_good_repo_at_top_of_tree(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % uptodate_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        self.assertTrue(ext_dep.verify(logversion=False))
        self.assertEqual(ext_dep.version, uptodate_version)

    def test_fetch_verify_good_repo_at_not_top_of_tree(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % behind_one_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        self.assertTrue(ext_dep.verify(logversion=False))
        self.assertEqual(ext_dep.version, behind_one_version)

    def test_fetch_verify_non_existant_repo_commit_hash(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % invalid_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        self.assertEqual(ext_dep.version, invalid_version)
        self.assertFalse(ext_dep.verify(logversion=False), "Should not verify")

    def test_verify_no_directory(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % invalid_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        self.assertFalse(ext_dep.verify(logversion=False))

    def test_verify_empty_repo_dir(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % invalid_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        os.makedirs(ext_dep._local_repo_root_path, exist_ok=True)
        self.assertFalse(ext_dep.verify(logversion=False))

    def test_verify_invalid_git_repo(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % invalid_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        os.makedirs(ext_dep._local_repo_root_path, exist_ok=True)
        with open(os.path.join(ext_dep._local_repo_root_path, "testfile.txt"), 'a') as myfile:
            myfile.write("Test code\n")
        self.assertFalse(ext_dep.verify(logversion=False))

    def test_verify_dirty_git_repo(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % uptodate_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        # now write a new file
        with open(os.path.join(ext_dep._local_repo_root_path, "testfile.txt"), 'a') as myfile:
            myfile.write("Test code to make repo dirty\n")
        self.assertFalse(ext_dep.verify(logversion=False))

    def test_verify_up_to_date(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % uptodate_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        self.assertTrue(ext_dep.verify(logversion=False))

    def test_verify_down_level_repo(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % behind_one_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        self.assertTrue(ext_dep.verify(logversion=False), "Confirm valid ext_dep at one commit behind")

        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % uptodate_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        self.assertFalse(ext_dep.verify(logversion=False), "Confirm downlevel repo fails to verify")
        ext_dep.fetch()
        self.assertTrue(ext_dep.verify(logversion=False), "Confirm repo can be updated")

    # CLEAN TESTS

    def test_clean_no_directory(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % uptodate_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        self.assertFalse(os.path.isdir(ext_dep.contents_dir), "Confirm not ext dep directory before cleaning")
        ext_dep.clean()
        self.assertFalse(os.path.isdir(ext_dep.contents_dir))

    def test_clean_dir_but_not_git_repo(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % invalid_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        os.makedirs(ext_dep._local_repo_root_path, exist_ok=True)
        with open(os.path.join(ext_dep._local_repo_root_path, "testfile.txt"), 'a') as myfile:
            myfile.write("Test code\n")
        ext_dep.clean()
        self.assertFalse(os.path.isdir(ext_dep.contents_dir))

    def test_clean_dirty_git_repo(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % uptodate_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        self.assertTrue(ext_dep.verify(), "Confirm repo is valid")
        # now write a new file
        with open(os.path.join(ext_dep._local_repo_root_path, "testfile.txt"), 'a') as myfile:
            myfile.write("Test code to make repo dirty\n")
        self.assertFalse(ext_dep.verify(), "Confirm repo is dirty")
        ext_dep.clean()
        self.assertFalse(os.path.isdir(ext_dep.contents_dir))

    def test_clean_clean_repo(self):
        ext_dep_file_path = os.path.join(test_dir, "hw_ext_dep.json")
        with open(ext_dep_file_path, "w+") as ext_dep_file:
            ext_dep_file.write(hw_json_template % uptodate_version)

        ext_dep_descriptor = EDF.ExternDepDescriptor(ext_dep_file_path).descriptor_contents
        ext_dep = GitDependency(ext_dep_descriptor)
        ext_dep.fetch()
        self.assertTrue(ext_dep.verify(), "Confirm repo is valid and clean")
        ext_dep.clean()
        self.assertFalse(os.path.isdir(ext_dep.contents_dir))


if __name__ == '__main__':
    unittest.main()
