import os
import platform
import importlib.util
import sys

##
## Common build system definitions.  Mostly standard
## commands for building various types of targets, which
## are used by others to construct the final targets.
##

# These are variables we use to collect overall lists
# of things being processed.

# Full paths to all of the documentation
all_docs = []


def get_host_2nd_arch():
    host_arch = platform.machine().lower()
    if host_arch == 'x86_64':
        return 'i686'
    elif host_arch in ['arm64', 'aarch64']:
        return 'arm'
    return 'unknown'

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)
        
def product_copy_files(src, dest):
    for root, dirs, files in os.walk(src):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest, os.path.relpath(src_file, src))
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            os.system(f'cp -f {src_file} {dest_file}')

def parse_and_copy_files(file_list):
    for entry in file_list:
        if ':' in entry:
            src, dest = entry.split(':')
            dest = dest.format(target_product_out=os.environ.get('TARGET_PRODUCT_OUT', ''))
            product_copy_files(src, dest)

def include(module_path):
    module_name = os.path.splitext(os.path.basename(module_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    globals().update(vars(module))

