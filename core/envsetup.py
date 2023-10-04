#!/usr/bin/env python

import os
import platform
import sys
from pathlib import Path
from build_id import *

# disable creation of __pycache__
sys.dont_write_bytecode = True

host_arch = platform.processor()
host_os = platform.system()
if os.name == 'nt':
    host_os = 'windows'
    host_os_extra = 'windows'
    host_arch = 'x86_64'
else:
    host_os_extra = os.uname().release

target_build_variant = os.environ.get("TARGET_BUILD_VARIANT")
build_top = os.environ.get("BUILD_TOP", "")
build_tools_dir = Path(build_top) / "build" / "make" / "tools"
build_core_dir = Path(build_top) / "build" / "make" / "core"
out_dir = Path(build_top) / "out"
target_device = os.environ.get("TARGET_DEVICE", "")
target_product_out = out_dir / "target" / "product" / target_device
target_obj = target_product_out / "obj"
target_system_out = target_product_out / "rootfs"
target_vendor_out = target_product_out / "vendor"  # should be mounted to /var/run/media/vendor in linux ramdisk
target_root_out = target_product_out / "rootfs"
target_recovery_out = target_product_out / "recovery"
bootable_obj = target_product_out / "obj" / "BOOTABLE_IMAGES"

os.environ.setdefault("TARGET_PRODUCT_OUT", str(target_product_out))
os.environ.setdefault("TARGET_SYSTEM_OUT", str(target_system_out))
os.environ.setdefault("TARGET_VENDOR_OUT", str(target_vendor_out))
os.environ.setdefault("TARGET_ROOT_OUT", str(target_root_out))
os.environ.setdefault("TARGET_RECOVERY_OUT", str(target_recovery_out))
os.environ.setdefault("OUT_DIR", str(out_dir))
os.environ.setdefault("TARGET_DEVICE", target_device)
os.environ.setdefault("BOOTABLE_OBJ", str(bootable_obj))
os.environ.setdefault("BUILD_TOOLS_DIR", str(build_tools_dir))
os.environ.setdefault("BUILD_CORE_DIR", str(build_core_dir))
os.environ.setdefault("HOST_ARCH", host_arch)
os.environ.setdefault("HOST_OS", host_os)
os.environ.setdefault("HOST_OS_EXTRA", host_os_extra)
os.environ.setdefault("TARGET_BUILD_VARIANT", target_build_variant)

if __name__ == "__main__":
    print(BUILD_ID)
