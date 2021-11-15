#!/usr/bin/python

import os

target_system_out = os.environ.get('TARGET_SYSTEM_OUT')
target_vendor_out = os.environ.get('TARGET_VENDOR_OUT')
get_build_variant = os.environ.get('TARGET_BUILD_VARIANT')


def write_default_prop(prop, var):
    with open(f'{target_system_out}/etc/prop.default', 'a') as f:
        f.write(f'{prop}={var}\n')


def write_vendor_prop(prop, var):
    with open(f'{target_vendor_out}/etc/prop.default', 'a') as f:
        f.write(f'{prop}={var}\n')


def generate_props():
    write_default_prop("androidboot_persist", "mnt/persist")
    write_default_prop("androidboot_kernel", "/dev/bootdevice/by_name/kernel")
    write_default_prop("androidboot_heap", "4096")
    write_default_prop("androidbootbootloader_version", "11.3")
    if (os.environ.get('TARGET_BUILD_VARIANT') == 'eng'):
        write_default_prop("androidboot_secure", "1")
        write_default_prop("ro_boot_selinux", "enforcing")
        write_default_prop("ro_sys_persist_logging", "true")
        write_default_prop("ro_adb_secure", "1")
        write_default_prop("ro_debuggable", "0")
        write_default_prop("debug_atrace_tags_enableflags", "1")
    else:
        write_default_prop("androidboot_secure", "0")
        write_default_prop("ro_boot_selinux", "permissive")
        write_default_prop("ro_sys_persist_logging", "verbose")
        write_default_prop("ro_adb_secure", "0")
        write_default_prop("ro_debuggable", "1")
        write_default_prop("debug_atrace_tags_enableflags", "0")
    if (os.environ.get('TARGET_BUILD_SYSTEM_AS_ROOT') == 'true'):
        write_default_prop("androidboot_kernel_init", "true")
        write_default_prop("androidboot_first_stage_init", 'true')
        write_default_prop("androidboot_reason", 'true')
        write_default_prop("androidboot_mnt_path", '/')
        write_default_prop("androidboot_cpu_mx_nr",
                           os.environ.get('TARGET_BOARD_MAX_CPU'))
        write_default_prop("androidboot_odm_name",
                           os.environ.get('TARGET_DEVICE'))
    if (os.environ.get('TARGET_USES_FDE') == 'true'):
        write_default_prop("androidboot_selinux_override", "locked")
        write_default_prop("androidboot_selinux_sha_crypto", "256")
        write_default_prop("androidboot_selinux_pgp_key", "0")

    write_default_prop("ro_boot_hardware", os.environ.get('TARGET_DEVICE'))
    write_default_prop("ro_board_name", os.environ.get('TARGET_DEVICE'))
    write_default_prop('ro_kernel_version', os.environ.get('SCM_VERSION'))
    write_default_prop('ro_kernel_dtb_offset',
                       os.environ.get('DTB_TABLE_OFFSET'))
    write_default_prop('ro_boot_build_date', os.environ.get('BUILD_DATE'))
    write_default_prop('ro_actionable_compatible_property', 'false')
    write_default_prop('ro_postinstall_fstab_prefix', '/system')
    write_default_prop('ro_allow_mock_location', 'true')
    write_default_prop('ro_com_google_clientidbase', 'android_google')
    write_default_prop('ro_control_privapp_permissions', 'enforce')
    write_default_prop('ro_storage_manager_enabled', 'true')
    write_default_prop('persist_sys_dun_override', '0')
    write_default_prop('media_recorder_show_manufacturer_and_model', 'true')
    write_default_prop('dalvik_vm_image_dex2oat_Xms', '128m')
    write_default_prop('dalvik_vm_image_dex2oat_Xmx', '128m')
    write_default_prop('dalvik_vm_dex2oat_Xms', '128m')
    write_default_prop('dalvik_vm_dex2oat_Xmx', '782m')
    write_default_prop('dalvik_vm_usejit', 'true')
    write_default_prop('dalvik_vm_usejitprofiles', 'true')
    write_default_prop('dalvik_vm_dexopt_secondary', 'true')
    write_default_prop('dalvik_vm_appimageformat', 'lz4')
    write_default_prop('ro_dalvik_vm_native_bridge', '0')
    write_default_prop('pm_dexopt_first_boot', 'extract')
    write_default_prop('pm_dexopt_install', 'speed_profile')
    write_default_prop('pm_dexopt_bg_dexopt', 'speed_profile')
    write_default_prop('pm_dexopt_ab_ota', 'speed_profile')
    write_default_prop('pm_dexopt_inactive', 'verify')
    write_default_prop('pm_dexopt_shared', 'speed')
    write_default_prop('dalvik_vm_dex2oat_resolve_startup_strings', 'true')
    write_default_prop('dalvik_vm_dex2oat_max_image_block_size', '524288')
    write_default_prop('dalvik_vm_minidebuginfo', 'true')
    write_default_prop('dalvik_vm_dex2oat_minidebuginfo', 'true')
    write_default_prop('ro_dynamic_partitions', os.environ.get(
        'TARGET_BOARD_DYNAMIC_PARTITONS'))
    write_default_prop('tombstoned_max_tombstone_count', '50')
    write_default_prop('persist_sys_usb_config', '')


generate_props()
