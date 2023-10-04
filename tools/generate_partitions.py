import tarfile
import os
import pwd
import shutil


def get_username():
    return pwd.getpwuid(os.getuid())[0]


user = get_username()
mkbootimg_header = os.environ.get("MKBOOTIMG_HEADER")

TARGET_PRODUCT_OUT = os.environ.get("TARGET_PRODUCT_OUT")
recovery_offset = os.environ.get("RECOVERY_IMAGE_OFFSET")


import os
import shutil
import subprocess

import os
import shutil
import subprocess

def generate_image(img_file, img_size, img_mount, img_name, user, target_product_out):
    # Define the paths for the input and output directories
    images_dir = os.path.join(target_product_out, "OBJ/ota_packaging_indetermdates/IMAGES")
    temp_dir = os.path.join(target_product_out, "out/soong/tmp")
    os.makedirs(temp_dir, exist_ok=True)

    # Copy the image files to the temporary directory
    img_file_path = os.path.join(images_dir, img_file)
    img_name_path = os.path.join(images_dir, img_name)
    temp_img_file_path = os.path.join(temp_dir, img_file)
    temp_img_mount_path = os.path.join(temp_dir, img_mount)
    shutil.copyfile(img_file_path, temp_img_file_path)
    shutil.copytree(img_name_path, temp_img_mount_path, dirs_exist_ok=True)

    print(f"generating {img_name} image...")
    try:
        # Create an LVM partition and mount it
        subprocess.run(["lvcreate", f"-L{img_size}", "-n", img_file, "vg0"], check=True)
        subprocess.run(["mkfs.ext4", f"/dev/vg0/{img_file}"], check=True)
        os.makedirs(os.path.join(target_product_out, img_mount), exist_ok=True)
        subprocess.run(["mount", f"/dev/vg0/{img_file}", os.path.join(target_product_out, img_mount)], check=True)

        # Copy the image files to the partition
        subprocess.run(["cp", "-a", os.path.join(temp_img_mount_path, "."), os.path.join(target_product_out, img_mount)], check=True)

        # Set the ownership of the files
        subprocess.run(["chown", "-R", user, os.path.join(target_product_out, img_mount)], check=True)

    finally:
        # Unmount the partition and clean up
        subprocess.run(["umount", os.path.join(target_product_out, img_mount)], check=False)
        subprocess.run(["lvremove", "-f", f"vg0/{img_file}"], check=False)
        shutil.rmtree(temp_dir)

    # Move the image files back to the original directory
    shutil.move(temp_img_file_path, img_file_path)
    shutil.move(temp_img_mount_path, img_name_path)


def generate_images():
    # Generate recovery image
    print("Target recovery fs image")
    print("----- Making uncompressed recovery ramdisk ------")
    tar = tarfile.open(f"{TARGET_PRODUCT_OUT}/recovery-ramdisk.tar.gz", "w")
    tar.add(f"{TARGET_PRODUCT_OUT}/ramdisk", arcname="recovery-ramdisk")
    tar.close()
    print("----- Making compressed recovery ramdisk ------")
    print(f"recovery image args (offset) {recovery_offset}")
    print(f"recovery image args(recovery header) {mkbootimg_header}")
    generate_image("recovery.img", "32M", "recovery_tmp", "recovery/root")

    # Generate ramdisk image
    tar = tarfile.open(f"{TARGET_PRODUCT_OUT}/ramdisk.img", "w")
    tar.add(f"{TARGET_PRODUCT_OUT}/ramdisk", arcname="ramdisk")
    tar.close()

    # Generate boot image
    print(f'boot image args (boot header) {mkbootimg_header}')
    print("generating boot image...")
    generate_image("boot.img", "24M", "boot", "root")

    # Generate vendor image
    generate_image("vendor.img", "32M", "boot", "vendor")

    # Generate rootfs image
    generate_image("rootfs.img", "8096M", "boot", "root")
    

generate_images()
