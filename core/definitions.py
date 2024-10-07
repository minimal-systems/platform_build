import fnmatch
import os
import platform
import importlib.util
import sys
from pathlib import Path
import glob
import subprocess
from collections import defaultdict

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

def call_my_dir(module_file, build_system_dir, out_dir):
    """
    Retrieves the directory of the current module file (e.g., `module_info.bp`).

    Args:
        module_file (str or Path): Path to the current module file (e.g., `module_info.bp`).
        build_system_dir (str or Path): Path to the build system directory.
        out_dir (str or Path): Path to the output directory.

    Returns:
        Path: Directory of the current module file.

    Raises:
        RuntimeError: If `call_my_dir` is called after other module files have been included.
    """
    module_file = Path(module_file).resolve()
    build_system_dir = Path(build_system_dir).resolve()
    out_dir = Path(out_dir).resolve()

    if not module_file.exists():
        raise FileNotFoundError(f"Module file {module_file} does not exist.")

    # Ensure that call_my_dir is called before other module files are included.
    if module_file.is_relative_to(build_system_dir) or module_file.is_relative_to(out_dir):
        raise RuntimeError("call_my_dir must be called before including other module files.")

    return module_file.parent

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
    module_file = Path(module_file).resolve()
    build_system_dir = Path(build_system_dir).resolve()
    out_dir = Path(out_dir).resolve()

    if not module_file.exists():
        raise FileNotFoundError(f"Module file {module_file} does not exist.")

    if module_file.is_relative_to(build_system_dir) or module_file.is_relative_to(out_dir):
        raise RuntimeError("get_module_dir must be called before including other module files.")

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

###########################################################
## Look under a directory for makefiles that don't have parent
## makefiles.
###########################################################

# $(1): directory to search under
# Ignores $(1)/module_info.bp

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

###########################################################
## Retrieve a list of all module_info.bp immediately below your directory
## Must be called before including any other module_info.bp!!
###########################################################

def all_subdir_module_info(module_file, build_system_dir, out_dir, filename="module_info.bp", min_depth=0, max_depth=None):
    """
    Retrieve a list of `module_info.bp` files in subdirectories of the specified module file directory.
    Utilizes `get_module_dir` to get the base directory and allows specifying depth constraints.

    Args:
        module_file (str or Path): Path to the current module file (e.g., `module_info.bp`).
        build_system_dir (str or Path): Path to the build system directory.
        out_dir (str or Path): Path to the output directory.
        filename (str): The filename to search for (default is "module_info.bp").
        min_depth (int): Minimum depth of subdirectories to include files (default is 0).
        max_depth (int or None): Maximum depth of subdirectories to include files (default is None).

    Returns:
        list: List of paths to the specified `filename` found immediately below the module directory.
    """
    # Get the module directory using `get_module_dir`
    base_dir = get_module_dir(module_file, build_system_dir, out_dir)
    base_dir = Path(base_dir)

    # List to hold paths of `filename` found in subdirectories
    found_files = []

    print(f"Searching for {filename} files in {base_dir} and its subdirectories...\n")

    # Use rglob to find all instances of the specified filename
    for file in base_dir.rglob(filename):
        # Calculate the depth of the current file relative to the base directory
        relative_depth = len(file.relative_to(base_dir).parts)

        # Print debugging information
        print(f"Found: {file}, Relative Depth: {relative_depth}")

        # Check if the file is within the specified depth range
        if relative_depth >= min_depth and (max_depth is None or relative_depth <= max_depth):
            found_files.append(str(file))  # Append the path as a string

    return found_files

# TODO: add this to testcases
# Example usage:
# module_file_example = "/run/media/kjones/build/android/minimal_linux/vendor/generic/module_info.bp"
# build_system_dir_example = "/run/media/kjones/build/android/minimal_linux/build"
# out_dir_example = "/run/media/kjones/build/android/minimal_linux/out"
# Retrieve `module_info.bp` files immediately below the directory of the current module file
# module_info_files = all_subdir_module_info(module_file_example, build_system_dir_example, out_dir_example)
# print("Found module_info.bp files immediately below the module directory:")
# for file in module_info_files:
#     print(f" - {file}")

###########################################################
## Look in the named list of directories for makefiles,
## relative to the current directory.
## Must be called before including any other makefile!!
###########################################################

