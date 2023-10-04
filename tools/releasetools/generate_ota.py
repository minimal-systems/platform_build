import os
import shutil
import zipfile

BUILD_TOP = os.environ.get("BUILD_TOP")
TARGET_PRODUCT_OUT = os.environ.get("TARGET_PRODUCT_OUT")
OUT_DIR = os.environ.get("OUT_DIR")
DEVICE_NAME = os.environ.get("TARGET_PRODUCT")

OTA_OBJ = f"{TARGET_PRODUCT_OUT}/obj/PACKAGING"
META_DIR = f"{OTA_OBJ}/META-INF/com/google/android"


def zip_directory(src_dir, dst_zip):
    zf = zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            abs_file = os.path.join(root, file)
            arcname = os.path.relpath(abs_file, src_dir)
            zf.write(abs_file, arcname)
    zf.close()


def copy_files():
    os.makedirs(META_DIR, exist_ok=True)
    file_names = ["update_binary", "updater_script.py", "system.img", "vendor.img", "recovery.img", "ramdisk.img", "boot.img"]
    for file_name in file_names:
        src_file = os.path.join(BUILD_TOP, "bootable", "recovery", "ota", "prebuilts", "bin", file_name) if file_name in ["update_binary", "updater_script.py"] else os.path.join(TARGET_PRODUCT_OUT, file_name)
        dst_file = os.path.join(OTA_OBJ, file_name)
        shutil.copy(src_file, dst_file)



def generate_ota_package():
    print("Generating OTA package...")
    copy_files()
    zip_directory(OTA_OBJ, f"{OUT_DIR}/soong/tmp/{DEVICE_NAME}.zip")
    os.system(
        f"signapk {OUT_DIR}/soong/tmp/{DEVICE_NAME}.zip -out {TARGET_PRODUCT_OUT}/{DEVICE_NAME}.zip"
    )


generate_ota_package()
