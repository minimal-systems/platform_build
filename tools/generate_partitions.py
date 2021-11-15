#!/usr/bin/python

import tarfile
import os
import pwd
import shutil


def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]


user = get_username()
mkbootimg_header = os.environ.get("MKBOOTIMG_HEADER")

TARGET_PRODUCT_OUT = os.environ.get('TARGET_PRODUCT_OUT')
recovery_offset= os.environ.get('RECOVERY_IMAGE_OFFSET')


def generate_recovery_image():
    print('Target recovery fs image')
    print ('----- Making uncompressed recovery ramdisk ------')
    tar = tarfile.open(f'{TARGET_PRODUCT_OUT}/recovery-ramdisk.img', "w")
    tar.add(f'{TARGET_PRODUCT_OUT}/ramdisk', arcname="recovery-ramdisk")
    tar.close()
    print ('----- Making compressed recovery ramdisk ------')
    print (f'recovery image args (offset) {recovery_offset}')
    print (f'recovery image args(recovery header) {mkbootimg_header}')
    os.system(f'dd if=/dev/zero of={TARGET_PRODUCT_OUT}/recovery.img bs=32M count=1 status=none')
    os.makedirs(f'{TARGET_PRODUCT_OUT}/recovery_tmp', exist_ok=True)
    os.system(f'mkfs.ext4 {TARGET_PRODUCT_OUT}/recovery.img')
    os.system(f'sudo -E mount {TARGET_PRODUCT_OUT}/recovery.img {TARGET_PRODUCT_OUT}/recovery_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/recovery_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/recovery_tmp/*')
    shutil.copytree(f'{TARGET_PRODUCT_OUT}/recovery/root', f'{TARGET_PRODUCT_OUT}/recovery_tmp', dirs_exist_ok=True,  symlinks = False)
    os.system(f'sudo umount {TARGET_PRODUCT_OUT}/recovery_tmp')
    shutil.rmtree(f'{TARGET_PRODUCT_OUT}/recovery_tmp')
    

def generate_ramdisk_image():
    tar = tarfile.open(f'{TARGET_PRODUCT_OUT}/ramdisk.img', "w")
    tar.add(f'{TARGET_PRODUCT_OUT}/ramdisk', arcname="ramdisk")
    tar.close()


def generate_boot_image():
    print(f' "boot image args (boot header) {mkbootimg_header}')
    print('generating boot image...')
    os.system(f'dd if=/dev/zero of={TARGET_PRODUCT_OUT}/boot.img bs=24M count=1 status=none')
    os.makedirs(f'{TARGET_PRODUCT_OUT}/boot_tmp', exist_ok=True)
    os.system(f'mkfs.ext4 {TARGET_PRODUCT_OUT}/boot.img')
    os.system(f'sudo -E mount {TARGET_PRODUCT_OUT}/boot.img {TARGET_PRODUCT_OUT}/boot_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/boot_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/boot_tmp/*')
    shutil.copytree(f'{TARGET_PRODUCT_OUT}/root', f'{TARGET_PRODUCT_OUT}/boot_tmp', dirs_exist_ok=True,  symlinks = False)
    os.system(f'sudo umount {TARGET_PRODUCT_OUT}/boot_tmp')
    shutil.rmtree(f'{TARGET_PRODUCT_OUT}/boot_tmp')



def generate_system_image():
    print('generating system image...')
    os.system(f'dd if=/dev/zero of={TARGET_PRODUCT_OUT}/system.img bs=500M count=1 status=none')
    os.makedirs(f'{TARGET_PRODUCT_OUT}/system_tmp', exist_ok=True)
    os.system(f'mkfs.ext4 {TARGET_PRODUCT_OUT}/system.img')
    os.system(f'sudo -E mount {TARGET_PRODUCT_OUT}/system.img {TARGET_PRODUCT_OUT}/system_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/system_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/system_tmp/*')
    shutil.copytree(f'{TARGET_PRODUCT_OUT}/root', f'{TARGET_PRODUCT_OUT}/system_tmp', dirs_exist_ok=True,  symlinks = False)
    os.system(f'sudo umount {TARGET_PRODUCT_OUT}/system_tmp')
    shutil.rmtree(f'{TARGET_PRODUCT_OUT}/system_tmp')


def generate_vendor_image():
    print('generating vendor image...')
    os.system(f'dd if=/dev/zero of={TARGET_PRODUCT_OUT}/vendor.img bs=32M count=1 status=none')
    os.makedirs(f'{TARGET_PRODUCT_OUT}/vendor_tmp', exist_ok=True)
    os.system(f'mkfs.ext4 {TARGET_PRODUCT_OUT}/vendor.img')
    os.system(f'sudo -E mount {TARGET_PRODUCT_OUT}/vendor.img {TARGET_PRODUCT_OUT}/vendor_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/vendor_tmp')
    os.system(f'sudo chown {user} {TARGET_PRODUCT_OUT}/vendor_tmp/*')
    shutil.copytree(f'{TARGET_PRODUCT_OUT}/root', f'{TARGET_PRODUCT_OUT}/vendor_tmp', dirs_exist_ok=True,  symlinks = False)
    os.system(f'sudo umount {TARGET_PRODUCT_OUT}/vendor_tmp')
    shutil.rmtree(f'{TARGET_PRODUCT_OUT}/vendor_tmp')


generate_recovery_image()
generate_ramdisk_image()
generate_boot_image()
generate_vendor_image()
generate_system_image()
