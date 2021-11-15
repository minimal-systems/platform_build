
import os

target_system_out = os.environ.get('TARGET_SYSTEM_OUT')
target_vendor_out = os.environ.get('TARGET_VENDOR_OUT')
target_recovery_out = os.environ.get('TARGET_RECOVERY_OUT')
target_root_out = os.environ.get('TARGET_ROOT_OUT')


def generate_recovery_folders():
    recovery_folder_list = ['dev', 'firmware', 'mnt',
                            'etc', 'odm', 'oem', 'persist', 'sbin', 'proc', 'sys']
    for items in recovery_folder_list:
        os.makedirs(f'{target_recovery_out}/{items}', exist_ok=True)


def generate_system_folders():
    system_folder_list = ['apex', 'app', 'lib64', 'lib', 'etc',
                          'fonts', 'framework', 'media', 'priv-app', 'usr', 'xbin', 'bin']
    for items in system_folder_list:
        os.makedirs(f'{target_system_out}/{items}', exist_ok=True)


def generate_vendor_folders():
    vendor_folder_list = ['app', 'lib', 'bin', 'lib64',
                          'etc', 'firmware', 'media', 'priv-app']
    for items in vendor_folder_list:
        os.makedirs(f'{target_vendor_out}/{items}', exist_ok=True)


def generate_boot_folders():
    boot_folder_list = ['dev', 'firmware', 'proc', 'persist',
                          'mnt', 'odm', 'oem', 'sys']
    for items in boot_folder_list:
        os.makedirs(f'{target_root_out}/{items}', exist_ok=True)

generate_recovery_folders()
generate_system_folders()
generate_vendor_folders()
generate_boot_folders()
