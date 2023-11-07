#!/usr/bin/env python
import os
import glob
import shutil
import sys
import platform
import subprocess
from colorama import *

# TODO: transition to LFS linux from scratch build system

build_top = os.environ.get("BUILD_TOP")
sys.path.append(f"{build_top}/build/make/core")
from envsetup import *

#default values 
local_proprietary_module = False
local_cpp_clang = False
override_exec_path = False
local_cpp_flags = ''
local_src_files = ''
local_c_includes = ''
ld_flags = ''


sys.path.insert(1, sys.argv[1])
from module_info import *

# disable creation of __pycache__
sys.dont_write_bytecode = True

target_recovery_out = os.environ.get("TARGET_RECOVERY_OUT")
target_product_out = os.environ.get("TARGET_PRODUCT_OUT")
target_vendor_out = os.environ.get("TARGET_VENDOR_OUT")
target_system_out = os.environ.get("TARGET_SYSTEM_OUT")



obj = f"{target_product_out}/obj/EXECUTABLES/{local_module}_indeterminates"
recovery_obj = (
    f"{target_product_out}/obj/EXECUTABLES/{local_module}_recovery_indeterminates"
)
default_local_c_includes = "."
local_shared_libs = ""


#default flags for compiling
default_cpp_flags = "-fdiagnostics-color=always -pipe -D_FILE_OFFSET_BITS=64"
additional_cpp_flags = f'{local_cpp_flags}'
ld_flags =  ''

default_strip_flags = [
    "-S",
    "--strip-unneeded",
    "--remove-section=.note.gnu.gold-version",
    "--remove-section=.comment",
    "--remove-section=.note",
    "--remove-section=.note.gnu.build.id",
    "--remove-section=.not.ABI-tag",
]
ccache = '/usr/bin/ccache'
compiler = '/usr/bin/clang'  # Add the missing single quote

# set up the compilers and the compiler name
cc = f"{ccache} {compiler}"
ccpp = f"{ccache} {compiler}++"

compiler_name = "clang"


if local_proprietary_module == True:
    if override_exec_path == True:
        install_exec_path = f"{install_path}"
    else:
        install_exec_path = f"{target_system_out}/opt/bin"
else:
    if override_exec_path == True:
        install_exec_path = f"{install_path}"
    else:
        install_exec_path = f"{target_system_out}/bin"



obj_o = []
for src_o in local_src_files:
    obj_o.append(f"{obj}/{local_path}/{src_o}.o")
    compiled_obj = " ".join(obj_o)

strip_flags = []
for strip_flags in default_strip_flags:
    strip_flags = " ".join(default_strip_flags)


includes_files = []
for include_dir in local_c_includes:
    includes_files.append(f'-I{include_dir}')
    includes_clean = " ".join(includes_files)

installed_exectutable_target =f'{install_exec_path}/{local_module}'
install_recovery_exec_path = f'{target_recovery_out}/sbin'

def warn_deprecation():
    print(
        color.RED
        + f"//{local_path}:{local_module} is using deprecated build system"
        + color.END
    )

def build_target():
    # remove old object directory and create new one
    shutil.rmtree(f"{obj}", ignore_errors=True)
    os.makedirs(f"{obj}", exist_ok=True)
    os.makedirs(f"{obj}/LINKED", exist_ok=True)

    # create object directory structure
    rootdir = f"{local_path}"
    for path in glob.glob(f"{rootdir}/*/**/", recursive=True):
        os.makedirs(f"{obj}/{path}", exist_ok=True)
    os.makedirs(f'{obj}/{local_path}', exist_ok=True)

    # set up ld flags to link shared libraries
    ld_flags = ''
    lib_dir = f'{target_product_out}/OBJ/SHARED_LIBRARIES'
    for lib in local_shared_libs:
        lib_name = lib.split(':')[0]
        lib_path = os.path.join(lib_dir, f'{lib_name}_indeterminates/linked')
        lib_file = os.path.join(lib_path, f'{lib_name}.so')
        if os.path.exists(lib_file):
            ld_flags += f' -L{lib_path} -l{lib_name}'

    # create necessary directories
    os.makedirs(f"{obj}/LINKED", exist_ok=True)
    for src in local_src_files:
        os.makedirs(f"{obj}/{os.path.dirname(src)}", exist_ok=True)

    # compile source files
    object_files = []
    for src in local_src_files:
        if src.endswith('.cpp'):
            cc_command = [ccache, f"{compiler}++"]
            compiler_name = "clang++"
        else:
            cc_command = [ccache, compiler]
            compiler_name = "clang"

        src_base = os.path.splitext(src)[0]
        obj_file = f"{obj}/{src_base}.o"
        object_files.append(obj_file)
        cmd_compile = cc_command + includes_clean.split() + default_cpp_flags.split() + additional_cpp_flags.split() + ["-g", "-MD", "-MQ", obj_file, "-MF", f"{obj_file}.d", "-c", f"{build_top}/{local_path}/{src}", "-o", obj_file]
        print(f'\r//{local_path}:{chr(27)}[1m{local_module}{chr(27)}[0m {compiler_name} {src}', end='', flush=True)
        subprocess.run(cmd_compile)

    # link object files
    cmd_link = [cc_command[1], "-o", f"{obj}/LINKED/{local_module}"] + object_files
    if platform.system() == 'Darwin':
        cmd_link += ["-Wl", f"{ld_flags}"]
    else:
        cmd_link += ["-Wl,--as-needed"] + ld_flags.split() + ["-Wl,--no-undefined"]
    subprocess.run(cmd_link)

    # copy linked executable to installation path
    shutil.copyfile(f'{obj}/LINKED/{local_module}', f'{installed_exectutable_target}')

    # print success message
    print(f'\n[ {Fore.GREEN} SUCCESS {Style.RESET_ALL} ] Compiled and installed {local_module} to {installed_exectutable_target}')


build_target()
