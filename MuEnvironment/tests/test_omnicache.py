import os
from MuEnvironment import Omnicache


def test_basic_init():
    valueabs = os.path.join(os.path.abspath(os.getcwd()), "test", "test2")
    result = Omnicache.CommonFilePathHandler(valueabs)
    assert(result == valueabs)


def test_commonfilepathhandler_real():
    valueabs = os.path.join(os.path.abspath(os.getcwd()), "test", "test2")
    result = Omnicache.CommonFilePathHandler(os.path.join(valueabs, "..", "test2"))
    assert(result == valueabs)


def test_commonfilepathhandler_relative():
    valueabs = os.path.join(os.path.abspath(os.getcwd()), "test", "test2")
    result = Omnicache.CommonFilePathHandler(os.path.join("test", "test2"))
    assert(result == valueabs)