# $(1): List of directories to look for under this directory
def all_named_subdir_module_info(directories, current_dir):
    """
    Look for 'module_info.bp' files in the named list of directories relative to the current directory.
    Searches all subdirectories recursively.

    Args:
        directories (list of str or Path): List of directories to look for `module_info.bp` under `current_dir`.
        current_dir (str or Path): The directory relative to which to search for `module_info.bp` files.

    Returns:
        list: A list of paths to all found `module_info.bp` files.
    """
    current_dir = Path(current_dir).resolve()
    found_files = []

    for directory in directories:
        dir_path = current_dir / directory

        if not dir_path.exists() or not dir_path.is_dir():
            continue

        # Use rglob to recursively search for 'module_info.bp' in the directory and its subdirectories
        for makefile in dir_path.rglob("module_info.bp"):
            found_files.append(str(makefile))

    return found_files

###########################################################
## Find all of the directories under the named directories with
## the specified name.
## Meant to be used like:
##    INC_DIRS := $(call all-named-dirs-under,inc,.)
###########################################################
def all_named_dirs_under(directory_name, base_directories):
    """
    Find all directories with the specified name under the given base directories.

    Args:
        directory_name (str): The name of the directories to look for.
        base_directories (list of str or Path): A list of base directories to search under.

    Returns:
        list: A list of paths to all directories matching `directory_name` under the given base directories.
    """
    found_directories = []

    for base_directory in base_directories:
        base_directory = Path(base_directory).resolve()
        if not base_directory.exists() or not base_directory.is_dir():
            continue

        # Use rglob to search for directories with the given name
        for directory in base_directory.rglob(directory_name):
            if directory.is_dir():
                found_directories.append(str(directory))

    return found_directories

###########################################################
## Find all the directories under the current directory that
## haves name that match $(1)
###########################################################

def all_subdir_named_dirs(directory_name):
    """
    Find all directories under the current directory with the specified name.

    Args:
        directory_name (str): The name of the directories to look for.
        current_directory (str or Path): The directory to start the search from. Default is the current directory.

    Returns:
        list: A list of paths to all directories matching `directory_name` under the current directory.
    """
    current_directory = Path(os.getcwd()).resolve()
    found_directories = []

    # Check if the current directory exists and is indeed a directory
    if not current_directory.exists() or not current_directory.is_dir():
        return found_directories

    # Use rglob to search for directories with the given name under the current directory
    for directory in current_directory.rglob(directory_name):
        if directory.is_dir():
            found_directories.append(str(directory))

    return found_directories

###########################################################
## Find all of the files under the named directories with
## the specified name.
## Meant to be used like:
##    src_files = all_named_files_under("*.h", ["src", "tests"])
###########################################################

def all_named_files_under(file_pattern, base_directories, local_path="."):
    """
    Find all of the files under the named directories with the specified name.

    Args:
        file_pattern (str): The file name pattern to search for (e.g., "*.h").
        base_directories (list of str or Path): List of base directories to search under.
        local_path (str or Path): The base path to start searching from. Default is the current directory.

    Returns:
        list: A list of paths to all files that match the specified pattern under the given directories.
    """
    local_path = Path(local_path).resolve()
    found_files = []

    for base_dir in base_directories:
        base_dir_path = local_path / base_dir

        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for files that match the file pattern
        for file_path in base_dir_path.rglob(file_pattern):
            if file_path.is_file():
                found_files.append(str(file_path))

    return

###########################################################
## Find all of the files under the current directory with
## the specified name.
###########################################################

def all_subdir_named_files(file_pattern):
    """
    Find all of the files under the current directory with the specified name.

    Args:
        file_pattern (str): The file name pattern to search for (e.g., "*.h").

    Returns:
        list: A list of paths to all files that match the specified pattern under the current directory.
    """
    # Get the current working directory using os.getcwd()
    current_directory = Path(os.getcwd()).resolve()
    found_files = []

    # Use rglob to search for files that match the file pattern in the current directory
    for file_path in current_directory.rglob(file_pattern):
        if file_path.is_file():
            found_files.append(str(file_path))

    return found_files

###########################################################
## Find all of the c files under the named directories.
## Meant to be used like:
##    src_files = all_c_files_under(["src", "tests"])
###########################################################

def all_c_files_under(base_directories):
    """
    Find all of the `.c` files under the named directories.

    Args:
        base_directories (list of str or Path): List of directories to search for `.c` files.

    Returns:
        list: A list of paths to all `.c` files under the given directories.
    """
    # Get the current working directory using os.getcwd()
    local_path = Path(os.getcwd()).resolve()
    found_files = []

    for base_dir in base_directories:
        base_dir_path = local_path / base_dir

        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for `.c` files in the specified directory and its subdirectories
        for file_path in base_dir_path.rglob("*.c"):
            if file_path.is_file():
                found_files.append(str(file_path))

    return found_files

###########################################################
## Find all of the c files from the current directory.
## Meant to be used like:
##    src_files = all_subdir_c_files()
###########################################################

