#!/usr/bin/env python

import os
import platform
import sys
from pathlib import Path
from build_id import *
from build_config import *
from ccache import *
from definitions import *
# disable creation of __pycache__
sys.dont_write_bytecode = True

host_os = platform.system().lower()
host_arch = platform.machine()
if os.name == 'nt':
    host_os = 'windows'
    host_os_extra = 'windows'
    host_arch = 'x86_64'
else:
    uname_info = os.uname()
    host_os_extra = f"{uname_info.sysname} {uname_info.release} {uname_info.machine}"

# Map platform.system() values to Android build host names
if host_os == "linux":
    host_os = "linux-x86"
elif host_os == "darwin":
    host_os = "darwin-x86"
elif host_os == "windows":
    host_os = "windows-x86"

# Ensure architecture compatibility with AOSP build system expectations
if host_arch == "x86_64":
    host_arch = "x86_64"
else:
    # Default to x86_64 for unknown architectures
    host_arch = "x86_64"

target_build_variant = os.environ.get("TARGET_BUILD_VARIANT")
build_top = os.environ.get("BUILD_TOP", "")
build_tools_dir = Path(build_top) / "build" / "make" / "tools"
build_core_dir = Path(build_top) / "build" / "make" / "core"
out_dir = Path(build_top) / "out"
target_device = os.environ.get("TARGET_DEVICE", "")
target_product_out = out_dir / "target" / "product" / target_device
target_obj = target_product_out / "obj"
target_system_out = target_product_out / "rootfs"
target_oem_out = target_product_out / "oem"
target_vendor_out = target_product_out / "rootfs" / "usr"
target_container_out = target_product_out / "containers"
target_copy_out_system = target_system_out
target_copy_out_vendor = target_vendor_out
target_copy_out_containers = target_container_out
target_root_out = target_product_out / "root"
target_boot_out = target_product_out / "boot"
target_containers_out = target_product_out / "containers"
target_container_data_out = target_product_out / "container-data"
target_recovery_out = target_product_out / "recovery" / "root"
target_copy_out_recovery = target_recovery_out
target_kernel_out = target_product_out / "obj" / "KERNEL_OBJ"
target_vendor_out_etc = target_vendor_out / "etc"
target_system_out_etc = target_system_out / "etc"
target_recovery_out_etc = target_recovery_out / "etc"
target_ramdisk_out = target_product_out / "ramdisk"
target_vendor_out_bin = target_vendor_out / "bin"
target_system_out_bin = target_system_out / "bin"
target_vendor_out_lib = target_vendor_out / "lib"
target_system_out_lib = target_system_out / "lib"
target_system_out_lib64 = target_system_out / "lib64"
target_vendor_out_lib64 = target_vendor_out / "lib64"
target_recovery_out_usr_bin = target_recovery_out / "usr" / "bin"
target_shared_libs_obj = target_obj / "SHARED_LIBRARIES"
target_executables_obj = target_obj / "EXECUTABLES"
target_static_libs_obj = target_obj / "STATIC_LIBRARIES"
target_kernel_out = target_obj / "KERNEL_OBJ"
target_etc_obj = target_obj / "ETC"
product_out = target_product_out
soong_out_dir = out_dir / "soong"
host_out_executables = os.path.join(out_dir, "host", f"{host_os}-{host_arch}", "bin")
# compiler variables
clang = "clang"
clangxx = "clang++"

os.environ.setdefault("TARGET_PRODUCT_OUT", str(target_product_out))
os.environ.setdefault("TARGET_SYSTEM_OUT", str(target_system_out))
os.environ.setdefault("TARGET_VENDOR_OUT", str(target_vendor_out))
os.environ.setdefault("TARGET_ROOT_OUT", str(target_root_out))
os.environ.setdefault("TARGET_RECOVERY_OUT", str(target_recovery_out))
os.environ.setdefault("TARGET_KERNEL_OUT", str(target_kernel_out))
os.environ.setdefault("TARGET_VENDOR_OUT_ETC", str(target_vendor_out_etc))
os.environ.setdefault("TARGET_SYSTEM_OUT_ETC", str(target_system_out_etc))
os.environ.setdefault("TARGET_RECOVERY_OUT_ETC", str(target_recovery_out_etc))
os.environ.setdefault("TARGET_RAMDISK_OUT", str(target_ramdisk_out))
os.environ.setdefault("OUT_DIR", str(out_dir))
os.environ.setdefault("TARGET_DEVICE", target_device)
os.environ.setdefault("BUILD_TOOLS_DIR", str(build_tools_dir))
os.environ.setdefault("BUILD_CORE_DIR", str(build_core_dir))
os.environ.setdefault("HOST_ARCH", host_arch)
os.environ.setdefault("HOST_OS", host_os)
os.environ.setdefault("HOST_OS_EXTRA", host_os_extra)
os.environ.setdefault("TARGET_BUILD_VARIANT", target_build_variant)


from select_arch import *
