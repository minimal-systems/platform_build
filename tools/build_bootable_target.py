#!/usr/bin/env python

import subprocess
import os
import shutil
import sys
import glob
import platform
import logging


# disable creation of __pycache__
sys.dont_write_bytecode = True

log = "out/build.log"
logging.basicConfig(
    filename=log,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
arch = platform.processor()
ccache = shutil.which("ccache")

build_top = os.environ.get("BUILD_TOP")
sys.path.append(f"{build_top}/build/make/core")
from envsetup import *

sys.path.insert(1, sys.argv[1])
from module_info import *

class color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


bootable_obj = f"{target_product_out}/obj/BOOTABLE_IMAGES"
obj_include = f"{bootable_obj}/{local_module}/include"
# default_cflags
default_cflags = f"-fdiagnostics-color=always -pipe -D_FILE_OFFSET_BITS=64 -Winvalid-pch -Wnon-virtual-dtor {cpp_flags}"
obj = f"{bootable_obj}/{local_module}"
# use clang for bootloaders
compiler = "prebuilts/clang/bin/clang"
compiler_name = "clang"
local_objs = ""

installed_bootable_target = f"{target_product_out}/{target_device}_{local_module}.bin"

if type(local_src_files) is str:
  local_src_files = (local_src_files,)


obj_o = []

for src_o in local_src_files:
    obj_o.append(f"{obj}/{local_path}/{src_o}.o")
    compiled_obj = " ".join(obj_o)

def build_target():
    shutil.rmtree(f"{bootable_obj}/{local_module}", ignore_errors=True)
    os.makedirs(f"{bootable_obj}/{local_module}", exist_ok=True)
    subprocess.call(f"{build_top}/{local_path}/scripts/gen_conf", shell=True)
    shutil.copytree(
        f"{build_top}/{local_path}/include",
        f"{bootable_obj}/{local_module}/include",
        dirs_exist_ok=True,
    )
    os.makedirs(f"{obj}/LINKED", exist_ok=True)
    rootdir = f"{local_path}"
    for path in glob.glob(f"{rootdir}/*/**/", recursive=True):
        os.makedirs(f"{bootable_obj}/{local_module}/{path}", exist_ok=True)
    for src in local_src_files:
        os.system(
            f"{ccache} {compiler} -I{local_c_includes} {default_cflags} -g -MD -MQ {obj}/{local_path}/{src}.o -MF {obj}/{local_path}/{src}.o.d -o {obj}/{local_path}/{src}.o -c {build_top}/{local_path}/{src}"
        )
        print(
            color.BOLD
            + f"//{local_path}:{local_module} {compiler_name} {src}"
            + color.END,
        )
        logging.info(f"//{local_path}:{local_module} {compiler_name} {src}")

    if platform.system() == 'Darwin' :
        os.system(
            f"{ccache} {compiler} -o {obj}/LINKED/{local_module} {compiled_obj} -Wl {ld_flags}"
        )
    else:
        os.system(f"{compiler} -o {obj}/LINKED/{local_module} {compiled_obj} -Wl,--as-needed {ld_flags} -Wl,--no-undefined")
    if platform.system() == 'Darwin' :
            os.system(
        f"{ccache} {compiler} -o {target_product_out}/{target_device}_{local_module}.bin {compiled_obj}  -Wl {ld_flags}")
    else:
        os.system(f"{ccache} {compiler} -o {target_product_out}/{target_device}_{local_module}.bin {compiled_obj}  -Wl,--as-needed {ld_flags} -Wl,--no-undefined")


build_target()
