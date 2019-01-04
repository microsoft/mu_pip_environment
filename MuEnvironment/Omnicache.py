import os
import sys
import logging
import argparse
import datetime
import yaml
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from MuEnvironment import MuLogging
from MuPythonLibrary import UtilityFunctions


class OmniCacheConfig():
    '''
    class to manage the Internal Omnicache config file.
    Load, Save, Version check, etc.
    '''

    CONFIG_VERSION = 1

    def __init__(self, absfilepath):
        self.version = OmniCacheConfig.CONFIG_VERSION
        self.filepath = absfilepath
        self.last_change = datetime.datetime.strftime(datetime.datetime.now(), "%A, %B %d, %Y %I:%M%p")
        if(os.path.isfile(self.filepath)):
            self._Load()
        else:
            self.remotes = {}

    def _Load(self):
        with open(self.filepath) as ymlfile:
            content = yaml.safe_load(ymlfile)

        if "version" not in content:
            raise Exception("Unsupported Config Version (None)")
        elif content["version"] == self.version:
            # parse yml into config data
            self.remotes = {x["name"]: x for x in content["remotes"]}
            self.last_change = content["last_change"]
        else:
            self._Transition(content)

    def Save(self):
        data = {"version": self.version, "remotes": list(self.remotes.values()),
                "last_change": datetime.datetime.strftime(datetime.datetime.now(),
                                                          "%A, %B %d, %Y %I:%M%p")}
        with open(self.filepath, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)

    def _Transition(self, data):
        # Add code here to move old config data to new format
        raise Exception("Unsupported config data")

    def Log(self, level=logging.DEBUG):
        logging.log(level, "OmniCache Config")
        logging.log(level, " Filepath: {0}".format(self.filepath))
        logging.log(level, " Version: {%d}", self.version)
        logging.log(level, " Remotes({%d})", len(self.remotes))
        for remote in self.remotes.values():
            rstring = "Name: {0} Url: {1} TagSync: {2}".format(remote["name"], remote["url"], ("tag" in remote))
            logging.log(level, "   " + rstring)

    def Add(self, name, url, tags=False):
        remote = {"name": name, "url": url}
        if(tags):
            remote["tag"] = True
        self.remotes[name] = remote

    def Remove(self, name):
        if name in self.remotes:
            del self.remotes[name]

    def Contains(self, name):
        return name in self.remotes


OMNICACHE_VERSION = "0.9"
OMNICACHE_FILENAME = "omnicache.yaml"


def CommonFilePathHandler(path):
    '''
    function to check for absolute path and if not
    concat with current dir and return absolute real path
    '''
    if(not os.path.isabs(path)):
        path = os.path.join(os.getcwd(), path)
    path = os.path.realpath(path)
    return path


def AddEntriesFromConfig(config, input_config_file):
    '''
    Add config entries found in the config file
    to the omnicache. Entries already in omnicache
    with the same name will be updated.

    return
        the number of entries added to cache
    '''

    count = 0
    with open(input_config_file) as ymlfile:
        content = yaml.safe_load(ymlfile)
    if("remotes" in content):
        for remote in content["remotes"]:
            if("tag" in remote):
                AddEntry(config, remote["name"], remote["url"], bool(remote["tag"]))
            else:
                AddEntry(config, remote["name"], remote["url"])
            count += 1
    return (count, content["remotes"])


def InitOmnicache(path):
    logging.critical("Initialize Omnicache to {0}".format(path))
    os.makedirs(path)
    return UtilityFunctions.RunCmd("git", "--bare init", workingdir=path)


def AddEntry(config, name, url, tags=False):
    if config.Contains(name):
        logging.info("Updating remote ({0} : {1}) in Omnicache".format(name, url))
        param = "remote set-url {0} {1}".format(name, url)
    else:
        logging.info("Adding remote ({0} : {1}) to Omnicache".format(name, url))
        param = "remote add {0} {1}".format(name, url)

    if(UtilityFunctions.RunCmd("git", param) == 0):
        config.Add(name, url, tags)
    else:
        logging.error("Failed to add remote for {0}".format(name))


