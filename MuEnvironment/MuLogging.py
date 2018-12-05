# @file MuLogging.py
# Handle basic logging config for Project Mu Builds
# MuBuild splits logs into a master log and per package.
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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCEOR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
##
import logging
import sys
from datetime import datetime
import os
import shutil
from MuPythonLibrary import MuAnsiHandler
from MuPythonLibrary import MuMarkdownHandler
from MuPythonLibrary import MuStringHandler


SECTION = logging.CRITICAL + 1  # just above critical


def clean_build_logs(ws):
    # Make sure that we have a clean environment.
    if os.path.isdir(os.path.join(ws, "Build", "BuildLogs")):
        shutil.rmtree(os.path.join(ws, "Build", "BuildLogs"))


def get_section_level():
    return SECTION


# called to setup Buildlog_master as well as buildlogs for the individual packages
def setup_logging(workspace, filename=None,
                  loghandle=None,
                  use_color=True,
                  use_azure_colors=False):

    if loghandle is not None:
        stop_logging(loghandle)

    logging_level = logging.INFO

    if filename is None:
        filename = "BUILDLOG_MASTER.txt"

    # setup logger
    logger = logging.getLogger('')
    logger.setLevel(logging.NOTSET)  # we capture everything
    default_formatter = logging.Formatter(
        "%(levelname)s - %(message)s")

    # todo define section level
    # add section as a level to the logger
    section_level = get_section_level()
    if logging.getLevelName(section_level) is not "SECTION":
        logging.addLevelName(section_level, "SECTION")

    if len(logger.handlers) == 0:
        # Create the main console as logger
        handler = setup_console_logging(use_azure_colors, use_color, level=logging.INFO)
        logger.addHandler(handler)

    logfile = os.path.join(workspace, "Build", "BuildLogs", filename)
    if(not os.path.isdir(os.path.dirname(logfile))):
        os.makedirs(os.path.dirname(logfile))

    # Create file logger
    filelogger = logging.FileHandler(filename=(logfile), mode='w')
    filelogger.setLevel(logging_level)
    filelogger.setFormatter(default_formatter)
    logger.addHandler(filelogger)

    # add markdown handler
    markdown_filename = os.path.splitext(filename)[0] + ".md"
    markdown_path = os.path.join(
        workspace, "Build", "BuildLogs", markdown_filename)
    markdownHandler = MuMarkdownHandler.MarkdownFileHandler(markdown_path)
    markdownHandler.setFormatter(default_formatter)
    markdownHandler.setLevel(logging_level)
    logger.addHandler(markdownHandler)

    logging.info("Log Started: " + datetime.strftime(datetime.now(), "%A, %B %d, %Y %I:%M%p"))
    logging.info("Running Python version: " + str(sys.version_info))

    return logfile, filelogger


# sets up a colored console logger
def setup_console_logging(use_azure_colors, use_color=True, level=logging.INFO, formatter_msg="%(levelname)s - %(message)s"):
    if use_azure_colors or use_color:
        formatter = MuAnsiHandler.ColoredFormatter(formatter_msg, use_azure=use_azure_colors)
        console = MuAnsiHandler.ColoredStreamHandler()
    else:
        formatter = logging.Formatter(formatter_msg)
        console = logging.StreamHandler()

    console.setLevel(level)
    console.setFormatter(formatter)

    return console


def stop_logging(loghandle):
    loghandle.close()
    logging.getLogger('').removeHandler(loghandle)


def create_output_stream(level=logging.INFO):
    # creates an output stream that is in memory
    handler = MuStringHandler.StringStreamHandler()
    logger = logging.getLogger('')
    handler.setLevel(level)
    logger.addHandler(handler)
    return handler


def remove_output_stream(handler):
    logger = logging.getLogger('')
    logger.removeHandler(handler)
