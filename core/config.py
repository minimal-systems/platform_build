import os
import platform
import sys

# Utility variables
build_system = 'build/make/core'
build_system_common = 'build/make/common'

# append the build system to the path
sys.path.append(build_system)
sys.path.append(build_system_common)

UNAME = platform.system() + '-' + platform.machine()

SRC_TARGET_DIR = os.path.join(os.getcwd(), 'build/make/target')

from core import *
from math_build import *
from json import *
from strings_build import *

# Build system internal files
BUILD_COMBOS = os.path.join(build_system, 'combo')

CLEAR_VARS = os.path.join(build_system, 'clear_vars.mk')

BUILD_HOST_STATIC_LIBRARY = os.path.join(build_system, 'host_static_library.mk')
BUILD_HOST_SHARED_LIBRARY = os.path.join(build_system, 'host_shared_library.mk')
BUILD_STATIC_LIBRARY = os.path.join(build_system, 'static_library.mk')
BUILD_HEADER_LIBRARY = os.path.join(build_system, 'header_library.mk')
BUILD_SHARED_LIBRARY = os.path.join(build_system, 'shared_library.mk')
BUILD_EXECUTABLE = os.path.join(build_system, 'executable.mk')
BUILD_HOST_EXECUTABLE = os.path.join(build_system, 'host_executable.mk')
BUILD_PACKAGE = os.path.join(build_system, 'package.mk')
BUILD_HOST_PREBUILT = os.path.join(build_system, 'host_prebuilt.mk')
BUILD_PREBUILT = os.path.join(build_system, 'prebuilt.mk')
BUILD_MULTI_PREBUILT = os.path.join(build_system, 'multi_prebuilt.mk')
BUILD_COPY_HEADERS = os.path.join(build_system, 'copy_headers.mk')
BUILD_NOTICE_FILE = os.path.join(build_system, 'notice_files.mk')

# Simulating parsing out any modifier targets
hide = '@'

# Print out configuration for debugging purposes
def print_config():
    print("UNAME:", UNAME)
    print("SRC_TARGET_DIR:", SRC_TARGET_DIR)
    print("BUILD_COMBOS:", BUILD_COMBOS)
    print("CLEAR_VARS:", CLEAR_VARS)
    print("BUILD_HOST_STATIC_LIBRARY:", BUILD_HOST_STATIC_LIBRARY)
    print("BUILD_HOST_SHARED_LIBRARY:", BUILD_HOST_SHARED_LIBRARY)
    print("BUILD_STATIC_LIBRARY:", BUILD_STATIC_LIBRARY)
    print("BUILD_HEADER_LIBRARY:", BUILD_HEADER_LIBRARY)
    print("BUILD_SHARED_LIBRARY:", BUILD_SHARED_LIBRARY)
    print("BUILD_EXECUTABLE:", BUILD_EXECUTABLE)
    print("BUILD_HOST_EXECUTABLE:", BUILD_HOST_EXECUTABLE)
    print("BUILD_PACKAGE:", BUILD_PACKAGE)
    print("BUILD_HOST_PREBUILT:", BUILD_HOST_PREBUILT)
    print("BUILD_PREBUILT:", BUILD_PREBUILT)
    print("BUILD_MULTI_PREBUILT:", BUILD_MULTI_PREBUILT)
    print("BUILD_COPY_HEADERS:", BUILD_COPY_HEADERS)
    print("BUILD_NOTICE_FILE:", BUILD_NOTICE_FILE)