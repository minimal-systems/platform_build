#!/usr/bin/python3
import json

from build_logger import *
from definitions import *

# Ensure BUILD_TOP and TARGET_DEVICE are set
BUILD_TOP = os.environ.get("BUILD_TOP")
TARGET_DEVICE = os.environ.get("TARGET_DEVICE")
TARGET_BUILD_VARIANT = os.environ.get("TARGET_BUILD_VARIANT")

if not BUILD_TOP or not TARGET_DEVICE or not TARGET_BUILD_VARIANT:
    pr_error("Error: BUILD_TOP, TARGET_DEVICE, and TARGET_BUILD_VARIANT environment variables must be set.")
    sys.exit(1)

try:
    from envsetup import *
    from device_info import *
except ImportError as e:
    pr_error(f"Error importing necessary modules: {e}")
    sys.exit(1)

def main():
    generate_target_device_config()

def generate_target_device_config():
    target_product_dir = os.path.join(BUILD_TOP, "out", "target", "product", TARGET_DEVICE)
    soong_dir = os.path.join(BUILD_TOP, "out", "soong")
    os.makedirs(target_product_dir, exist_ok=True)
    os.makedirs(soong_dir, exist_ok=True)

    touch(os.path.join(soong_dir, f"build_{TARGET_DEVICE}.lock"))
    write_json()
    dump_info()

def write_json():
    device_info = {
        "target_product": target_device,
        "target_arch": target_board_platform,
        "target_arch_variant": target_arch_variant,
        "target_cpu_variant": target_cpu_abi,
    }

    json_file = os.path.join(BUILD_TOP, "out", "soong", "target_device.json")
    with open(json_file, "w") as write_file:
        json.dump(device_info, write_file, indent=4, sort_keys=True)

def dump_info():
    # Data to be printed with '=' between variable and value
    data = [
        ['PLATFORM_VERSION_CODENAME', platform_version_codename],
        ['PLATFORM_VERSION', platform_version],
        ['TARGET_PRODUCT', target_device],
        ['TARGET_BUILD_VARIANT', target_build_variant],
        ['TARGET_ARCH', target_board_platform],
        ['TARGET_ARCH_VARIANT', target_arch_variant],
        ['TARGET_CPU_VARIANT', target_cpu_abi],
        ['HOST_ARCH', host_arch],
        ['HOST_2ND_ARCH', get_host_2nd_arch()],
        ['HOST_OS', host_os],
        ['HOST_OS_EXTRA', host_os_extra],
        ['BUILD_ID', build_id],
        ['OUT_DIR', out_dir],
    ]

    # Print separator
    separator = "=" * 45
    print(separator)

    # Print each line in 'KEY = VALUE' format
    for key, value in data:
        print(f"{key} = {value}")

    # Print separator again at the bottom
    print(separator)
if __name__ == '__main__':
    main()
