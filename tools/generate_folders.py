import os
import sys
build_top = os.environ.get("BUILD_TOP")
sys.path.append(f"{build_top}/build/make/core")
from envsetup import *
target_recovery_out = os.environ.get("TARGET_RECOVERY_OUT")
target_root_out = os.environ.get("TARGET_ROOT_OUT")

def generate_recovery_folders():
    recovery_folder_list = ["dev", "firmware", "mnt", "etc", "persist", "sbin", "proc", "sys"]
    [os.makedirs(f"{target_recovery_out}/{item}", exist_ok=True) for item in recovery_folder_list]

def generate_root_folders():
    root_folder_list = [
        "lib", "bin", "lib64", "dev", "firmware", "proc", "persist", "mnt", "sys", "acct", "cache", "sbin",
        "config", "postinstall", "usr", "xbin"
    ]
    root_extra_folders = os.environ.get("ROOT_EXTRA_FOLDERS", "").split(",")
    folder_list = root_folder_list + root_extra_folders
    [os.makedirs(f"{target_root_out}/{item}", exist_ok=True) for item in folder_list]

generate_recovery_folders()
generate_root_folders()