def all_subdir_c_files():
    """
    Find all `.c` files under the current directory.

    Returns:
        list: A list of paths to all `.c` files under the current directory and its subdirectories.
    """
    # Get the current working directory
    current_directory = Path(os.getcwd()).resolve()
    found_files = []

    # Use rglob to search for `.c` files in the current directory and its subdirectories
    for file_path in current_directory.rglob("*.c"):
        if file_path.is_file():
            found_files.append(str(file_path))

    return found_files

###########################################################
## Find all of the cpp files under the named directories.
## LOCAL_CPP_EXTENSION is respected if set.
## Meant to be used like:
##    src_files = all_cpp_files_under(["src", "tests"], local_cpp_extension=".cpp")
###########################################################

def all_cpp_files_under(base_directories, local_cpp_extension=".cpp"):
    """
    Find all `.cpp` files (or other specified extension) under the named directories.

    Args:
        base_directories (list of str or Path): List of directories to search for `.cpp` files.
        local_cpp_extension (str): The extension to search for (e.g., `.cpp` or `.cc`).

    Returns:
        list: A list of paths to all `.cpp` files (or files with the specified extension) under the given directories.
    """
    # Get the current working directory
    current_directory = Path(os.getcwd()).resolve()
    found_files = []

    for base_dir in base_directories:
        base_dir_path = current_directory / base_dir

        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for files with the given extension in the specified directory and its subdirectories
        for file_path in base_dir_path.rglob(f"*{local_cpp_extension}"):
            # Exclude hidden files (those that start with a dot)
            if file_path.is_file() and not file_path.name.startswith('.'):
                found_files.append(str(file_path))

    # Sort and return the found files
    return sorted(found_files)

###########################################################
## Find all of the cpp files from the current directory.
## Meant to be used like:
##    src_files = all_subdir_cpp_files(local_cpp_extension=".cpp")
###########################################################

def all_subdir_cpp_files(local_cpp_extension=".cpp"):
    """
    Find all `.cpp` files (or other specified extension) under the current directory.

    Args:
        local_cpp_extension (str): The extension to search for (e.g., `.cpp` or `.cc`).

    Returns:
        list: A list of paths to all `.cpp` files (or files with the specified extension) under the current directory.
    """
    # Get the current working directory
    current_directory = Path(os.getcwd()).resolve()
    found_files = []

    # Use rglob to search for files with the given extension in the current directory and its subdirectories
    for file_path in current_directory.rglob(f"*{local_cpp_extension}"):
        # Exclude hidden files (those that start with a dot)
        if file_path.is_file() and not file_path.name.startswith('.'):
            found_files.append(str(file_path))

    # Sort and return the found files
    return sorted(found_files)


###########################################################
## Find all of the S files under the named directories.
## Meant to be used like:
##    src_files = all_S_files_under(["src", "tests"])
###########################################################

def all_S_files_under(base_directories):
    """
    Find all `.S` files under the named directories.

    Args:
        base_directories (list of str or Path): List of directories to search for `.S` files.

    Returns:
        list: A list of paths to all `.S` files under the given directories.
    """
    return find_subdir_files("*.S", base_directories)


###########################################################
## Find all of the html files under the named directories.
## Meant to be used like:
##    src_files = all_html_files_under(["src", "tests"])
###########################################################

def all_html_files_under(base_directories):
    """
    Find all `.html` files under the named directories.

    Args:
        base_directories (list of str or Path): List of directories to search for `.html` files.

    Returns:
        list: A list of paths to all `.html` files under the given directories.
    """
    return find_subdir_files("*.html", base_directories)


###########################################################
## Find all of the html files from here. Meant to be used like:
##    src_files = all_subdir_html_files()
###########################################################

def all_subdir_html_files():
    """
    Find all `.html` files under the current directory and its subdirectories.

    Returns:
        list: A list of paths to all `.html` files under the current directory.
    """
    return all_html_files_under([os.getcwd()])


###########################################################
## Find all of the files matching pattern
##    src_files = find_subdir_files(<pattern>, [<directories>])
###########################################################

def find_subdir_files(pattern, base_directories):
    """
    Find all of the files matching the given pattern under the named directories.

    Args:
        pattern (str): The pattern to search for (e.g., `*.c`).
        base_directories (list of str or Path): List of directories to search under.

    Returns:
        list: A list of paths to all files matching the pattern under the given directories.
    """
    found_files = []
    for base_dir in base_directories:
        base_dir_path = Path(base_dir).resolve()
        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for files matching the pattern in the specified directory and subdirectories
        for file_path in base_dir_path.rglob(pattern):
            if file_path.is_file():
                found_files.append(str(file_path))
    return sorted(found_files)


