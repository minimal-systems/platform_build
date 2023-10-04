#!/usr/bin/python
import json
import os
import sys
from prettytable import PrettyTable


# Global variables
BUILD_TOP = os.environ.get("BUILD_TOP")
TARGET_DEVICE = os.environ.get("TARGET_DEVICE")


# Utility functions
def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)


def dump_info():
    x = PrettyTable(border=True)
    x.field_names = ['Varible', 'Value']
    x.align = 'l'
    x.add_row(['PLATFORM_VERSION_CODENAME', platform_version_codename])
    x.add_row(['PLATFORM_VERSION', platform_version])
    x.add_row(['TARGET_PRODUCT', target_device])
    x.add_row(['TARGET_BUILD_VARIANT', target_build_variant])
    x.add_row(['TARGET_ARCH', target_board_platform])
    x.add_row(['TARGET_ARCH_VARIANT', target_arch_variant])
    x.add_row(['TARGET_CPU_VARIANT', target_cpu_abi])
    x.add_row(['HOST_ARCH', host_arch])
    x.add_row(['HOST_2ND_ARCH', host_arch])
    x.add_row(['HOST_OS', host_os])
    x.add_row(['HOST_OS_EXTRA', host_os_extra])
    x.add_row(['BUILD_ID', build_id])
    x.add_row(['OUT_DIR', out_dir])
    print(x.get_string(header=False, border=True))



def write_json():
    device_info = {
        "target_product": f'{target_device}',
        "target_arch": f"{target_board_platform}",
        "target_arch_variant": f'{target_arch_variant}',
        "target_cpu_variant": f"{target_cpu_abi}",
    }
    with open(f"{BUILD_TOP}/out/soong/target_device.json", "w") as write_file:
        json.dump(device_info, write_file, indent=4, sort_keys=True)


def generate_target_device_config():
    os.makedirs(f'{BUILD_TOP}/out/target/product/{TARGET_DEVICE}', exist_ok=True)
    os.makedirs(f'{BUILD_TOP}/out/soong', exist_ok=True)
    touch(f'{BUILD_TOP}/out/soong/build_generic.lock')
    write_json()
    dump_info()


# Check command-line arguments
if len(sys.argv) == 1:
    print("lunch <product_name>-<build_variant>")
    print("          Selects <product_name> as the product to build, and <build_variant> as the variant to")
    print("          build, and stores those selections in the environment to be read by subsequent")
    print("          invocations of 'm' etc.")
    sys.exit(1)


# Import device-specific modules
sys.path.append(f"{BUILD_TOP}/device/{TARGET_DEVICE}")
from envsetup import *
from device_info import *


# Main function
def main():
    generate_target_device_config()


if __name__ == '__main__':
    main()
