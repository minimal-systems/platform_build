#
# Copyright (C) 2024 The Minimal Systems Project
# SPDX-License-Identifier: GPL-2.0-or-later

# Only use LINUX_BUILD_SHELL to wrap around bash.
# DO NOT use other shells such as zsh.
import os

# Define the shell environment.
# First, check if 'LINUX_BUILD_SHELL' is set in the environment variables.
# If it exists, use its value. Otherwise, default to '/bin/bash' as the preferred shell.
# This avoids relying on '/bin/sh' or any other non-standard shells.
SHELL = os.environ.get('LINUX_BUILD_SHELL', '/bin/bash')

