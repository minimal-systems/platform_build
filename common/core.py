import os
import sys

# disable __pycache__ directory
sys.dont_write_bytecode = True

# Utility variables
empty = ""
space = " "
comma = ","

# The pound character "#"
pound = "#"

# Unfortunately you can't simply define backslash as \ or \\.
backslash = "\\"

# Convert these variables to lowercase
top = "."
topdir = ""
# Support UPPER_CASE variables for backwards compatibility
TOP = top
TOPDIR = topdir

# Prevent accidentally changing these variables
readonly_vars = ["shell", "empty", "space", "comma", "newline", "pound", "backslash", "top", "topdir"]

# Basic warning/error wrappers
def pretty_warning(message):
    print(f"Warning: {message}")

def pretty_error(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)

# Only use LINUX_BUILD_SHELL to wrap around bash
linux_build_shell = os.environ.get('LINUX_BUILD_SHELL')
if linux_build_shell:
    shell = linux_build_shell
else:
    # Use bash, not whatever shell somebody has installed as /bin/sh
    shell = "/bin/bash"

def main():
    # Example usage of the pretty_warning and pretty_error functions
    pretty_warning("This is a warning message")
    pretty_error("This is an error message")

if __name__ == "__main__":
    main()