###########################################################
# Find the files in the subdirectory $1 of LOCAL_DIR matching pattern $2,
# filtering out files $3
# e.g.
#     src_files += find_subdir_subdir_files("css", "*.cpp", "DontWantThis.cpp")
###########################################################

def find_subdir_subdir_files(subdir, pattern, exclude_pattern=None):
    """
    Find all files in the given subdirectory matching the pattern, excluding the files that match `exclude_pattern`.

    Args:
        subdir (str): The subdirectory to search in.
        pattern (str): The pattern to search for (e.g., `*.cpp`).
        exclude_pattern (str): A pattern to exclude files (optional).

    Returns:
        list: A list of paths to all files matching the pattern, excluding files that match `exclude_pattern`.
    """
    current_dir = Path(os.getcwd()).resolve() / subdir
    if not current_dir.exists() or not current_dir.is_dir():
        return []

    # Search for files in the specified subdirectory
    files = [str(file_path) for file_path in current_dir.glob(pattern) if file_path.is_file()]

    # Filter out files matching the exclude pattern, if specified
    if exclude_pattern:
        files = [file for file in files if not fnmatch.fnmatch(file, str(current_dir / exclude_pattern))]

    return sorted(files)

###########################################################
## Find all of the files in the directory, excluding hidden files
##    src_files = find_subdir_assets(<directory>)
###########################################################

def find_subdir_assets(base_directory=None):
    """
    Find all files in the given directory, excluding hidden files.

    Args:
        base_directory (str or Path): The directory to search in. If None, return an empty list.

    Returns:
        list: A list of paths to all non-hidden files in the given directory.
    """
    if not base_directory:
        print(f"Warning: Empty argument supplied to find_subdir_assets in {os.getcwd()}")
        return []

    base_dir_path = Path(base_directory).resolve()
    if not base_dir_path.exists() or not base_dir_path.is_dir():
        return []

    # Find all files, excluding hidden files (those starting with a dot)
    found_files = [str(file_path) for file_path in base_dir_path.rglob("*") if
                   file_path.is_file() and not file_path.name.startswith(".")]
    return sorted(found_files)

###########################################################
## Find various file types in a list of directories relative to the current path.
###########################################################

def find_other_html_files(base_directories):
    """
    Find all `.html` files under the named directories relative to the current directory.

    Args:
        base_directories (list of str or Path): List of directories to search for `.html` files.

    Returns:
        list: A list of paths to all `.html` files under the given directories.
    """
    return all_html_files_under(base_directories)

###########################################################
# Use utility find to find given files in the given subdirs.
# This function uses $(1), instead of LOCAL_PATH as the base.
# $(1): the base dir, relative to the root of the source tree.
# $(2): the file name pattern to be passed to find as "-name".
# $(3): a list of subdirs of the base dir.
# Returns: a list of paths relative to the base dir.
###########################################################

def find_files_in_subdirs(base_dir, pattern, subdirs):
    """
    Find files in the given subdirectories relative to the base directory.

    Args:
        base_dir (str): The base directory relative to the root of the source tree.
        pattern (str): The file name pattern to search for (e.g., "*.cpp").
        subdirs (list of str): List of subdirectories relative to the base directory.

    Returns:
        list: A sorted list of paths relative to the base directory.
    """
    result_files = set()

    for subdir in subdirs:
        # Construct full directory path
        search_dir = os.path.join(base_dir, subdir)

        # Use glob to find matching files, excluding hidden files and directories
        files = glob.glob(f'{search_dir}/**/{pattern}', recursive=True)
        filtered_files = [os.path.relpath(f, base_dir) for f in files if not os.path.basename(f).startswith('.')]

        result_files.update(filtered_files)

    return sorted(result_files)

# Example usage:
# base_dir = "/path/to/base"
# pattern = "*.cpp"
# subdirs = ["dir1", "dir2"]
# print(find_files_in_subdirs(base_dir, pattern, subdirs))

###########################################################
## Scan through each directory of $(1) looking for files
## that match $(2) using $(wildcard).  Useful for seeing if
## a given directory or one of its parents contains
## a particular file.  Returns the first match found,
## starting furthest from the root.
###########################################################

