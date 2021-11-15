#ifneq ($(TARGET_BOARD_DISABLES_SELINUX),true)
#BOARD_CMDLINE_OVERRIDE +=  -enforce=0 -androidboot_bootloader_selinux=0
#else
BOARD_CMDLINE_OVERRIDE +=  enforce=1 androidboot_bootloader_selinux=enforce androidboot_init_secure=true androidboot_secure_verity_key_path=vendor/etc/security/verity_keys  androidboot_secureboot_sha=$(shell echo $(TARGET_DEVICE) $(USER) | md5sum | grep -o '^\S\+')
#endif


ifneq ($(TARGET_BOARD_DISABLES_SELINUX),true)
export BOOTLOADER_CMDLINE
export BOARD_SEPOLICY_DIRS
else
export BOARD_SEPOLICY_DIRS
endif

