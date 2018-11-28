## @file RepoResolver.py
# This module supports Project Mu Builds 
# and gathering external dependencies (git repos). 
#
##
# Copyright (c) 2018, Microsoft Corporation
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
from MuEnvironment.MuGit import Repo
import shutil
import stat

#this follows a documented flow chart
#TODO: include link to flowchart?


# checks out dependency at git_path
def resolve(file_system_path, dependency, force=False,ignore=False, update_ok=False):
    logging.info("Checking for dependency {0}".format(dependency["Path"]))
    git_path = os.path.abspath(file_system_path)

    #check if we have a path in our dependency
    if "Path" in dependency and not git_path.endswith(os.path.relpath(dependency["Path"])):
        # if we don't already the the path from the dependency at the end of the path we've been giving
        git_path = os.path.join(git_path, dependency["Path"])
        
    ##
    ## NOTE - this process is defined in the Readme.md including flow chart for this behavior
    ##
    if not os.path.isdir(git_path):
        clone_repo(git_path, dependency)
        checkout(git_path, dependency, Repo(git_path), True, False)
        return

    folder_empty = len(os.listdir(git_path)) == 0
    if folder_empty: #if the folder is empty, we can clone into it
        clone_repo(git_path, dependency)
        checkout(git_path, dependency, Repo(git_path), True, False)
        return

    repo = Repo(git_path)
    if not repo.initalized: #if there isn't a .git folder in there
        if force:
            clear_folder(git_path)
            logging.warning("Folder {0} is not a git repo and is being overwritten!".format(git_path))
            clone_repo(git_path, dependency)
            checkout(git_path, dependency, Repo(git_path), True, False)
            return
        else:
            if(ignore):
                logging.warning("Folder {0} is not a git repo but Force parameter not used.  Ignore State Allowed.".format(git_path))
                return
            else:
                logging.critical("Folder {0} is not a git repo and it is not empty.".format(git_path))
                raise Exception("Folder {0} is not a git repo and it is not empty".format(git_path))

    if repo.dirty:
        if force:
            clear_folder(git_path)
            logging.warning("Folder {0} is a git repo but is dirty and is being overwritten as requested!".format(git_path))
            clone_repo(git_path, dependency)
            checkout(git_path, dependency, Repo(git_path), True, False)
            return
        else:
            if(ignore):
                logging.warning("Folder {0} is a git repo but is dirty and Force parameter not used.  Ignore State Allowed.".format(git_path))
                return
            else:
                logging.critical("Folder {0} is a git repo and is dirty.".format(git_path))
                raise Exception("Folder {0} is a git repo and is dirty.".format(git_path))

    if repo.remotes.origin.url != dependency["Url"]:
        if force:
            clear_folder(git_path)
            logging.warning("Folder {0} is a git repo but it is at a different repo and is being overwritten as requested!".format(git_path))
            clone_repo(git_path, dependency)
            checkout(git_path, dependency, Repo(git_path), True, False)
        else:
            if ignore:
                logging.warning("Folder {0} is a git repo pointed at a different remote.  Can't checkout or sync state".format(git_path))
                return
            else:
                logging.critical("The URL of the git Repo {2} in the folder {0} does not match {1}".format(git_path,dependency["Url"],repo.remotes.origin.url))
                raise Exception("The URL of the git Repo {2} in the folder {0} does not match {1}".format(git_path,dependency["Url"],repo.remotes.origin.url))

    checkout(git_path, dependency, repo, update_ok, ignore, force)

##
# dependencies is a list of objects - it has Path, Commit, Branch,
def resolve_all(WORKSPACE_PATH, dependencies, force=False, ignore=False, update_ok=False):

    packages = []
    if force:
        logging.info("Resolving dependencies by force")
    if update_ok:
        logging.info("Resolving dependencies with updates as needed")
    for dependency in dependencies:
        git_path = os.path.join(WORKSPACE_PATH, dependency["Path"])
        packages.append(git_path)
        resolve(git_path, dependency, force, ignore, update_ok)

    # print out the details- this is optional
    for dependency in dependencies:
        git_path = os.path.join(WORKSPACE_PATH, dependency["Path"])
        GitDetails = get_details(git_path)
        #print out details
        logging.info("{3} = Git Details: Url: {0} Branch {1} Commit {2}".format(GitDetails["Url"], GitDetails["Branch"], GitDetails["Commit"], dependency["Path"]))

    return packages

#Gets the details of a particular repo
def get_details(abs_file_system_path):
    repo = Repo(abs_file_system_path)
    url = repo.remotes.origin.url
    active_branch = repo.active_branch
    head = repo.head.commit
    return {"Url": url, "Branch": active_branch, "Commit": head}

def clear_folder(abs_file_system_path):
    logging.warning("WARNING: Deleting contents of folder {0} to make way for Git repo".format(abs_file_system_path))
    def dorw(action, name, exc):
        os.chmod(name, stat.S_IWRITE)
        if(os.path.isdir(name)):
            os.rmdir(name)
        else:
            os.remove(name)

    shutil.rmtree(abs_file_system_path, onerror=dorw)

#Clones the repo in the folder we need using the dependency object from the json
def clone_repo(abs_file_system_path, DepObj):
    logging.critical("Cloning repo: {0}".format(DepObj["Url"]))
    dest = abs_file_system_path
    if not os.path.isdir(dest):
        os.makedirs(dest, exist_ok=True)
    shallow = False
    if "Commit" in DepObj:
        shallow = False
    repo = Repo.clone_from(DepObj["Url"],dest, shallow = shallow)
    
    return dest


def checkout(abs_file_system_path, dep, repo, update_ok = False, ignore_dep_state_mismatch = False, force = False):

    if "Commit" in dep:
        if update_ok or force:
            repo.fetch()
            repo.checkout(commit = dep["Commit"])
            repo.submodule("update", "--init", "--recursive")
        else:
            if repo.head.commit == dep["Commit"]:
                logging.debug("Dependency {0} state ok without update".format(dep["Path"]))
                return
            elif ignore_dep_state_mismatch:
                logging.warning("Dependency {0} is not in sync with requested commit.  Ignore state allowed".format(dep["Path"]))
                return
            else:
                logging.critical("Dependency {0} is not in sync with requested commit.  Fail.".format(dep["Path"]))
                raise Exception("Dependency {0} is not in sync with requested commit.  Fail.".format(dep["Path"]))

    elif "Branch" in dep:
        if update_ok or force:
            repo.fetch()
            repo.checkout(branch=dep["Branch"])
            repo.submodule("update", "--init", "--recursive")
        else:
            if repo.active_branch == dep["Branch"]:
                logging.debug("Dependency {0} state ok without update".format(dep["Path"]))
                return
            elif ignore_dep_state_mismatch:
                logging.warning("Dependency {0} is not in sync with requested branch.  Ignore state allowed".format(dep["Path"]))
                return
            else:
                error = "Dependency {0} is not in sync with requested branch. Expected: {1}. Got {2} Fail.".format(dep["Path"],dep["Branch"],repo.active_branch)
                logging.critical(error)
                raise Exception(error)
    else:
        raise Exception("Branch or Commit must be specified for {0}".format(dep["Path"]))