def find_parent_file(start_dir, filename_pattern):
    """
    Scan through each directory of `start_dir` looking for files that match `filename_pattern`.
    Useful for checking if a directory or one of its parents contains a particular file.
    Returns the first match found, starting furthest from the root.

    Args:
        start_dir (str): The directory to start searching from.
        filename_pattern (str): The file name pattern to match (e.g., "Makefile").

    Returns:
        str: The path of the first found file or None if none of the files are found.

    Example:
        start_dir = "/path/to/start/dir"
        filename_pattern = "Makefile"
        result = find_parent_file(start_dir, filename_pattern)
        print(result)  # Outputs: "/path/to/start/Makefile" if found, or None if not found.
    """
    # Normalize start_dir to an absolute path
    current_dir = os.path.abspath(start_dir)

    # Traverse up the directory tree until we reach the root
    while True:
        # Use glob to find matching files in the current directory
        matched_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir)
                         if os.path.isfile(os.path.join(current_dir, f)) and f == filename_pattern]

        # Return the first match found, if any
        if matched_files:
            return matched_files[0]

        # Move up one directory level
        parent_dir = os.path.dirname(current_dir)

        # Stop if we reach the root directory (no more parent directories)
        if current_dir == parent_dir:
            break

        current_dir = parent_dir

    # Return None if no match is found
    return None

###########################################################
## Find test data in a form required by local_test_data.
## $(1): the base dir, relative to the root of the source tree.
## $(2): the file name pattern to be passed to find as "-name"
## $(3): a list of subdirs of the base dir
###########################################################

def find_test_data_in_subdirs(base_dir, filename_pattern, subdirs):
    """
    Find test data in a form required by LOCAL_TEST_DATA.

    Args:
        base_dir (str): The base directory relative to the root of the source tree.
        filename_pattern (str): The file name pattern to search for (e.g., "*.txt").
        subdirs (list of str): List of subdirectories relative to the base directory.

    Returns:
        list of str: A list of strings in the format "base_dir:file_path".
                     Each file path is relative to the base directory.

    Example:
        base_dir = "/path/to/base"
        filename_pattern = "*.txt"
        subdirs = ["subdir1", "subdir2"]
        result = find_test_data_in_subdirs(base_dir, filename_pattern, subdirs)
        print(result)  # Example output: ['/path/to/base:subdir1/file1.txt', '/path/to/base:subdir2/file2.txt']
    """
    result_files = []

    for subdir in subdirs:
        # Construct the full search directory path
        search_dir = os.path.join(base_dir, subdir)

        # Use glob to find all matching files in subdirectories recursively
        files = glob.glob(f'{search_dir}/**/{filename_pattern}', recursive=True)

        # Filter out hidden files and directories (those that start with '.')
        filtered_files = [os.path.relpath(f, base_dir) for f in files if not os.path.basename(f).startswith('.')]

        # Format results in "base_dir:file_path" format
        result_files.extend([f"{base_dir}:{file}" for file in filtered_files])

    return sorted(result_files)

def add_dependency(target, dependency):
    """
    Define a dependency relationship between a target and a dependency.

    Args:
        target (str): The target file or task.
        dependency (str): The dependency file or task.

    Returns:
        tuple: A tuple representing the dependency relationship (target, dependency).

    Example:
        target = "build/output.o"
        dependency = "src/input.c"
        result = add_dependency(target, dependency)
        print(result)  # Output: ('build/output.o', 'src/input.c')
    """
    return target, dependency

def reverse_list(lst):
    """
    Reverse the order of a list.

    Args:
        lst (list): A list of elements to be reversed.

    Returns:
        list: A new list with the elements in reversed order.

    Example:
        original_list = ["a", "b", "c", "d"]
        reversed_list = reverse_list(original_list)
        print(reversed_list)  # Output: ['d', 'c', 'b', 'a']
    """
    if not lst:
        return []
    return reverse_list(lst[1:]) + [lst[0]]

def fix_notice_deps(all_modules, all_modules_attrs):
    """
    Replace unadorned module names in the 'NOTICE_DEPS' attribute with their adorned versions.

    Args:
        all_modules (list of str): List of all module names.
        all_modules_attrs (dict of dict): Attributes of each module, where the outer keys are module names,
                                          and the inner keys include 'NOTICE_DEPS' and 'PATH' attributes.

    Returns:
        dict of dict: Updated module attributes with corrected 'NOTICE_DEPS'.
    """
    # Collect all unique module references from 'NOTICE_DEPS' attributes.
    all_module_refs = {
        dep.split(":")[0] for m in all_modules for dep in all_modules_attrs.get(m, {}).get("NOTICE_DEPS", [])
    }

    # Build a lookup dictionary for adorned module names.
    lookup = {}
    for ref in sorted(all_module_refs):
        if ref in all_modules_attrs and "PATH" in all_modules_attrs[ref]:
            lookup[ref] = [ref]
        else:
            # Find possible adorned versions of the module.
            adorned_versions = [f"{ref}_32", f"{ref}_64", f"host_cross_{ref}", f"host_cross_{ref}_32", f"host_cross_{ref}_64"]
            lookup[ref] = sorted([mod for mod in all_modules if mod in adorned_versions])

    # Update 'NOTICE_DEPS' for each module using the lookup dictionary.
    for module in all_modules:
        notice_deps = all_modules_attrs.get(module, {}).get("NOTICE_DEPS", [])
        updated_deps = []
        for dep in notice_deps:
            dep_name, dep_suffix = dep.split(":", 1) if ":" in dep else (dep, "")
            adorned_names = lookup.get(dep_name, [dep_name])
            updated_deps.extend([f"{name}:{dep_suffix}" for name in adorned_names])

        all_modules_attrs[module]["NOTICE_DEPS"] = sorted(updated_deps)

    return all_modules_attrs