def RemoveEntry(config, name):
    logging.info("Removing remote named {0}".format(name))
    param = "remote remove {0}".format(name)
    if(UtilityFunctions.RunCmd("git", param) == 0):
        config.Remove(name)
    else:
        logging.error("Failed to remove remote for {0}".format(name))


def ConsistencyCheckCacheConfig(config):
    '''
    Check the git remote list vs what is in the config file
    Add remote to git for anything only in config
    Add git remote from git into the config file (tags will be false)

    return
        0:          success
        non-zero:   indicates an error
    '''

    logging.debug("start consistency check between git and omnicache config")
    out = StringIO()
    param = "remote -v"
    gitnames = []  # list of git remote names as found in git repo
    gitret = UtilityFunctions.RunCmd("git", param, outstream=out)

    if(gitret != 0):
        logging.critical("Could not list git remotes")
        return gitret

    lines = out.getvalue().split('\n')
    out.close()
    for line in lines:
        line = line.strip()
        if(len(line) == 0):
            # empty line
            continue
        git = line.split()
        gitnames.append(git[0])  # save for later
        if(not config.Contains(git[0])):
            logging.warning("Found entry in git not in config.  Name: {0} Url: {1}".format(git[0], git[1]))
            config.Add(git[0], git[1])
            config.Save()

    gitnames = set(gitnames)
    for remote in config.remotes.values():
        if(remote["name"] not in gitnames):
            logging.warning("Found entry in config not in git. Name: {0} Url: {1}".format(remote["name"],
                                                                                          remote["url"]))
            param = "remote add {0} {1}".format(remote["name"], remote["url"])
            UtilityFunctions.RunCmd("git", param)

    return 0


def FetchEntry(name, tags=False):
    '''
    do git operation to fetch a single entry

    return
        0:          success
        non-zero:   git command line error
    '''

    param = "fetch {0}".format(name)
    if(not tags):
        param += " --no-tags"
    else:
        param += " --tags"
        # might want to look at something more complex to avoid tag conflicts
        # https://stackoverflow.com/questions/22108391/git-checkout-a-remote-tag-when-two-remotes-have-the-same-tag-name
        # param += "+refs/heads/:refs/remotes/{0}/ +refs/tags/:refs/rtags/{0}/".format(name)
    return UtilityFunctions.RunCmd("git", param)


def get_cli_options():
    parser = argparse.ArgumentParser(description='Tool to provide easy method create and manage the OMNICACHE', )
    parser.add_argument(dest="cache_dir", help="path to an existing or desired OMNICACHE directory")
    parser.add_argument("--new", dest="new", help="Initialize the OMNICACHE.  MUST NOT EXIST",
                        action="store_true", default=False)
    parser.add_argument("--init", dest="init", help="Initialize the OMNICACHE if it doesn't already exist",
                        action="store_true", default=False)
    parser.add_argument("-l", "--list", dest="list", default=False, action="store_true",
                        help="List config of OMNICACHE")
    parser.add_argument("-a", "--add", dest="add", nargs='*', action="append",
                        help="Add config entry to OMNICACHE <name> <url> <Sync tags optional default=False>",
                        default=[])
    parser.add_argument("-c", "--configfile", dest="input_config_file", default=None,
                        help="Add new entries from config file to OMNICACHE")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-u", "--update", "--fetch", dest="fetch", action="store_true",
                       help="Update the Omnicache.  All cache changes also cause a fetch", default=False)
    group.add_argument("--no-fetch", dest="no_fetch", action="store_true",
                       help="Prevent auto-fetch if implied by other arguments.", default=False)
    parser.add_argument("-r", "--remove", dest="remove", nargs="?", action="append",
                        help="remove config entry from OMNICACHE <name>", default=[])
    parser.add_argument('--version', action='version', version='%(prog)s ' + OMNICACHE_VERSION)
    parser.add_argument("--debug", dest="debug", help="Output all debug messages to console",
                        action="store_true", default=False)
    args = parser.parse_args()
    return args


