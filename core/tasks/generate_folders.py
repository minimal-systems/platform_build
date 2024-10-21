import os
import shutil
import subprocess
from envsetup import *
from build_logger import *
from device_info import rootfs_extra_folders

log_tag = "generate_folders"

# Function to get the kernel version (uname -r)
def get_kernel_version():
    """
    Retrieves the current kernel version by executing the 'uname -r' command.
    
    Returns:
        str: The kernel version as a string. If the command fails, returns 'unknown'.
    """
    try:
        return subprocess.check_output(["uname", "-r"]).decode().strip()
    except subprocess.CalledProcessError:
        pr_error("Unable to get kernel version", log_tag)
        return "unknown"  # fallback in case uname fails

# Get the kernel version dynamically
kernel_version = get_kernel_version()

# Define the folder structures with symlinks
folder_structures = {
    'root': [
        ('bin', 'usr/bin', True),  # bin is a symlink pointing to usr/bin
        ('boot', None, False),  # boot directory for storing bootloader and related files
        ('dev', None, False),  # dev for device files
        ('etc', None, False),  # etc for system configuration files
        ('home', None, False),  # home for user directories
        ('lib', 'usr/lib', True),  # lib is a symlink pointing to usr/lib
        ('lib64', 'usr/lib', True),  # lib64 is a symlink pointing to usr/lib
        ('mnt', None, False),  # mnt is used for mounting filesystems
        ('opt', None, False),  # opt for optional software packages
        ('proc', None, False),  # proc for kernel and process information
        ('root', None, False),  # root user home directory
        ('run', None, False),  # run for runtime variable data
        ('sbin', 'usr/bin', True),  # sbin is a symlink pointing to usr/bin
        ('srv', None, False),  # srv for service data
        ('sys', None, False),  # sys for system information
        ('tmp', None, False),  # tmp for temporary files
        ('usr', None, False),  # usr for user programs and data
        ('var', 'run', True)  # var is now a symlink to run
    ],
    'rootfs': [
        ('bin', 'usr/bin', True),  # bin is a symlink pointing to usr/bin
        ('containers', None, False),  # containers directory for container files
        ('etc', None, False),  # etc for configuration specific to rootfs
        ('lib', 'usr/lib', True),  # lib is a symlink pointing to usr/lib
        ('lib64', 'usr/lib', True),  # lib64 is a symlink pointing to usr/lib
        ('sbin', 'usr/bin', True),  # sbin is a symlink pointing to usr/bin
        ('usr', None, False),  # usr directory inside rootfs
        ('var', 'run', True),  # var is now a symlink to run
        ('firmware', None, False)  # firmware for device firmware files
    ],
    'rootfs_usr': [
        ('bin', None, False),  # bin directory for binary executables
        ('include', None, False),  # include for C/C++ header files
        ('lib', None, False),  # lib for essential libraries
        ('lib32', None, False),  # lib32 for 32-bit libraries
        ('lib64', 'lib', True),  # lib64 is a symlink to lib
        ('local', None, False),  # local for site-specific programs
        ('sbin', 'bin', True),  # sbin is a symlink to bin
        ('share', None, False),  # share for architecture-independent data
        ('src', None, False)  # src for source files
    ],
    'recovery': [
        ('bin', 'usr/bin', True),  # bin is a symlink pointing to usr/bin
        ('containers', None, False),  # containers directory for recovery
        ('etc', None, False),  # etc for recovery-specific configuration
        ('lib', 'usr/lib', True),  # lib is a symlink pointing to usr/lib
        ('lib64', 'usr/lib', True),  # lib64 is a symlink pointing to usr/lib
        ('sbin', 'usr/bin', True),  # sbin is a symlink pointing to usr/bin
        ('usr', None, False),  # usr directory inside recovery
        ('var', 'run', True)  # var is now a symlink to run
    ],
    'oem': [
        ('bin', None, False),  # bin directory for OEM-specific binaries
        ('etc', None, False),  # etc for OEM configuration
        ('lib', None, False),  # lib for OEM-specific libraries
        ('lib64', None, False),  # lib64 for OEM-specific 64-bit libraries
        ('sbin', None, False),  # sbin for OEM-specific system binaries
        ('var', None, False),  # var for OEM-specific variable data
        ('modules', None, False),  # modules for OEM-specific kernel modules
        ('firmware', None, False),  # firmware for OEM-specific firmware
        ('keys', None, False),  # keys for OEM-specific purposes
        ('manufacturer', None, False),  # manufacturer information
        ('wifi', None, False),  # WLAN configuration
        ('carrier', None, False),  # Carrier-specific configuration
        ('touch', None, False)  # Touch firmware configuration
    ],
    'boot': [
        ('efi/EFI/BOOT', None, False),  # EFI boot directory for UEFI systems
        ('efi/EFI/minimal_systems', None, False),  # Vendor-specific EFI directory
        ('grub2/fonts', None, False),  # Fonts used by GRUB2 bootloader
        ('grub2', None, False),  # GRUB2 bootloader configuration
        ('loader/entries', None, False),  # Bootloader entries for systemd-boot
    ],
    'containers_data': [
        ('data', None, False),  # Contains the actual container data or container layers
        ('overlay', None, False),  # Overlay filesystem directory for upper and lower layers
        ('overlay/lower', None, False),  # Lower directory for read-only layers
        ('overlay/upper', None, False),  # Upper directory for read-write layers
        ('overlay/work', None, False),  # Work directory used by overlayfs
        ('overlay/merged', None, False),  # Merged view of the upper and lower layers
        ('config', None, False),  # Configuration files for containers
        ('logs', None, False),  # Logs directory for container logs
        ('runtimes', None, False),  # Runtimes for containers (e.g., runc)
        ('network', None, False),  # Networking configurations for containers
        ('volumes', None, False),  # Volumes for persistent storage
        ('secrets', None, False),  # Secrets mounted inside containers
        ('tmp', None, False),  # Temporary files for containers
        ('hooks', None, False),  # Hooks for custom behavior (e.g., pre-start, post-stop)
        ('snapshots', None, False),  # Snapshots of container states
        ('runtime', None, False)  # Contains runtime-specific directories (cgroups, etc.)
    ],
}