def license_metadata_dir(target, out_dir, generated_sources_dir="META/lic"):
    """
    Generate the target directory for license metadata files.

    Args:
        target (str): The target for which to generate the license metadata directory.
        out_dir (str): The base output directory (equivalent to `PRODUCT_OUT` in Makefile).
        generated_sources_dir (str): The base directory for generated sources. Default is "META/lic".

    Returns:
        str: Path to the license metadata directory.
    """
    # Filter out paths that start with `out_dir` and construct the directory path.
    relative_target = target.replace(out_dir, "").lstrip("/")
    return f"{out_dir}/{generated_sources_dir}/{relative_target}"

targets_missing_license_metadata = []

def corresponding_license_metadata(targets, all_modules, all_targets):
    """
    Retrieve the license metadata files corresponding to the given targets.

    Args:
        targets (list of str): List of target names.
        all_modules (dict of dict): Dictionary containing module attributes, where keys are module names and values are dictionaries of attributes.
        all_targets (dict of dict): Dictionary containing target attributes, where keys are target names and values are dictionaries of attributes.

    Returns:
        list of str: List of license metadata paths corresponding to the given targets.
        list of str: List of targets missing license metadata.
    """

    # Collect license metadata paths for each target, excluding "0p"
    license_metadata_paths = []
    for target in sorted(targets):
        # Check for META_LIC in all_modules first
        meta_lic = all_modules.get(target, {}).get("META_LIC")

        # If not found in all_modules, check in all_targets
        if not meta_lic:
            meta_lic = all_targets.get(target, {}).get("META_LIC")

        # If META_LIC is found, add to the list, otherwise add to missing license metadata list
        if meta_lic:
            license_metadata_paths.append(meta_lic)
        else:
            targets_missing_license_metadata.append(target)

    # Filter out "0p" entries and return both results
    return [lic for lic in license_metadata_paths if lic != "0p"], targets_missing_license_metadata

def declare_copy_target_license_metadata(target, sources, all_copied_targets, out_dir):
    """
    Record a target copied from another source(s) that will need license metadata.

    Args:
        target (str): The target that will need license metadata.
        sources (list of str): List of source paths for the target.
        all_copied_targets (list): List of dictionaries representing copied targets that need license metadata.
        out_dir (str): The base output directory (similar to `OUT_DIR` in the Makefile).

    Returns:
        None: Updates the `all_copied_targets` list in-place.
    """
    # Filter sources to only include those within the output directory.
    filtered_sources = [source for source in sources if source.startswith(out_dir)]

    # If there are sources within the output directory, proceed to record the target.
    if filtered_sources:
        # Strip whitespace from the target.
        target = target.strip()

        # Find existing target in the list or create a new dictionary if it doesn't exist.
        target_entry = next((item for item in all_copied_targets if item.get("target") == target), None)
        if not target_entry:
            target_entry = {"target": target, "sources": []}
            all_copied_targets.append(target_entry)

        # Update the 'sources' field by adding the new sources and keeping them sorted and unique.
        target_entry["sources"] = sorted(set(target_entry["sources"] + filtered_sources))

