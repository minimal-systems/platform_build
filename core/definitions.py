import os
import platform
import importlib.util
import sys
from pathlib import Path

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

# List to hold all installed configuration or metadata fragments for a Linux system
all_config_fragments_list = []

# List to hold all tests that should be skipped in the presubmit check
all_disabled_presubmit_tests = []

# List to hold all compatibility suites mentioned in local_compatibility_suites in module_info.bp
all_compatibility_suites = []

# List to hold all compatibility suite files to be distributed
all_compatibility_dist_files = []

# List to hold all link type entries
all_link_types = []

# List to hold all exported/imported include entries
exports_list = []

# List to hold all modules already converted to Soong
soong_already_converted = []

###########################################################
## Debugging; prints a variable list to stdout
###########################################################

# Function to print variable names and their corresponding values
def print_vars(variable_names, variables):
    """
    Print the names of variables and their corresponding values.

    Args:
        variable_names (list): List of variable names as strings.
        variables (dict): Dictionary containing variable names as keys and their values as list of strings.
    """
    # Check if variable_names is empty
    if not variable_names:
        print("No variable names provided.")
        return

    # Print each variable and its values
    for var in variable_names:
        # Print the variable name and the number of values it contains (if applicable)
        value_count = len(variables.get(var, []))
        print(f"{var}: ({value_count} values)")

        # If the variable has values, print them with indentation
        if var in variables and variables[var]:
            for value in variables[var]:
                print(f"  {value}")  # Two spaces for indentation
        else:
            print("  (No values found)")

###########################################################
# Evaluates to "true" if the string contains the word "true",
# and returns an empty string otherwise.
# Arguments:
#     var (str): A variable or string to test.
###########################################################

def true_or_empty(var):
    """
    Returns "true" if the string contains "true", otherwise returns an empty string.

    Args:
        var (str): A variable or string to test.

    Returns:
        str: "true" if the input string contains "true", otherwise an empty string.
    """
    return "true" if "true" in var else ""

def boolean_not(var):
    """
    Returns "true" if the input string does NOT contain "true", otherwise returns an empty string.

    Args:
        var (str): A variable or string to test.

    Returns:
        str: "true" if the input string does not contain "true", otherwise an empty string.
    """
    return "" if "true" in var else "true"

###########################################################
# Rule for touching GCNO files.
# Args:
#     source_file (str or Path): Path to the source file (dependency).
#     gcno_file (str or Path): Path to the GCNO file to be touched.
###########################################################

def gcno_touch_rule(source_file, gcno_file):
    """
    Updates the timestamp of the GCNO file if the source file exists.
    If the GCNO file does not exist, it will be created.

    Args:
        source_file (str or Path): Path to the source file (dependency).
        gcno_file (str or Path): Path to the GCNO file to be touched.
    """
    # Convert input paths to Path objects for consistency
    source_file = Path(source_file)
    gcno_file = Path(gcno_file)

    # Check if the source file exists
    if source_file.exists():
        # If the gcno file exists, update its timestamp
        if gcno_file.exists():
            gcno_file.touch()  # This updates the timestamp of the file
            print(f"Updated timestamp for existing file: {gcno_file}")
        else:
            # Create the gcno file if it does not exist
            gcno_file.touch()
            print(f"Created new GCNO file: {gcno_file}")
    else:
        print(f"Source file {source_file} does not exist. GCNO file not touched or created.")

###########################################################

###########################################################
## Retrieve the directory of the current makefile
## Must be called before including any other makefile!!
###########################################################

def get_module_dir(module_file, build_system_dir, out_dir):
    """
    Retrieves the directory of the current module file (e.g., `module_info.bp`).

    Args:
        module_file (str or Path): Path to the current module file (e.g., `module_info.bp`).
        build_system_dir (str or Path): Path to the build system directory.
        out_dir (str or Path): Path to the output directory.

    Returns:
        str: Directory of the current module file.

    Raises:
        RuntimeError: If `get_module_dir` is called after other modules have been included.
    """
    # Convert input paths to Path objects for easier handling
    module_file = Path(module_file)
    build_system_dir = Path(build_system_dir)
    out_dir = Path(out_dir)

    # Check if the module file is valid and exists
    if not module_file.exists():
        raise FileNotFoundError(f"Module file {module_file} does not exist.")

    # Check if the module file is in build_system_dir or out_dir
    if module_file.is_relative_to(build_system_dir) or module_file.is_relative_to(out_dir):
        raise RuntimeError("get_module_dir must be called before including other module files.")

    # Return the directory of the current module file
    return str(module_file.parent)

###########################################################
# Retrieve a list of all `module_info.bp` files immediately
# below the specified directory.
#
# Args:
#     base_dir (str or Path): The base directory to search in.
#
# Returns:
#     list: List of paths to `module_info.bp` files found in the specified directory.
###########################################################

def all_module_info_under(base_dir):
    """
    Retrieve a list of all `module_info.bp` files in the specified directory and its subdirectories.

    Args:
        base_dir (str or Path): The base directory to search in.

    Returns:
        list: List of paths to `module_info.bp` files found in the specified directory and its subdirectories.
    """
    base_dir = Path(base_dir)  # Convert to Path object for easier manipulation

    # Use rglob to find all `module_info.bp` files recursively in base_dir and its subdirectories
    module_info_files = [str(file) for file in base_dir.rglob("module_info.bp")]

    return module_info_files

#TODO: add this to testcases
# # Example usage
# base_dir_example = "/run/media/kjones/build/android/minimal_linux/"
# module_info_files = all_module_info_under(base_dir_example)
# print("Found module_info.bp files:")
# for file in module_info_files:
#     print(f" - {file}")

def first_module_info_under(base_dir, filename="module_info.bp", min_depth=0, max_depth=None):
    """
    Retrieve a list of all specified files (e.g., `module_info.bp`) in the given directory and its subdirectories.
    Allows control over minimum and maximum depth to filter results.

    Args:
        base_dir (str or Path): The base directory to search in.
        filename (str): The filename to search for (default is "module_info.bp").
        min_depth (int): Minimum depth of subdirectories to include files (default is 0, which includes all files).
        max_depth (int or None): Maximum depth of subdirectories to include files (default is None, which means no limit).

    Returns:
        list: List of paths to the specified files found in the directory and its subdirectories.
    """
    base_dir = Path(base_dir).resolve()  # Convert to absolute Path object for consistency

    # List to store the paths of found files
    found_files = []

    # Use rglob to find all instances of the specified filename
    for file in base_dir.rglob(filename):
        # Calculate the depth of the current file relative to the base directory
        relative_depth = len(file.relative_to(base_dir).parts)

        # Check if the file is within the specified depth range
        if relative_depth >= min_depth and (max_depth is None or relative_depth <= max_depth):
            found_files.append(str(file))  # Append the path as a string

    return found_files

#TODO: add this to testcases
# # Example usage
# base_dir_example = "/run/media/kjones/build/android/minimal_linux/"
# module_info_files = first_module_info_under(base_dir_example, filename="module_info.bp", min_depth=2)
# print("Found module_info.bp files:")
# for file in module_info_files:
#     print(f" - {file}")

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