# Extra categorized folders including kernel module directory
extra_folders = {
    'wlan': [
        "etc/wifi",
    ],
    'carrier': [
        "etc/carrier",
        "usr/share/carrier"
    ],
    'firmware': [
        "firmware",
        "firmware-update",
        "firmware/touch",
        "firmware/wlan",
        "firmware/carrier",
        "firmware/audio",
        "firmware/wifi",
        "firmware/bt",
        "firmware/nfc",
        "firmware/fmradio",
        "firmware/camera",
        "firmware/display",
        "firmware/media",
        "firmware/leds",
        "firmware/battery",
        "firmware/vibrator",
        "firmware/fingerprint",
        "firmware/biometrics",
        "firmware/usb"
    ],
    'touch_firmware': [
        "etc/touch",
        "usr/share/touch",
    ],
    'linux_etc': [
        "etc/init.d",
        "etc/network",
        "etc/cron.d",
        "etc/cron.daily",
        "etc/cron.hourly",
        "etc/cron.monthly",
        "etc/cron.weekly",
        "etc/default",
        "etc/skel",
        "etc/apt",
        "etc/bash_completion.d",
        "etc/xdg",
        "etc/logrotate.d",
        "etc/ssh",
        "etc/systemd",
        "etc/sysctl.d",
        "etc/udev",
        "etc/profile.d",
        "etc/ssl"
    ],
    'run': [
        "run/lock",
        "run/user",
        "run/shm"
    ],
    'var': [
        "var/cache",
        "var/lib",
        "var/log",
        "var/mail",
        "var/spool",
        "var/tmp",
        "var/backups",
        "var/lock"
    ],
    'containers': [
        "containers",
    ],
    # Kernel modules directory dynamically based on the kernel version
    'kernel_modules': [
        "usr/lib/modules"
    ]
}

# Merge extra folders for specific structures
rootfs_extra = (
    rootfs_extra_folders +
    extra_folders['linux_etc'] +
    extra_folders['run'] +
    extra_folders['var'] +
    extra_folders['kernel_modules']
)

oem_extra = (
    rootfs_extra_folders +
    extra_folders['firmware'] +
    extra_folders['kernel_modules']
)

