#
# Copyright (C) 2024 The Minimal Systems Project
# SPDX-License-Identifier: GPL-2.0-or-later
# core.py - Core variables and functions for the build system.

import os
import sys
from collections import namedtuple
import inspect

# Create a named tuple to hold the read-only variables.
ReadOnlyVars = namedtuple('ReadOnlyVars', [
    'SHELL', 'empty', 'space', 'comma', 'newline', 'pound', 'backslash', 'TOP', 'TOPDIR'
])

# Instantiate the namedtuple with the required values.
readonly_vars = ReadOnlyVars(
    SHELL=os.environ.get('LINUX_BUILD_SHELL', '/bin/bash'),
    empty='',
    space=' ',
    comma=',',
    newline='\n',
    pound='#',
    backslash='\\',
    TOP='.',
    TOPDIR=''
)

# Access variables (read-only).
SHELL = readonly_vars.SHELL

# Utility variables are commonly used for formatting or string manipulations.

# Empty string, used when a placeholder or absence of value is needed.
empty = readonly_vars.empty

# Single space, useful for separating words or values in concatenations.
space = readonly_vars.space

# Comma character, used for separating values in lists or CSV formats.
comma = readonly_vars.comma

# Newline character, for creating line breaks in strings (equivalent to pressing "Enter").
newline = readonly_vars.newline

# Pound character, often used for commenting in many programming languages.
pound = readonly_vars.pound

# Backslash character, used for escaping special characters or as a file path separator.
# In Python, the backslash needs to be escaped, hence the double backslash '\\'.
backslash = readonly_vars.backslash

# Current directory, equivalent to defining TOP :=$= . in Makefile.
TOP = readonly_vars.TOP
top = TOP  # Backward compatibility with lowercase variable.

# Empty directory placeholder, equivalent to TOPDIR :=$= in Makefile.
TOPDIR = readonly_vars.TOPDIR
topdir = TOPDIR  # Backward compatibility with lowercase variable.

# Basic warning/error/info wrappers. These are designed to include the local
# module information (filename and line number) for use within Python-based
# build files, helping to track issues with relevant context.

def pretty_message(msg, level="error"):
    """
    Outputs messages in a Makefile-style format with dynamic line number and filename.
    
    Args:
        msg (str): The message to be displayed.
        level (str): The type of message, either 'error', 'warning', or 'info'. Defaults to 'error'.
    """
    # Get the caller's frame, filename, and line number
    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno

    # Print the message in the format: filename:lineno: level: msg
    print(f"{filename}:{lineno}: {level}: {msg}", file=sys.stderr)

    # Exit if it's an error
    if level == "error":
        sys.exit(1)

# Example usage:
# pretty_message("This is an info message", level="info")
# pretty_message("This is a warning", level="warning")
# pretty_message("This is an error", level="error")