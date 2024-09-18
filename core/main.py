import argparse
import logging
import os
import shutil
import subprocess

# import build system modules
from envsetup import *
from lunch_target import *
from soong_ui import *
from build_logger import *


# global variables
build_top = os.environ.get("BUILD_TOP")
build_system_version = '1.0'

# global variables
BUILD_TOP = os.environ.get("BUILD_TOP")
BUILD_SYSTEM_VERSION = '1.0'
MAKE = 'make'
CMAKE = 'cmake'
CLANG = 'clang'
STRIP = 'strip'

def exec_full_build():
    pr_info("Executing full build...", log_tag="BUILD")
    dump_info()
    setup_ccache()
    soong_main()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['clean', 'clean_module', 'target'], help='command to run')
    parser.add_argument('--module', help='target module to clean')
    return parser.parse_args()


def main():
    exec_full_build()

if __name__ == '__main__':
    main()