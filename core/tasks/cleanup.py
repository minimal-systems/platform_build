# cleanspec.py

import os
import shutil

# Import necessary variables from envsetup
from envsetup import (
    target_product_out,
    target_system_out,
    target_vendor_out,
    target_root_out,
    target_recovery_out,
    target_kernel_out,
    target_container_out,
)

# List of folders to exclude from cleanup (e.g., 'OBJ' and 'INSTALLED')
exclude_folders = ['OBJ', 'INSTALLED']

# List of folders to clean during installclean
cleanup_folders = [
    target_system_out,
    target_vendor_out,
    target_root_out,
    target_recovery_out,
    target_kernel_out,
    target_container_out,
]

# List to store additional folders and files to clean
additional_cleanup_folders = []
cleanup_files = []

# Iterate through the items in target_product_out
items = os.listdir(target_product_out)
for item in items:
    item_path = os.path.join(target_product_out, item)
    
    # Exclude specified folders from cleanup
    if item in exclude_folders:
        continue

    # Add directories to additional_cleanup_folders
    if os.path.isdir(item_path):
        additional_cleanup_folders.append(item_path)
    # Add .img and .bin files to cleanup_files
    elif item.endswith('.img') or item.endswith('.bin'):
        cleanup_files.append(item_path)

# Combine the cleanup folders
cleanup_folders.extend(additional_cleanup_folders)

# Function to perform installclean tasks
def installclean():
    # Remove files
    for file_path in cleanup_files:
        if os.path.exists(file_path):
            print(f"Removing file: {file_path}")
            os.remove(file_path)

    # Remove directories
    for folder_path in cleanup_folders:
        if os.path.exists(folder_path):
            print(f"Removing directory: {folder_path}")
            shutil.rmtree(folder_path)

    print("Installclean completed successfully.")

# Entry point
if __name__ == '__main__':
    installclean()
