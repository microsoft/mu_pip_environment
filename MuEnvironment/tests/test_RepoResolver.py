
import logging
import os
import unittest
from MuEnvironment import RepoResolver
import tempfile


branch_dependency = {
    "Url": "https://github.com/microsoft/mu",
    "Path": "test_repo",
    "Branch": "master"
}

sub_branch_dependency = {
    "Url": "https://github.com/microsoft/mu",
    "Path": "test_repo",
    "Branch": "gh-pages"
}

commit_dependency = {
    "Url": "https://github.com/microsoft/mu",
    "Path": "test_repo",
    "Commit": "b1e35a5d2bf05fb7f58f5b641a702c70d6b32a98"
}
commit_later_dependency = {
    "Url": "https://github.com/microsoft/mu",
    "Path": "test_repo",
    "Commit": "e28910950c52256eb620e35d111945cdf5d002d1"
}

microsoft_commit_dependency = {
    "Url": "https://github.com/Microsoft/microsoft.github.io",
    "Path": "test_repo",
    "Commit": "e9153e69c82068b45609359f86554a93569d76f1"
}
microsoft_branch_dependency = {
    "Url": "https://github.com/Microsoft/microsoft.github.io",
    "Path": "test_repo",
    "Commit": "e9153e69c82068b45609359f86554a93569d76f1"
}

test_dir = None


def prep_workspace():
    global test_dir
    # if test temp dir doesn't exist
    if test_dir is None or not os.path.isdir(test_dir):
        test_dir = tempfile.mkdtemp()
        logging.debug("temp dir is: %s" % test_dir)
    else:
        RepoResolver.clear_folder(test_dir)
        test_dir = tempfile.mkdtemp()


def clean_workspace():
    global test_dir
    if test_dir is None:
        return

    if os.path.isdir(test_dir):
        RepoResolver.clear_folder(test_dir)
        test_dir = None


def get_first_file(folder):
    folder_list = os.listdir(folder)
    for file_path in folder_list:
        path = os.path.join(folder, file_path)
        if os.path.isfile(path):
            return path
    return None