# Combine the extra folders into the dictionary
extra_folders_combined = {
    'root': [],
    'recovery': rootfs_extra,
    'rootfs': rootfs_extra,
    'rootfs_usr': [
        "bin",
        "lib",
        "lib32",
        "lib64",
        "local",
        "share",
        "src"
    ],  # Extra folders for usr structure
    'containers': extra_folders['containers'],
    'oem': oem_extra + [
        "modules",
        "firmware",
        "keys",
        "manufacturer",
        "wifi",
        "carrier",
        "touch"
    ],
}

# Function to create the directory and symlink structure based on a provided definition
def create_structure(base_path, structure, extra_folders):
    """
    Creates the directory and symlink structure for a given base path.
    
    Args:
        base_path (str): The root path where the folder structure should be created.
        structure (list of tuples): A list of tuples defining the folder structure. Each tuple consists of:
            - name (str): The folder or symlink name.
            - link_target (str or None): The target path for symlinks. None if it's a regular directory.
            - is_symlink (bool): Indicates whether the entry is a symlink or a directory.
        extra_folders (list of str): A list of additional folders to create under the base path.
    
    This function ensures that all required directories and symlinks are properly created, taking into
    account any dependencies between them.
    """
    # Ensure the base_path itself exists
    os.makedirs(base_path, exist_ok=True)

    # Create main directory structure
    for name, link_target, is_symlink in structure:
        path = os.path.join(base_path, name)
        if is_symlink:
            # Create a symlink if it doesn't exist yet
            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)  # Make sure parent dirs exist
                os.symlink(link_target, path)  # Create symlink
                pr_info(f"Created symlink {path} -> {link_target}", log_tag)
        else:
            # Create regular directory
            os.makedirs(path, exist_ok=True)
            pr_info(f"Created folder {path}", log_tag)

    # Now, create the extra folders ensuring parent directories exist
    for folder in extra_folders:
        full_path = os.path.join(base_path, folder)
        os.makedirs(full_path, exist_ok=True)
        pr_info(f"Created extra folder {full_path}", log_tag)

# Function to clean up an existing directory structure
def clean_structure(base_path):
    """
    Deletes an existing directory structure at the given base path.
    
    Args:
        base_path (str): The root path to be deleted.
    
    This function ensures that any existing directory structure at the given base path is completely
    removed before creating a new one.
    """
    if os.path.exists(base_path):
        shutil.rmtree(base_path)  # Remove the entire directory tree
        pr_debug(f"Cleaned up existing structure at {base_path}", log_tag)

# Function to set up a directory structure based on a specific key
def setup_directory(base_path, structure_key):
    """
    Sets up a specific directory structure by first cleaning any existing structure and then creating a new one.
    
    Args:
        base_path (str): The root path where the folder structure should be created.
        structure_key (str): The key to identify which structure to create (e.g., 'root', 'rootfs', 'recovery').
    
    This function uses the predefined folder structures and additional folders to create a fully
    configured directory structure at the specified base path.
    """
    clean_structure(base_path)  # Clean up any existing content
    create_structure(base_path, folder_structures[structure_key], extra_folders_combined.get(structure_key, []))  # Create new structure
    pr_info(f"{structure_key.capitalize()} folder structure created at {base_path}", log_tag)

# Main function to orchestrate directory creation
def main():
    """
    Main function to orchestrate the creation of multiple directory structures.
    
    This function is responsible for setting up various directory structures such as root, rootfs, recovery,
    oem, boot, and containers data. It ensures that each directory structure is properly cleaned and recreated
    with the required folders and symlinks.
    """
    # Setup root, rootfs, recovery, oem, and boot directories
    setup_directory(target_root_out, 'root')  # Setup root directory structure
    setup_directory(target_system_out, 'rootfs')  # Setup root filesystem structure
    setup_directory(os.path.join(target_system_out, 'usr'), 'rootfs_usr')  # Setup /usr inside rootfs
    setup_directory(target_recovery_out, 'recovery')  # Setup recovery partition structure
    setup_directory(target_oem_out, 'oem')  # Setup OEM-specific structure
    setup_directory(target_boot_out, 'boot')  # Setup boot partition structure
    setup_directory(target_container_data_out, 'containers_data')  # Setup container data structure

# Entry point of the script
if __name__ == "__main__":
    main()
