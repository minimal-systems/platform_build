import os
import subprocess

"""
/boot – Highly recommended. Use this partition to store kernels and other booting information. To minimize potential boot problems with larger disks, make this the first physical partition on your first disk drive. A partition size of 200 megabytes is quite adequate.

/home – Highly recommended. Share your home directory and user customization across multiple distributions or LFS builds. The size is generally fairly large and depends on available disk space.

/EFI  - Highly recommended. The EFI partition is used to store the EFI boot loader and related files. The size is generally fairly small and depends on available disk space.

/usr – In LFS, /bin, /lib, and /sbin are symlinks to their counterpart in /usr. So /usr contains all binaries needed for the system to run. For LFS a separate partition for /usr is normally not needed. If you need it anyway, you should make a partition large enough to fit all programs and libraries in the system. The root partition can be very small (maybe just one gigabyte) in this configuration, so it's suitable for a thin client or diskless workstation (where /usr is mounted from a remote server). However you should take care that an initramfs (not covered by LFS) will be needed to boot a system with separate /usr partition.

/opt – This directory is most useful for BLFS where multiple installations of large packages like Gnome or KDE can be installed without embedding the files in the /usr hierarchy. If used, 5 to 10 gigabytes is generally adequate.

/tmp – A separate /tmp directory is rare, but useful if configuring a thin client. This partition, if used, will usually not need to exceed a couple of gigabytes.

/usr/src – This partition is very useful for providing a location to store BLFS source files and share them across LFS builds. It can also be used as a location for building BLFS packages. A reasonably large partition of 30-50 

 ext4

    is the latest version of the ext file system family of partition types. It provides several new capabilities including nano-second timestamps, creation and use of very large files (16 TB), and speed improvements.

"""