class TestRepoResolver(unittest.TestCase):
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

        # check to make sure that we can clone a branch correctly
    def test_clone_branch_repo(self):
        # create an empty directory- and set that as the workspace
        RepoResolver.resolve(test_dir, branch_dependency)
        folder_path = os.path.join(test_dir, branch_dependency["Path"])
        details = RepoResolver.get_details(folder_path)
        self.assertEqual(details['Url'], branch_dependency['Url'])
        self.assertEqual(details['Branch'], branch_dependency['Branch'])

    # don't create a git repo, create the folder, add a file, try to clone in the folder, it should throw an exception
    def test_wont_delete_files(self):
        folder_path = os.path.join(test_dir, commit_dependency["Path"])
        os.makedirs(folder_path)
        file_path = os.path.join(folder_path, "test.txt")
        file_path = os.path.join(
            test_dir, branch_dependency["Path"], "test.txt")
        out_file = open(file_path, "w+")
        out_file.write("Make sure we don't delete this")
        out_file.close()
        self.assertTrue(os.path.isfile(file_path))
        with self.assertRaises(Exception):
            RepoResolver.resolve(test_dir, branch_dependency)
            self.fail("We shouldn't make it here")
        self.assertTrue(os.path.isfile(file_path))

    # don't create a git repo, create the folder, add a file, try to clone in the folder, will force it to happen
    def test_will_delete_files(self):
        folder_path = os.path.join(test_dir, commit_dependency["Path"])
        os.makedirs(folder_path)
        file_path = os.path.join(folder_path, "test.txt")
        out_file = open(file_path, "w+")
        out_file.write("Make sure we don't delete this")
        out_file.close()
        self.assertTrue(os.path.exists(file_path))
        try:
            RepoResolver.resolve(test_dir, commit_dependency, force=True)
        except:
            self.fail("We shouldn't fail when we are forcing")
        details = RepoResolver.get_details(folder_path)
        self.assertEqual(details['Url'], commit_dependency['Url'])

    def test_wont_delete_dirty_repo(self):
        RepoResolver.resolve(test_dir, commit_dependency)

        folder_path = os.path.join(test_dir, commit_dependency["Path"])
        file_path = get_first_file(folder_path)
        # make sure the file already exists
        self.assertTrue(os.path.isfile(file_path))
        out_file = open(file_path, "a+")
        out_file.write("Make sure we don't delete this")
        out_file.close()
        self.assertTrue(os.path.exists(file_path))

        with self.assertRaises(Exception):
            RepoResolver.resolve(test_dir, commit_dependency, update_ok=True)

    def test_will_delete_dirty_repo(self):
        RepoResolver.resolve(test_dir, commit_dependency)
        folder_path = os.path.join(test_dir, commit_dependency["Path"])
        file_path = get_first_file(folder_path)
        # make sure the file already exists
        self.assertTrue(os.path.isfile(file_path))
        out_file = open(file_path, "a+")
        out_file.write("Make sure we don't delete this")
        out_file.close()
        self.assertTrue(os.path.exists(file_path))

        try:
            RepoResolver.resolve(test_dir, commit_later_dependency, force=True)
        except:
            self.fail("We shouldn't fail when we are forcing")

    # check to make sure we can clone a commit correctly

    def test_clone_commit_repo(self):
        # create an empty directory- and set that as the workspace
        RepoResolver.resolve(test_dir, commit_dependency)
        folder_path = os.path.join(test_dir, commit_dependency["Path"])
        details = RepoResolver.get_details(folder_path)

        self.assertEqual(details['Url'], commit_dependency['Url'])
        self.assertEqual(details['Commit'], commit_dependency['Commit'])

    # check to make sure we can clone a commit correctly
    def test_fail_update(self):
        # create an empty directory- and set that as the workspace
        RepoResolver.resolve(test_dir, commit_dependency)
        folder_path = os.path.join(test_dir, commit_dependency["Path"])
        details = RepoResolver.get_details(folder_path)

        self.assertEqual(details['Url'], commit_dependency['Url'])
        self.assertEqual(details['Commit'], commit_dependency['Commit'])
        # first we checkout
        with self.assertRaises(Exception):
            RepoResolver.resolve(test_dir, commit_later_dependency)

        details = RepoResolver.get_details(folder_path)
        self.assertEqual(details['Url'], commit_dependency['Url'])
        self.assertEqual(details['Commit'], commit_dependency['Commit'])

    def test_does_update(self):
        # create an empty directory- and set that as the workspace
        RepoResolver.resolve(test_dir, commit_dependency)
        folder_path = os.path.join(test_dir, commit_dependency["Path"])
        details = RepoResolver.get_details(folder_path)

        self.assertEqual(details['Url'], commit_dependency['Url'])
        self.assertEqual(details['Commit'], commit_dependency['Commit'])
        # first we checkout
        try:
            RepoResolver.resolve(
                test_dir, commit_later_dependency, update_ok=True)
        except:
            self.fail("We are not supposed to throw an exception")
        details = RepoResolver.get_details(folder_path)

        self.assertEqual(details['Url'], commit_later_dependency['Url'])
        self.assertEqual(details['Commit'], commit_later_dependency['Commit'])

    def test_cant_switch_urls(self):
        # create an empty directory- and set that as the workspace
        RepoResolver.resolve(test_dir, branch_dependency)
        folder_path = os.path.join(test_dir, branch_dependency["Path"])

        details = RepoResolver.get_details(folder_path)

        self.assertEqual(details['Url'], branch_dependency['Url'])
        # first we checkout
        with self.assertRaises(Exception):
            RepoResolver.resolve(test_dir, microsoft_branch_dependency)

        details = RepoResolver.get_details(folder_path)
        self.assertEqual(details['Url'], branch_dependency['Url'])

    def test_ignore(self):
        # create an empty directory- and set that as the workspace
        RepoResolver.resolve(test_dir, branch_dependency)
        folder_path = os.path.join(test_dir, branch_dependency["Path"])

        details = RepoResolver.get_details(folder_path)

        self.assertEqual(details['Url'], branch_dependency['Url'])
        # first we checkout

        RepoResolver.resolve(
            test_dir, microsoft_branch_dependency, ignore=True)

        details = RepoResolver.get_details(folder_path)
        self.assertEqual(details['Url'], branch_dependency['Url'])

    def test_will_switch_urls(self):
        # create an empty directory- and set that as the workspace
        RepoResolver.resolve(test_dir, branch_dependency)

        folder_path = os.path.join(test_dir, branch_dependency["Path"])

        details = RepoResolver.get_details(folder_path)

        self.assertEqual(details['Url'], branch_dependency['Url'])
        # first we checkout
        try:
            RepoResolver.resolve(
                test_dir, microsoft_branch_dependency, force=True)
        except:
            self.fail("We shouldn't fail when we are forcing")

        details = RepoResolver.get_details(folder_path)
        self.assertEqual(details['Url'], microsoft_branch_dependency['Url'])


if __name__ == '__main__':
    unittest.main()