def _license_metadata_rule(target, meta_lic, all_modules, all_targets, build_license_metadata_cmd, intermediates_dir, out_dir):
    """
    Internal function to process license metadata rules for a given target and meta_lic.

    Args:
        target (str): The target for which the license metadata rule applies.
        meta_lic (str): The specific meta license being processed.
        all_modules (list of dict): List of dictionaries representing all modules with their attributes.
        all_targets (list of dict): List of all targets with their attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        intermediates_dir (str): Directory path for intermediate files.
        out_dir (str): The base output directory for the build.

    Returns:
        tuple: The output and error messages from the build command.
    """
    # Retrieve module dictionary for the given target from the list of modules
    module = next((m for m in all_modules if m.get("name") == target), None)
    if not module:
        return None, f"Module '{target}' not found"

    # Retrieve attributes from the module
    notice_deps = module.get("notice_deps", [])
    built = module.get("built", [])
    installed = module.get("installed", [])
    license_kinds = module.get("license_kinds", [])
    license_conditions = module.get("license_conditions", [])
    notices = module.get("notices", [])
    license_package_name = module.get("license_package_name", "").strip()
    is_container = module.get("is_container", False)
    module_type = module.get("module_type", "")
    module_class = module.get("module_class", "")
    license_install_map = module.get("license_install_map", [])

    # Retrieve sources for the notice_deps
    sources = []
    for dep in notice_deps:
        dep_name = dep.split(":")[0]
        dep_module = next((m for m in all_modules if m.get("name") == dep_name), None)
        sources.extend(dep_module.get("installed", []) or dep_module.get("built", []) or [dep_name])

    # Retrieve dependencies for the notice_deps
    deps = []
    for dep in notice_deps:
        dep_name = dep.split(":")[0]
        suffix = ":".join(dep.split(":")[1:])  # Extract suffix after colon
        dep_module = next((m for m in all_modules if m.get("name") == dep_name), None)
        dep_meta_lics = [
            target_meta.get("meta_lic")
            for target_meta in all_targets if target_meta.get("name") == dep_name
        ]
        # Add dependencies to the list
        deps.extend([f"{file}:{suffix}" for file in dep_meta_lics if file])

    # Prepare license_install_map entries
    install_map = []
    for item in sorted(license_install_map):
        src, dest = item.split(":", 1)
        src_module = next((m for m in all_modules if m.get("name") == src), None)
        source_files = src_module.get("installed", []) or src_module.get("built", []) or [src]
        install_map.extend([f"{file}:{dest}" for file in source_files])

    # Prepare paths and other attributes
    path = sorted(module.get("path", []))
    module_name = target

    # Prepare argument file path
    argument_file = os.path.join(out_dir, "intermediates", "PACKAGING", "notice", target, "arguments")

    # Prepare command arguments to dump into the file
    args_to_dump = [
        f"-mn {module_name}" if module_name else "",  # Make module_name optional
        f"-mt \"{module_type}\"" if module_type else "",  # Use quotes for module_type
        f"-mc \"{module_class}\"" if module_class else "",  # Use quotes for module_class
        f"-k \"{' '.join(sorted(license_kinds))}\"" if license_kinds else "",  # Join and quote license kinds
        f"-c \"{' '.join(sorted(license_conditions))}\"" if license_conditions else "",  # Join and quote license conditions
        f"-n \"{' '.join(sorted(notices))}\"" if notices else "",  # Join and quote notices
        f"-d \"{','.join(sorted(deps))}\"" if deps else "",  # Join dependencies correctly
        f"-s \"{','.join(sorted(sources))}\"" if sources else "",  # Join sources correctly
        f"-m \"{','.join(sorted(install_map))}\"" if install_map else "",  # Join install map correctly
        f"-t \"{' '.join(sorted(built))}\"" if built else "",  # Quote built targets
        f"-i \"{' '.join(sorted(installed))}\"" if installed else "",  # Quote installed targets
        f"-r \"{' '.join(sorted(path))}\"" if path else ""  # Quote paths
    ]

    # Remove empty arguments
    args_to_dump = [arg for arg in args_to_dump if arg]

    # Create directories and write arguments to the argument file
    os.makedirs(os.path.dirname(argument_file), exist_ok=True)
    with open(argument_file, 'w') as file:
        file.write("\n".join(args_to_dump))

    # Read the argument file and format arguments correctly
    with open(argument_file, 'r') as file:
        argument_content = " ".join(line.strip() for line in file if line.strip())

    # Update all_targets with the metadata (as a dictionary entry)
    all_targets.append({
        "name": target,
        "meta_lic": meta_lic,
        "private_kinds": sorted(license_kinds),
        "private_conditions": sorted(license_conditions),
        "private_notices": sorted(notices),
        "private_notice_deps": sorted(deps),
        "private_sources": sorted(sources),
        "private_targets": sorted(built),
        "private_installed": sorted(installed),
        "private_path": sorted(path),
        "private_is_container": is_container,
        "private_package_name": license_package_name,
        "private_install_map": sorted(install_map),
        "private_module_name": module_name,
        "private_module_type": module_type,
        "private_module_class": module_class,
        "private_argument_file": argument_file
    })

    # Construct the build command with correctly formatted arguments
    build_command = f"OUT_DIR={out_dir} {build_license_metadata_cmd} "
    if is_container:
        build_command += "--is_container "
    build_command += f"-p '{license_package_name}' {argument_content} -o {meta_lic}"

    try:
        # Execute the build command and capture the output and error
        result = subprocess.run(
            build_command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"Build Command Output:\n{result.stdout}")
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        # If the command fails, capture the error output and return it
        print(f"Build Command Error:\n{e.stderr}")
        return e.stdout, e.stderr

