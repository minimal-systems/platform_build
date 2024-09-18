import os
import shutil
import subprocess
from envsetup import *
from build_logger import *
from device_info import rootfs_extra_folders

log_tag = "generate_folders"

# Function to get the kernel version (uname -r)
def get_kernel_version():
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
        ('bin', 'usr/bin', True),
        ('boot', None, False),
        ('dev', None, False),
        ('etc', None, False),
        ('home', None, False),
        ('lib', 'usr/lib', True),
        ('lib64', 'usr/lib', True),
        ('mnt', None, False),
        ('opt', None, False),
        ('proc', None, False),
        ('root', None, False),
        ('run', None, False),
        ('sbin', 'usr/bin', True),
        ('srv', None, False),
        ('sys', None, False),
        ('tmp', None, False),
        ('usr', None, False),
        ('var', 'run', True)  # var is now a symlink to run
    ],
    'rootfs': [
        ('bin', 'usr/bin', True),
        ('containers', None, False),
        ('etc', None, False),
        ('lib', 'usr/lib', True),
        ('lib64', 'usr/lib', True),
        ('sbin', 'usr/bin', True),
        ('usr', None, False),  # Setup the usr directory inside rootfs
        ('var', 'run', True)  # var is now a symlink to run
    ],
    'rootfs_usr': [
        ('bin', None, False),
        ('include', None, False),
        ('lib', None, False),
        ('lib32', None, False),
        ('lib64', 'lib', True),  # Symlink lib64 to lib
        ('local', None, False),
        ('sbin', 'bin', True),  # Symlink sbin to bin
        ('share', None, False),
        ('src', None, False)
    ]
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
        "containers/data",           # Contains the actual data or container layers
        "containers/overlay",        # Overlay filesystem directory for upper and lower layers
        "containers/overlay/lower",  # Lower directory for read-only layers
        "containers/overlay/upper",  # Upper directory for read-write layers
        "containers/overlay/work",   # Work directory used by overlayfs
        "containers/overlay/merged", # Merged view of the upper and lower layers
        "containers/config",         # Configuration files for containers
        "containers/logs",           # Logs directory
        "containers/runtimes",       # Runtimes for containers (e.g., runc)
        "containers/network",        # Networking configurations for containers
        "containers/volumes",        # Volumes for persistent storage
        "containers/secrets",        # Secrets mounted inside containers
        "containers/tmp",            # Temporary files for containers
        "containers/hooks",          # Hooks for custom behavior (e.g., pre-start, post-stop)
        "containers/snapshots",      # Snapshots of container states
        "containers/runtime",        # Contains runtime-specific directories (cgroups, etc.)
    ],
    # Kernel modules directory dynamically based on the kernel version
    'kernel_modules': [
        "usr/lib/modules"
    ]
}

# Merge extra folders for specific structures
rootfs_extra = (rootfs_extra_folders +
                extra_folders['wlan'] +
                extra_folders['carrier'] +
                extra_folders['firmware'] +
                extra_folders['touch_firmware'] +
                extra_folders['linux_etc'] +
                extra_folders['run'] +
                extra_folders['var'] +
                extra_folders['kernel_modules'])

# Combine the extra folders into the dictionary
extra_folders_combined = {
    'root': [],
    'recovery': [],
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
    'containers': extra_folders['containers']
}


def create_structure(base_path, structure, extra_folders):
    # Ensure the base_path itself exists
    os.makedirs(base_path, exist_ok=True)

    # First, create the main directory structure
    for name, link_target, is_symlink in structure:
        path = os.path.join(base_path, name)
        if is_symlink:
            if not os.path.exists(path):
                # Ensure the parent directory of the symlink exists before creating the symlink
                os.makedirs(os.path.dirname(path), exist_ok=True)
                os.symlink(link_target, path)
                pr_info(f"Created symlink {path} -> {link_target}", log_tag)

    # Now, create the extra folders ensuring parent directories exist
    for folder in extra_folders:
        full_path = os.path.join(base_path, folder)
        os.makedirs(full_path, exist_ok=True)
        pr_info(f"Created extra folder {full_path}", log_tag)



def clean_structure(base_path):
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
        pr_debug(f"Cleaned up existing structure at {base_path}", log_tag)


def setup_directory(base_path, structure_key):
    clean_structure(base_path)
    os.makedirs(base_path, exist_ok=True)
    create_structure(base_path, folder_structures[structure_key], extra_folders_combined.get(structure_key, []))
    pr_info(f"{structure_key.capitalize()} folder structure created at {base_path}", log_tag)


def main():
    # Setup root and rootfs directories
    setup_directory(target_root_out, 'root')
    setup_directory(target_system_out, 'rootfs')
    setup_directory(os.path.join(target_system_out, 'usr'), 'rootfs_usr')
    # Ensure rootfs/usr is set up properly with its subdirectories



if __name__ == "__main__":
    main()
