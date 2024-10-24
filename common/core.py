#
# Copyright (C) 2024 The Minimal Systems Project
# SPDX-License-Identifier: GPL-2.0-or-later
# core.py - Core variables and functions for the build system.

# Only use LINUX_BUILD_SHELL to wrap around bash.
# DO NOT use other shells such as zsh.
import os

# Define the shell environment.
# First, check if 'LINUX_BUILD_SHELL' is set in the environment variables.
# If it exists, use its value. Otherwise, default to '/bin/bash' as the preferred shell.
# This avoids relying on '/bin/sh' or any other non-standard shells.
SHELL = os.environ.get('LINUX_BUILD_SHELL', '/bin/bash')

# Utility variables are commonly used for formatting or string manipulations.

# Empty string, used when a placeholder or absence of value is needed.
empty = ''

# Single space, useful for separating words or values in concatenations.
space = ' '

# Comma character, used for separating values in lists or CSV formats.
comma = ','

# Newline character, for creating line breaks in strings (equivalent to pressing "Enter").
newline = '\n'

# Pound character, often used for commenting in many programming languages.
pound = '#'

# Backslash character, used for escaping special characters or as a file path separator.
# In Python, the backslash needs to be escaped, hence the double backslash '\\'.
backslash = '\\'

# Current directory, equivalent to defining TOP :=$= . in Makefile.
TOP = '.'
top = TOP  # Lowercase variable for backward compatibility.

# Empty directory placeholder, equivalent to TOPDIR :=$= in Makefile.
TOPDIR = ''
topdir = TOPDIR  # Lowercase variable for backward compatibility.
