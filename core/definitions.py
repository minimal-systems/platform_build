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

# a list of all module targets in the system.
# for each element in the `all_modules` list, two additional variables
# are defined:
#   all_modules[target].built
#   all_modules[target].installed
#
# the `built` attribute stores the `local_built_module` for that target,
# and the `installed` attribute stores the `local_installed_module`.
#
# some targets may have multiple files listed in the `built` and `installed`
# attributes.
all_modules = []

all_make_module_info_json_modules = []

# the relative paths of the non-module targets in the system.
all_non_modules = []
non_modules_without_license_metadata = []

# list of copied targets that need license metadata.
all_copied_targets = []

# Full paths to targets that should be added to the "make linux"
# set of installed targets.
all_default_installed_modules = []

# Full path to all asm, C, C++, lex and yacc generated C files.
# These all have an order-only dependency on the copied headers
all_c_cpp_etc_objects = []

# These files go into the SDK
all_sdk_files = []

# All findbugs xml files
all_findbug_files = []

# Packages with certificate violation
certificate_violation_modules = []

# Target and host installed module's dependencies on shared libraries.
# They are list of "<module_name>:<installed_file>:lib1,lib2...".
# 2nd arch variant dependencies on shared libraries is also stored.
target_dependencies_on_shared_libraries = {}
target_2nd_arch_variant_dependencies_on_shared_libraries = {}
host_dependencies_on_shared_libraries = {}
host_2nd_arch_dependencies_on_shared_libraries = {}
host_cross_dependencies_on_shared_libraries = {}
host_cross_2nd_arch_dependencies_on_shared_libraries = {}

# Display names for various build targets
target_display = "target"
host_display = "host"
host_cross_display = "host cross"

# All installed initrc files
all_init_rc_installed_pairs = []

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

