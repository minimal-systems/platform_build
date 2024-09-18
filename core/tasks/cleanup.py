# support cleanspec.py
# to add the following cleanup tasks:

from envsetup import *

from build.make.core.envsetup import target_container_out

items = os.listdir(target_product_out)
# if we are doing installclean, we want to exclude the following folders
# from the cleanup process OBJ and INSTALLED
cleanup_folders = [
    target_system_out,
    target_vendor_out,
    target_root_out,
    target_recovery_out,
    target_kernel_out,
    target_container_out
]

# Iterate through the items
for item in items:
    item_path = os.path.join(target_product_out, item)
    
    # Check if the item is a directory
    if os.path.isdir(item_path):
        cleanup_folders.append(item_path)
    # Check if the item is a file with .img or .bin extension
    elif item.endswith('.img') or item.endswith('.bin'):
        cleanup_folders.append(item_path)


# do the installclean tasks

print("Cleanup items:", cleanup_folders)