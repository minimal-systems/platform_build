"""
This script defines essential system packages for a Linux from Scratch (LFS) build using Clang as the compiler.
It includes the necessary utilities, libraries, and tools that are fundamental for a minimal yet functional system.

Product packages included:
- Base System: Linux kernel, system initialization, core utilities, file system utilities, shells, basic libraries.
- Compiler and Tools: Clang, LLVM, binutils.
- Boot Loader: GRUB.
- File and Disk Management: File system tools, archiving tools, device management.
- Networking: Networking utilities, DHCP client, DNS tools, SSH client.
- Text Processing: Text editors, printing and conversion tools.
- Development Tools: Version control, build tools, scripting languages.
- System Monitoring and Administration: Process management, system logging, performance monitoring, user management.
- Additional Utilities: Text utilities, networking tools, file transfer, compression tools.
- Shared Libraries: Essential shared libraries required for the included packages.
"""

# Initialize the list of product packages if not already defined
try:
    product_packages
except NameError:
    product_packages = []

# Essential system packages
product_packages += [
    "linux",
    "systemd",
    "coreutils",
    "e2fsprogs",
    "util-linux",
    "bash",
    "dash",
    "glibc",
    "clang",
    "llvm",
    "binutils",
    "grub",
    "dosfstools",
    "ntfs-3g",
    "tar",
    "gzip",
    "bzip2",
    "xz",
    "zip",
    "unzip",
    "udev",
    "iproute2",
    "net-tools",
    "wget",
    "curl",
    "dhcpcd",
    "bind-utils",
    "iputils",
    "openssh",
    "vim",
    "nano",
    "cups",
    "ghostscript",
    "git",
    "make",
    "cmake",
    "perl",
    "python",
    "procps-ng",
    "rsyslog",
    "htop",
    "iotop",
    "shadow",
    "du",
    "df",
    "ncdu",
    "grep",
    "sed",
    "awk",
    "ping",
    "traceroute",
    "netcat",
    "rsync",
    "init",
]

# Add shared libraries to product packages
product_packages += [
    "libc",
    "libm",
    "libpthread",
    "libdl",
    "libutil",
    "libpam",
    "libaudit",
    "libclang",
    "libLLVM",
    "libstdc++",
    "libgcc_s",
    "libuuid",
    "libblkid",
    "libmount",
    "libsmartcols",
    "libe2p",
    "libcom_err",
    "libpcap",
    "libssl",
    "libcrypto",
    "libz",
    "libncurses",
    "libtinfo",
    "libreadline",
    "libperl",
    "libpython",
    "libtcl",
    "libprocps",
    "libsystemd",
    "libudev",
    "libbz2",
    "liblzma",
    "libpcre",
    # add logging libraries
    "liblog",
]

def call_all_gnome_core():
    global product_packages
    product_packages += [
        "com.gnome.gnome-core",
        "com.gnome.gnome-core-apps",
        "com.gnome.gnome-core-settings",
        "com.gnome.gnome-core-extensions",
        "com.gnome.gnome-core-themes",
        "com.gnome.gnome-core-icons",
        "com.gnome.gnome-core-shell",
        "com.gnome.gnome-core-session",
        "com.gnome.gnome-core-utilities",
        "com.gnome.gnome-core-games",
    ]

call_all_gnome_core()

def call_all_gnome_config_overrides():
    global product_packages
    package_name = "com.gnome.gnome-config-overrides"
    product_packages += [package_name]

def generate_override_config():
    print("Generating override config")
    with open("system_config.xml", "w") as f:
        f.write("override_config")

def call_all_gnome_display_manager():
    global product_packages
    product_packages += [
        "com.gnome.gnome-display-manager",
    ]

# Recovery postinstall commands
recovery_postinstall_commands = [
    "# recovery is installed in /etc/recovery.img",
    "# update_recovery",
    "exec /sbin/update_recovery",
]

# Target filesystem generated images
target_fs_generated_filesystem_images = [
    "rootfs.img",
    "root.img",
    "boot.img",
    "system_mapping.img",
    "recovery.img",
    "containers.img",
    "sec.img",
    "vbmeta.img",
    "misc-info.img",
    "firmware/intel-ucode.img",
    "firmware/intel-ucode.sig",
    "firmware/amd-ucode.sig",
    "firmware/amd-ucode.img",
    "persist.img",
    "metadata.img",
    "user_containers.img",
]

target_overlay = [
    "etc",
    "usr",
    "var",
    "run",
    "containers",
    "mnt",
    "proc",
    "sys",
    "dev",
    "tmp",
    "lib",
    "sbin",
    "bin",
    "opt",
    "srv",
    "home",
    "root",
    "boot",
    "media",
    "mnt",
    "lost+found",
    "mnt",
    "mnt/containers",
    "mnt/containers/image",
    "mnt/containers/network",
    "mnt/containers/volumes",
    "mnt/containers/tmp",
    "mnt/containers/plugins",
    "mnt/containers/trust",
    "mnt/containers/swarm",
    "mnt/containers/secret",
    "mnt/containers/config",
    "mnt/containers/build",
    "mnt/containers/daemon",
    "mnt/containers/overlay",
]

# Additional packages can be added below if necessary