def main():
    # setup main console as logger
    logger = logging.getLogger('')
    logger.setLevel(logging.NOTSET)
    console = MuLogging.setup_console_logging(False)
    logger.addHandler(console)

    ErrorCode = 0
    auto_fetch = False
    input_config_remotes = None

    # arg parse
    args = get_cli_options()

    if(args.debug):
        console.setLevel(logging.DEBUG)

    logging.info("Log Started: " + datetime.datetime.strftime(
        datetime.datetime.now(), "%A, %B %d, %Y %I:%M%p"))

    args.cache_dir = CommonFilePathHandler(args.cache_dir)
    logging.debug("OMNICACHE dir: {0}".format(args.cache_dir))

    # input config file for adding new entries
    if(args.input_config_file is not None):
        args.input_config_file = CommonFilePathHandler(args.input_config_file)
        if(not os.path.isfile(args.input_config_file)):
            logging.critical("Invalid -c argument given.  File ({0}) isn't valid".format(args.input_config_file))
            return -4

    logging.debug("Args: " + str(args))

    omnicache_config = None  # config object
    omnicache_config_file = os.path.join(args.cache_dir, OMNICACHE_FILENAME)

    if(args.new):
        if(os.path.isdir(args.cache_dir)):
            logging.critical("--new argument given but OMNICACHE path already exists!")
            return -1
        InitOmnicache(args.cache_dir)
        auto_fetch = True

    if(args.init):
        if(os.path.isdir(args.cache_dir)):
            if(os.path.isfile(omnicache_config_file)):
                logging.debug("OMNICACHE already exists.  No need to initialize")
        else:
            InitOmnicache(args.cache_dir)
        auto_fetch = True

    # Check to see if exists
    if(not os.path.isdir(args.cache_dir)):
        logging.critical("OMNICACHE path invalid.")
        return -2

    # load config
    omnicache_config = OmniCacheConfig(omnicache_config_file)

    os.chdir(args.cache_dir)

    if(len(args.add) > 0):
        auto_fetch = True
        for inputdata in args.add:
            if len(inputdata) == 2:
                AddEntry(omnicache_config, inputdata[0], inputdata[1])
            elif len(inputdata) == 3:
                AddEntry(omnicache_config, inputdata[0], inputdata[1], bool(inputdata[2]))
            else:
                logging.critical("Invalid Add Entry.  Should be <name> <url> <Sync Tags optional default=False>")
                return -3

    if(args.input_config_file is not None):
        (count, input_config_remotes) = AddEntriesFromConfig(omnicache_config, args.input_config_file)
        if(count > 0):
            auto_fetch = True

    if(len(args.remove) > 0):
        for inputdata in args.remove:
            RemoveEntry(omnicache_config, inputdata)

    omnicache_config.Save()

    if(args.fetch or (auto_fetch and not args.no_fetch)):
        logging.critical("Updating OMNICACHE")
        # as an optimization, if input config file provided, only fetch remotes specified in input config
        # otherwise, fetch all remotes in the OmniCache
        if (input_config_remotes is not None):
            remotes = (x["name"] for x in input_config_remotes)
        else:
            remotes = omnicache_config.remotes.keys()
        for remote in remotes:
            ret = FetchEntry(omnicache_config.remotes[remote]["name"], ("tag" in omnicache_config.remotes[remote]))
            if(ret != 0) and (ErrorCode == 0):
                ErrorCode = ret

    if(args.list):
        ret = ConsistencyCheckCacheConfig(omnicache_config)
        if(ret != 0) and (ErrorCode == 0):
            ErrorCode = ret
        print("List OMNICACHE content\n")
        if(len(omnicache_config.remotes) == 0):
            logging.warning("No Remotes to show")

        for remote in omnicache_config.remotes.values():
            rstring = "Name: {0}\n  Url: {1}\n  Sync Tags: {2}".format(remote["name"], remote["url"], ("tag" in remote))
            print(" " + rstring + "\n\n")

    print("To use your OMNICACHE with Project Mu builds set the env variable:")
    print("set OMNICACHE_PATH=" + args.cache_dir)

    return ErrorCode


if __name__ == '__main__':
    retcode = main()
    logging.shutdown()
    sys.exit(retcode)