def license_metadata_rule(target, all_modules, all_targets, build_license_metadata_cmd, intermediates_dir, out_dir):
    """
    License metadata build rule for the given target.

    Args:
        target (str): The target for which license metadata needs to be built.
        all_modules (list of dict): List of dictionaries representing all modules with their attributes.
        all_targets (list of dict): List of all targets with their attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        intermediates_dir (str): Directory path for intermediate files.
        out_dir (str): The base output directory for the build.

    Returns:
        None: The function updates the `all_targets` list in-place.
    """
    # Get the delayed meta_lic list for the target
    module = next((m for m in all_modules if m.get("name") == target), None)
    delayed_meta_lics = module.get("delayed_meta_lic", []) if module else []

    # Call the _license_metadata_rule function for each delayed_meta_lic
    for meta_lic in delayed_meta_lics:
        _license_metadata_rule(target, meta_lic, all_modules, all_targets, build_license_metadata_cmd, intermediates_dir, out_dir)

def non_module_license_metadata_rule(target, all_non_modules, all_targets, build_license_metadata_cmd, out_dir):
    """
    License metadata build rule for a non-module target.

    Args:
        target (str): The non-module target for which the license metadata needs to be built.
        all_non_modules (dict): Dictionary representing all non-module targets with their attributes.
        all_targets (list): List of all targets with their attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        out_dir (str): The base output directory for the build.

    Returns:
        None: The function updates the `all_targets` list in-place.
    """
    # Define the directory and metadata path
    dir_path = license_metadata_dir(target, out_dir)
    meta_path = os.path.join(dir_path, f"{os.path.basename(target)}.meta_lic")

    # Retrieve dependencies, notices, paths, and root mappings for the target
    deps = sorted([
        f"{next((t for t in all_targets if t['name'] == dep.split(':')[0]), {}).get('meta_lic', '')}:{':'.join(dep.split(':')[1:])}"
        for dep in all_non_modules[target].get("dependencies", [])
        if dep
    ])
    notices = sorted(all_non_modules[target].get("notices", []))
    path = sorted(all_non_modules[target].get("path", []))
    install_map = all_non_modules[target].get("root_mappings", "")

    # Create the argument file directory
    intermediate_dir = os.path.join(out_dir, "intermediates", "PACKAGING", "notice", os.path.basename(meta_path), "arguments")
    os.makedirs(os.path.dirname(intermediate_dir), exist_ok=True)

    # Create argument file content
    args_to_dump = [
        f"-k {' '.join(sorted(all_non_modules[target].get('license_kinds', [])))}",
        f"-c {' '.join(sorted(all_non_modules[target].get('license_conditions', [])))}",
        f"-n {' '.join(notices)}",
        f"-d {' '.join(deps)}",
        f"-s {' '.join(all_non_modules[target].get('dependencies', []))}",
        f"-m {' '.join(install_map)}",
        f"-t {target}",
        f"-r {' '.join(path)}"
    ]

    # Write the arguments to the file
    with open(intermediate_dir, 'w') as file:
        file.write("\n".join([arg for arg in args_to_dump if arg]))

    # Construct the build command
    build_command = f"out_dir={out_dir} {build_license_metadata_cmd} -mt raw -mc unknown "
    if all_non_modules[target].get("is_container", False):
        build_command += "--is_container "
    build_command += f"-r {' '.join(path)} "
    build_command += f"@{intermediate_dir} -o {meta_path}"

    # Print the build command (for debugging purposes)
    print(f"Executing: {build_command}")

    # Prepare metadata to be added to the list
    target_metadata = {
        "name": target,
        "private_kinds": sorted(all_non_modules[target].get("license_kinds", [])),
        "private_conditions": sorted(all_non_modules[target].get("license_conditions", [])),
        "private_notices": notices,
        "private_notice_deps": deps,
        "private_sources": all_non_modules[target].get("dependencies", []),
        "private_targets": target,
        "private_path": path,
        "private_is_container": all_non_modules[target].get("is_container", False),
        "private_package_name": all_non_modules[target].get("license_package_name", ""),
        "private_install_map": install_map,
        "private_argument_file": intermediate_dir,
        "meta_lic": meta_path  # Add meta_lic path for consistency with module targets
    }

    # Add the metadata entry to the list instead of a dictionary-style update
    all_targets.append(target_metadata)
    print(f"Updated target metadata for: {target}")

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

