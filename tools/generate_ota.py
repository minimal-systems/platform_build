#!/usr/bin/python

import os
import shutil
import zipfile
TARGET_PRODUCT_OUT = os.environ.get("TARGET_PRODUCT_OUT")
OUT_DIR = os.environ.get("OUT_DIR")
device_name = os.environ.get("TARGET_PRODUCT")
BUILD_TOP = os.environ.get("BUILD_TOP")
ota_obj = TARGET_PRODUCT_OUT + '/obj/PACKAGING'
meta_dir = ota_obj + '/META-INF/com/google/android'


def zip(src, dst):
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            zf.write(absname, arcname)
    zf.close()


def generate_ota_package():
    print("Generating ota package...")
    os.makedirs(meta_dir, exist_ok=True)
    shutil.copy(
        f'{BUILD_TOP}/bootable/recovery/ota/prebuilts/bin/update_binary', meta_dir)
    shutil.copy(f'{TARGET_PRODUCT_OUT}/system.img',ota_obj)
    shutil.copy(f'{TARGET_PRODUCT_OUT}/vendor.img',ota_obj)
    shutil.copy(f'{TARGET_PRODUCT_OUT}/recovery.img',ota_obj)
    shutil.copy(f'{TARGET_PRODUCT_OUT}/ramdisk.img',ota_obj)
    shutil.copy(f'{TARGET_PRODUCT_OUT}/boot.img',ota_obj)
    zip(f'{TARGET_PRODUCT_OUT}/obj/PACKAGING',
        f'{OUT_DIR}/soong/tmp/{device_name}')
    os.system(
        f'signapk {OUT_DIR}/soong/tmp/{device_name}.zip -out {TARGET_PRODUCT_OUT}{device_name}.zip')
    shutil.copy(f'{OUT_DIR}/soong/tmp/{device_name}-signed.zip',
                f'{TARGET_PRODUCT_OUT}/{device_name}.zip')


generate_ota_package()
