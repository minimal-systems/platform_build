#!/usr/bin/python
import glob
import shutil


target_recovery_out = os.environ.get ("TARGET_RECOVERY_OUT")
target_device = os.environ.get ("TARGET_DEVICE")
build_top = os.environ.get ("BUILD_TOP")


def install_recovery_init_scripts():
    for file in glob.glob(rf'{build_top}/device/{target_device}/rootdir/init.recovery.*.rc'):
        print(file)
        shutil.copy(f'file,{target_recovery_out}')
    for file in glob.glob(rf'{build_top}/bootable/recovery/rootdir/*.rc'):
        print(file)
        shutil.copy(f'file,{target_recovery_out}')


install_recovery_init_scripts()