def make_uncompressed_recovery_ramdisk():
    print("----- Making uncompressed recovery ramdisk -----")
    subprocess.run([f"{BUILD_TOP}/build/tools/bin/mkbootfs", f"{TARGET_PRODUCT_OUT}/ramdisk/"],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(f"{TARGET_PRODUCT_OUT}/recovery-ramdisk.cpio", "w") as cpio_file:
        cpio_file.write(subprocess.check_output([f"{BUILD_TOP}/build/tools/bin/mkbootfs", f"{TARGET_PRODUCT_OUT}/ramdisk/"]).decode())

def make_compressed_recovery_ramdisk():
    print("----- Making compressed recovery ramdisk -----")
    uncompressed_cpio = open(f"{TARGET_PRODUCT_OUT}/recovery-ramdisk.cpio", "rb").read()
    compressed_cpio = subprocess.check_output(["lz4", "-l", "-12", "--favor-decSpeed"], input=uncompressed_cpio)
    with open(f"{TARGET_PRODUCT_OUT}/recovery-ramdisk.img", "wb") as img_file:
        img_file.write(compressed_cpio)

def generate_image():
    print("generating recovery image...")
    print(f"recovery image args (offset) {BOOT_IMAGE_OFFSET}")
    print(f"recovery image args (ramdisk version) {BSP_VERSION}")
    print(f"recovery image args (table offset) {DTB_TABLE_OFFSET}")
    print(f"recovery image args (boot header) {MKBOOTIMG_HEADER}")
    subprocess.run([f"{BUILD_TOP}/build/tools/bin/mkbootimg",
                    "--kernel", KERNEL_IMG,
                    "--ramdisk", f"{TARGET_PRODUCT_OUT}/recovery-ramdisk.img",
                    "--cmdline", BOOT_CMDLINE,
                    "--base", BOOT_BASE,
                    "--pagesize", BOOT_PAGESIZE,
                    "--os_version", BOOT_OS_VERSION,
                    "--os_patch_level", BOOT_OS_PATCH_LEVEL,
                    "--kernel_offset", KERNEL_OFFSET,
                    "--ramdisk_offset", RAMDISK_OFFSET,
                    "--second_offset", SECOND_OFFSET,
                    "--tags_offset", TAGS_OFFSET,
                    "--output", INSTALLED_RECOVERYIMAGE_TARGET])
    os.makedirs(os.path.dirname(INSTALLED_RECOVERYIMAGE_TARGET), exist_ok=True)
    subprocess.run(["cp", f"{TARGET_PRODUCT_OUT}/recovery.img", f"{TARGET_SYSTEM_OUT}/recovery.img"])
    with open(f"{TARGET_PRODUCT_OUT}/recovery.$(IMG_END)", "w") as md5sum_file:
        subprocess.run(["md5sum", "recovery.$(IMG_END)"], cwd=TARGET_PRODUCT_OUT, stdout=md5sum_file)
    print(f"Target recovery image: {INSTALLED_RECOVERYIMAGE_TARGET}")

def make_installed_gpt_image():
    if TARGET_BUILD_GPT:
        print(f"Target gpt fs image: {INSTALLED_GPT_IMAGE_TARGET}")
        os.makedirs(os.path.dirname(INSTALLED_GPT_IMAGE_TARGET), exist_ok=True)
        with open(INSTALLED_GPT_IMAGE_TARGET, "wb") as gpt_image:
            for target in [INSTALLED_RAMDISK_TARGET, INSTALLED_RECOVERYIMAGE_TARGET]:
                with open(target, "rb") as source_file:
                    gpt_image.write(source_file.read())

def build_uncompressed_ramdisk():
    print("--build uncompressed ramdisk--")
    subprocess.run([f"{BUILD_TOP}/build/tools/bin/mkbootfs", f"{TARGET_PRODUCT_OUT}/ramdisk/"],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(f"{TARGET_PRODUCT_OUT}/ramdisk.cpio", "w") as cpio_file:
        cpio_file.write(subprocess.check_output([f"{BUILD_TOP}/build/tools/bin/mkbootfs", f"{TARGET_PRODUCT_OUT}/ramdisk/"]).decode())
    print(f"generated {TARGET_PRODUCT_OUT}/ramdisk.cpio")

# Define other functions and targets similarly



def generate_image_info_rules(image_type):
	info_target = f'{target_product_out}/obj/PACKAGING/{image_type}__intermediates/{image_type}_image_info.txt'
		with open(info_target, 'w') as f:
			f.write(f"{image_type}_fs_type=ext4\n")
			f.write(f"{image_type}_size={board_vendorimage_partition_size}\n")
			f.write(f"{image_type}_selinux_fc={target_product_out}/obj/ETC/file_contexts.bin_intermediates/file_contexts.bin\n")
			f.write(f'building_{image_type}_image=true\n')
			f.write(f'ext_mkuserimg=mkuserimg_mke2fs\n')
			f.write("fs_type=ext4\n")
			f.write("extfs_sparse_flag=-s\n")
			f.write("erofs_sparse_flag=-s\n")
			f.write("squashfs_sparse_flag=-s\n")
			f.write("f2fs_sparse_flag=-S\n")
			f.write("avb_avbtool=avbtool\n")
			f.write("avb_system_hashtree_enable=false\n")
			f.write("avb_system_add_hashtree_footer_args=\n")
			f.write("avb_system_other_hashtree_enable=false\n")
			f.write("avb_system_other_add_hashtree_footer_args=\n")
			f.write("avb_vendor_hashtree_enable=false\n")
			f.write("avb_vendor_add_hashtree_footer_args=\n")
			f.write("avb_product_hashtree_enable=false\n")
			f.write("avb_product_add_hashtree_footer_args=\n")
			f.write("avb_system_ext_hashtree_enable=false\n")
			f.write("avb_system_ext_add_hashtree_footer_args=\n")
			f.write("avb_odm_hashtree_enable=false\n")
			f.write("avb_odm_add_hashtree_footer_args=\n")
			f.write("avb_vendor_dlkm_hashtree_enable=false\n")
			f.write("avb_vendor_dlkm_add_hashtree_footer_args=\n")
			f.write("avb_odm_dlkm_hashtree_enable=false\n")
			f.write("avb_odm_dlkm_add_hashtree_footer_args=\n")
			f.write("avb_system_dlkm_hashtree_enable=false\n")
			f.write("avb_system_dlkm_add_hashtree_footer_args=\n")
			f.write("root_dir=$(TARGET_PRODUCT_OUT)/root\n")
			f.write("skip_fsck=true\n")


def build_image(part)
	print(f'{part} image args (offset) {img_offset}')
	print(f'{part} image args (OS version) {platform_version}')
	print(f'{part} image args (DTB OFFSET)  {dtb_table_offset}')
	os.system(f'{build_top}/build/tools/bin/build_image {part} \ 
    	{info_target}/{part}_image_info.txt {part_dir}/{part}.img \
        {target_system_out}
        
        
        
def gen_img(part):
	generate_image_info_rules(part)
	build_image(part)
 
if __name__ == "__main__":
    # Define your main build logic here
    make_uncompressed_recovery_ramdisk()
    make_compressed_recovery_ramdisk()
    generate_recovery_image()
    make_installed_gpt_image()
    build_uncompressed_ramdisk()
    # Add more build steps as needed

