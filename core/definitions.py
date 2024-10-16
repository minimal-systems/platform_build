import fnmatch
import os
import platform
import importlib.util
import sys
from pathlib import Path
import subprocess
import shutil
from colorama import Fore, Style, init
from typing import Union
from collections import defaultdict

# Initialize colorama for cross-platform support
init(autoreset=True)

##
## Common build system definitions.  Mostly standard
## commands for building various types of targets, which
## are used by others to construct the final targets.
##

# These are variables we use to collect overall lists
# of things being processed.

# Full paths to all of the documentation
all_docs = {}

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
all_modules = {}

all_make_module_info_json_modules = {}

# the relative paths of the non-module targets in the system.
all_non_modules = {}
non_modules_without_license_metadata = {}

# list of copied targets that need license metadata.
all_copied_targets = {}

# Full paths to targets that should be added to the "make linux"
# set of installed targets.
all_default_installed_modules = {}

# Full path to all asm, C, C++, lex and yacc generated C files.
# These all have an order-only dependency on the copied headers
all_c_cpp_etc_objects = {}

# These files go into the SDK
all_sdk_files = {}

# All findbugs xml files
all_findbug_files = {}

# Packages with certificate violation
certificate_violation_modules = {}

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
all_init_rc_installed_pairs = {}

# List to hold all installed configuration or metadata fragments for a Linux system
all_config_fragments_list = {}

# List to hold all tests that should be skipped in the presubmit check
all_disabled_presubmit_tests = {}

# List to hold all compatibility suites mentioned in local_compatibility_suites in module_info.bp
all_compatibility_suites = {}

# List to hold all compatibility suite files to be distributed
all_compatibility_dist_files = {}

# List to hold all link type entries
all_link_types = {}

# List to hold all exported/imported include entries
exports_list = {}

# List to hold all modules already converted to Soong
soong_already_converted = {}

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
                print(f"  {value}")    # Two spaces for indentation
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
            gcno_file.touch()    # This updates the timestamp of the file
            print(f"Updated timestamp for existing file: {gcno_file}")
        else:
            # Create the gcno file if it does not exist
            gcno_file.touch()
            print(f"Created new GCNO file: {gcno_file}")
    else:
        print(
            f"Source file {source_file} does not exist. GCNO file not touched or created."
        )


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
    if module_file.is_relative_to(
            build_system_dir) or module_file.is_relative_to(out_dir):
        raise RuntimeError(
            "call_my_dir must be called before including other module files.")

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

    if module_file.is_relative_to(
            build_system_dir) or module_file.is_relative_to(out_dir):
        raise RuntimeError(
            "get_module_dir must be called before including other module files."
        )

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
    base_dir = Path(
        base_dir)    # Convert to Path object for easier manipulation

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


def first_module_info_under(base_dir,
                            filename="module_info.bp",
                            min_depth=0,
                            max_depth=None):
    """
    Retrieve a dictionary of all specified files (e.g., `module_info.bp`) in the given directory and its subdirectories.
    The dictionary uses relative paths as keys and absolute paths as values. Allows control over minimum and maximum
    depth to filter results.

    Args:
        base_dir (str or Path): The base directory to search in.
        filename (str): The filename to search for (default is "module_info.bp").
        min_depth (int): Minimum depth of subdirectories to include files (default is 0, which includes all files).
        max_depth (int or None): Maximum depth of subdirectories to include files (default is None, which means no limit).

    Returns:
        dict: Dictionary with relative paths as keys and absolute paths as values for the specified files found
              in the directory and its subdirectories.
    """
    base_dir = Path(
        base_dir).resolve()    # Convert to absolute Path object for consistency

    # Dictionary to store the relative paths as keys and absolute paths as values
    found_files = {}

    # Use rglob to find all instances of the specified filename
    for file in base_dir.rglob(filename):
        # Calculate the depth of the current file relative to the base directory
        relative_depth = len(file.relative_to(base_dir).parts)

        # Check if the file is within the specified depth range
        if relative_depth >= min_depth and (max_depth is None
                                            or relative_depth <= max_depth):
            # Use the relative path as the key and the absolute path as the value
            relative_path = str(file.relative_to(base_dir))
            found_files[relative_path] = str(file)

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


def all_subdir_module_info(module_file,
                           build_system_dir,
                           out_dir,
                           filename="module_info.bp",
                           min_depth=0,
                           max_depth=None):
    """
    Retrieve a dictionary of `module_info.bp` files in subdirectories of the specified module file directory.
    Utilizes `get_module_dir` to get the base directory and allows specifying depth constraints. The resulting
    dictionary uses relative paths as keys and absolute paths as values.

    Args:
        module_file (str or Path): Path to the current module file (e.g., `module_info.bp`).
        build_system_dir (str or Path): Path to the build system directory.
        out_dir (str or Path): Path to the output directory.
        filename (str): The filename to search for (default is "module_info.bp").
        min_depth (int): Minimum depth of subdirectories to include files (default is 0).
        max_depth (int or None): Maximum depth of subdirectories to include files (default is None).

    Returns:
        dict: Dictionary with relative paths as keys and absolute paths as values for the specified `filename`
              files found in the directory and its subdirectories.
    """
    # Get the module directory using `get_module_dir`
    base_dir = Path(get_module_dir(module_file, build_system_dir, out_dir))

    # Dictionary to hold relative paths as keys and absolute paths as values
    found_files = {}

    print(
        f"Searching for {filename} files in {base_dir} and its subdirectories...\n"
    )

    # Use rglob to find all instances of the specified filename
    for file in base_dir.rglob(filename):
        # Calculate the depth of the current file relative to the base directory
        relative_depth = len(file.relative_to(base_dir).parts)

        # Print debugging information
        print(f"Found: {file}, Relative Depth: {relative_depth}")

        # Check if the file is within the specified depth range
        if relative_depth >= min_depth and (max_depth is None
                                            or relative_depth <= max_depth):
            # Store relative path as the key and absolute path as the value
            relative_path = str(file.relative_to(base_dir))
            found_files[relative_path] = str(file)

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
        dict: A dictionary with relative paths as keys and absolute paths as values for all found `module_info.bp` files.
    """
    current_dir = Path(
        current_dir).resolve()    # Resolve the current directory path
    found_files = {
    }    # Dictionary to store relative and absolute paths of the found files

    for directory in directories:
        dir_path = current_dir / directory

        if not dir_path.exists() or not dir_path.is_dir():
            continue

        # Use rglob to recursively search for 'module_info.bp' in the directory and its subdirectories
        for makefile in dir_path.rglob("module_info.bp"):
            # Store the relative path as the key and the absolute path as the value
            relative_path = str(makefile.relative_to(current_dir))
            found_files[relative_path] = str(makefile.resolve())

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
        dict: A dictionary with relative paths as keys and absolute paths as values for all directories
              matching `directory_name` under the given base directories.
    """
    found_directories = {}    # Dictionary to store relative and absolute paths

    for base_directory in base_directories:
        base_directory = Path(
            base_directory).resolve()    # Resolve to absolute path
        if not base_directory.exists() or not base_directory.is_dir():
            continue

        # Use rglob to search for directories with the given name
        for directory in base_directory.rglob(directory_name):
            if directory.is_dir():
                # Store the relative path as the key and the absolute path as the value
                relative_path = str(directory.relative_to(base_directory))
                found_directories[relative_path] = str(directory)

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

    Returns:
        dict: A dictionary with relative paths as keys and absolute paths as values for all directories
              matching `directory_name` under the current directory.
    """
    current_directory = Path(
        os.getcwd()).resolve()    # Resolve the current working directory
    found_directories = {}    # Dictionary to store relative and absolute paths

    # Check if the current directory exists and is indeed a directory
    if not current_directory.exists() or not current_directory.is_dir():
        return found_directories

    # Use rglob to search for directories with the given name under the current directory
    for directory in current_directory.rglob(directory_name):
        if directory.is_dir():
            # Store the relative path as the key and the absolute path as the value
            relative_path = str(directory.relative_to(current_directory))
            found_directories[relative_path] = str(directory)

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
        dict: A dictionary with relative paths as keys and absolute paths as values for all files that match the
              specified pattern under the given directories.
    """
    local_path = Path(
        local_path).resolve()    # Resolve the base path to absolute path
    found_files = {
    }    # Dictionary to store relative and absolute paths of found files

    for base_dir in base_directories:
        base_dir_path = local_path / base_dir    # Combine local path with base directory

        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for files that match the file pattern
        for file_path in base_dir_path.rglob(file_pattern):
            if file_path.is_file():
                # Store the relative path as the key and the absolute path as the value
                relative_path = str(file_path.relative_to(local_path))
                found_files[relative_path] = str(file_path.resolve())

    return found_files


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
        dict: A dictionary with relative paths as keys and absolute paths as values for all files that match the
              specified pattern under the current directory.
    """
    # Get the current working directory and resolve it to an absolute path
    current_directory = Path(os.getcwd()).resolve()
    found_files = {
    }    # Dictionary to store relative and absolute paths of found files

    # Use rglob to search for files that match the file pattern in the current directory and subdirectories
    for file_path in current_directory.rglob(file_pattern):
        if file_path.is_file():
            # Store the relative path as the key and the absolute path as the value
            relative_path = str(file_path.relative_to(current_directory))
            found_files[relative_path] = str(file_path.resolve())

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
        dict: A dictionary with relative paths as keys and absolute paths as values for all `.c` files found
              under the given directories.
    """
    # Get the current working directory and resolve it to an absolute path
    local_path = Path(os.getcwd()).resolve()
    found_files = {
    }    # Dictionary to store relative and absolute paths of found `.c` files

    for base_dir in base_directories:
        base_dir_path = local_path / base_dir

        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for `.c` files in the specified directory and its subdirectories
        for file_path in base_dir_path.rglob("*.c"):
            if file_path.is_file():
                # Store the relative path as the key and the absolute path as the value
                relative_path = str(file_path.relative_to(local_path))
                found_files[relative_path] = str(file_path.resolve())

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
        dict: A dictionary with relative paths as keys and absolute paths as values for all `.c` files found
              under the current directory and its subdirectories.
    """
    # Get the current working directory and resolve it to an absolute path
    current_directory = Path(os.getcwd()).resolve()
    found_files = {
    }    # Dictionary to store relative and absolute paths of found `.c` files

    # Use rglob to search for `.c` files in the current directory and its subdirectories
    for file_path in current_directory.rglob("*.c"):
        if file_path.is_file():
            # Store the relative path as the key and the absolute path as the value
            relative_path = str(file_path.relative_to(current_directory))
            found_files[relative_path] = str(file_path.resolve())

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
        dict: A dictionary with relative paths as keys and absolute paths as values for all `.cpp` files (or files
              with the specified extension) found under the given directories.
    """
    # Get the current working directory and resolve it to an absolute path
    current_directory = Path(os.getcwd()).resolve()
    found_files = {
    }    # Dictionary to store relative and absolute paths of found `.cpp` files

    for base_dir in base_directories:
        base_dir_path = current_directory / base_dir

        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for files with the given extension in the specified directory and its subdirectories
        for file_path in base_dir_path.rglob(f"*{local_cpp_extension}"):
            # Exclude hidden files (those that start with a dot)
            if file_path.is_file() and not file_path.name.startswith('.'):
                # Store the relative path as the key and the absolute path as the value
                relative_path = str(file_path.relative_to(current_directory))
                found_files[relative_path] = str(file_path.resolve())

    return found_files


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
        dict: A dictionary with relative paths as keys and absolute paths as values for all `.cpp` files (or files
              with the specified extension) found under the current directory.
    """
    # Get the current working directory and resolve it to an absolute path
    current_directory = Path(os.getcwd()).resolve()
    found_files = {
    }    # Dictionary to store relative and absolute paths of found `.cpp` files

    # Use rglob to search for files with the given extension in the current directory and its subdirectories
    for file_path in current_directory.rglob(f"*{local_cpp_extension}"):
        # Exclude hidden files (those that start with a dot)
        if file_path.is_file() and not file_path.name.startswith('.'):
            # Store the relative path as the key and the absolute path as the value
            relative_path = str(file_path.relative_to(current_directory))
            found_files[relative_path] = str(file_path.resolve())

    return found_files


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
        dict: A dictionary with relative paths as keys and absolute paths as values for all files matching the
              given pattern under the specified directories.
    """
    found_files = {
    }    # Dictionary to store relative and absolute paths of found files

    for base_dir in base_directories:
        base_dir_path = Path(
            base_dir).resolve()    # Resolve base directory to absolute path
        if not base_dir_path.exists() or not base_dir_path.is_dir():
            continue

        # Use rglob to search for files matching the pattern in the specified directory and subdirectories
        for file_path in base_dir_path.rglob(pattern):
            if file_path.is_file():
                # Calculate the relative path with respect to the base directory
                relative_path = str(file_path.relative_to(base_dir_path))
                # Store the relative path as the key and the absolute path as the value
                found_files[relative_path] = str(file_path.resolve())

    return found_files


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
        dict: A dictionary with relative paths as keys and absolute paths as values for all files matching the pattern,
              excluding files that match `exclude_pattern`.
    """
    current_dir = Path(
        os.getcwd()).resolve() / subdir    # Resolve the subdirectory path
    if not current_dir.exists() or not current_dir.is_dir():
        return {}

    found_files = {
    }    # Dictionary to store relative and absolute paths of found files

    # Search for files in the specified subdirectory that match the pattern
    for file_path in current_dir.glob(pattern):
        if file_path.is_file():
            # Calculate the relative path with respect to the subdirectory
            relative_path = str(file_path.relative_to(current_dir))
            absolute_path = str(file_path.resolve())

            # Check if the file should be excluded based on the exclude_pattern
            if exclude_pattern and fnmatch.fnmatch(
                    str(file_path), str(current_dir / exclude_pattern)):
                continue

            # Store the relative path as the key and the absolute path as the value
            found_files[relative_path] = absolute_path

    return found_files


###########################################################
## Find all of the files in the directory, excluding hidden files
##    src_files = find_subdir_assets(<directory>)
###########################################################


def find_subdir_assets(base_directory=None):
    """
    Find all files in the given directory, excluding hidden files.

    Args:
        base_directory (str or Path): The directory to search in. If None, return an empty dictionary.

    Returns:
        dict: A dictionary with relative paths as keys and absolute paths as values for all non-hidden files
              in the given directory.
    """
    if not base_directory:
        print(
            f"Warning: Empty argument supplied to find_subdir_assets in {os.getcwd()}"
        )
        return {}

    base_dir_path = Path(base_directory).resolve()
    if not base_dir_path.exists() or not base_dir_path.is_dir():
        return {}

    found_files = {
    }    # Dictionary to store relative and absolute paths of found files

    # Find all files, excluding hidden files (those starting with a dot)
    for file_path in base_dir_path.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            # Calculate the relative path with respect to the base directory
            relative_path = str(file_path.relative_to(base_dir_path))
            # Store the relative path as the key and the absolute path as the value
            found_files[relative_path] = str(file_path.resolve())

    return found_files


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
        dict: A dictionary with relative paths (relative to the base directory) as keys and absolute paths as values
              for all files matching the given pattern found in the specified subdirectories.
    """
    base_dir_path = Path(
        base_dir).resolve()    # Resolve the base directory to an absolute path
    found_files = {
    }    # Dictionary to store relative and absolute paths of found files

    for subdir in subdirs:
        # Construct the full directory path
        search_dir = base_dir_path / subdir

        if not search_dir.exists() or not search_dir.is_dir():
            continue

        # Use rglob to find matching files, excluding hidden files and directories
        for file_path in search_dir.rglob(pattern):
            if file_path.is_file() and not file_path.name.startswith('.'):
                # Calculate the relative path with respect to the base directory
                relative_path = str(file_path.relative_to(base_dir_path))
                # Store the relative path as the key and the absolute path as the value
                found_files[relative_path] = str(file_path.resolve())

    return found_files


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
        matched_files = [
            os.path.join(current_dir, f)
            for f in os.listdir(current_dir)
            if os.path.isfile(os.path.join(current_dir, f))
            and f == filename_pattern
        ]

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
        dict: A dictionary with relative paths (relative to the base directory) as keys and formatted strings
              in the format "base_dir:file_path" as values.

    Example:
        base_dir = "/path/to/base"
        filename_pattern = "*.txt"
        subdirs = ["subdir1", "subdir2"]
        result = find_test_data_in_subdirs(base_dir, filename_pattern, subdirs)
        print(result)  # Example output: {'subdir1/file1.txt': '/path/to/base:subdir1/file1.txt', ...}
    """
    base_dir_path = Path(
        base_dir).resolve()    # Resolve the base directory to an absolute path
    result_files = {
    }    # Dictionary to store relative paths and formatted string values

    for subdir in subdirs:
        # Construct the full search directory path
        search_dir = base_dir_path / subdir

        if not search_dir.exists() or not search_dir.is_dir():
            continue

        # Use rglob to find all matching files in subdirectories recursively
        for file_path in search_dir.rglob(filename_pattern):
            if file_path.is_file() and not file_path.name.startswith('.'):
                # Calculate the relative path with respect to the base directory
                relative_path = str(file_path.relative_to(base_dir_path))
                # Format result in the "base_dir:file_path" format
                formatted_value = f"{base_dir}:{relative_path}"
                # Store the relative path as the key and formatted string as the value
                result_files[relative_path] = formatted_value

    return result_files


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
        all_modules (dict): Dictionary of all module attributes, where keys are module names and values are dictionaries of attributes.
        all_modules_attrs (dict of dict): Attributes of each module, where the outer keys are module names,
                                          and the inner keys include 'NOTICE_DEPS' and 'PATH' attributes.

    Returns:
        dict of dict: Updated module attributes with corrected 'NOTICE_DEPS'.
    """
    # Collect all unique module references from 'NOTICE_DEPS' attributes.
    all_module_refs = set()
    for module_name, attrs in all_modules_attrs.items():
        if 'NOTICE_DEPS' in attrs:
            for dep in attrs['NOTICE_DEPS']:
                dep_name = dep.split(":")[
                    0]    # Extract the module name from the dependency string
                all_module_refs.add(dep_name)

    # Build a lookup dictionary for adorned module names.
    lookup = {}
    for ref in sorted(all_module_refs):
        if ref in all_modules_attrs and "PATH" in all_modules_attrs[ref]:
            lookup[ref] = [ref
                          ]    # If the module is already adorned, add it as-is
        else:
            # Find possible adorned versions of the module
            adorned_versions = [
                f"{ref}_32", f"{ref}_64", f"host_cross_{ref}",
                f"host_cross_{ref}_32", f"host_cross_{ref}_64"
            ]
            # Check if these adorned versions exist in all_modules and add them to lookup
            lookup[ref] = [
                mod for mod in adorned_versions if mod in all_modules
            ]

    # Update 'NOTICE_DEPS' for each module using the lookup dictionary
    for module_name, attrs in all_modules_attrs.items():
        notice_deps = attrs.get("NOTICE_DEPS", [])
        updated_deps = set()    # Use a set to avoid duplicates

        for dep in notice_deps:
            dep_name, dep_suffix = dep.split(":", 1) if ":" in dep else (dep,
                                                                         "")
            adorned_names = lookup.get(dep_name, [dep_name])

            # Create new dependencies with adorned names and the original suffix, if any
            for name in adorned_names:
                updated_deps.add(f"{name}:{dep_suffix}" if dep_suffix else name)

        # Update the NOTICE_DEPS attribute for the module
        all_modules_attrs[module_name]["NOTICE_DEPS"] = sorted(updated_deps)

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


targets_missing_license_metadata = {}


def corresponding_license_metadata(targets, all_modules, all_targets):
    """
    Retrieve the license metadata files corresponding to the given targets.

    Args:
        targets (list of str): List of target names.
        all_modules (dict): Dictionary containing module attributes, where keys are module names and values are dictionaries of attributes.
        all_targets (dict): Dictionary containing target attributes, where keys are target names and values are dictionaries of attributes.

    Returns:
        dict: A dictionary where keys are target names and values are the corresponding license metadata paths.
        dict: A dictionary where keys are target names and values are empty strings, representing targets missing license metadata.
    """

    # Dictionary to store license metadata paths for each target
    license_metadata_paths = {
    }    # Format: {target_name: license_metadata_path}
    # Dictionary to track targets that are missing license metadata

    # Iterate through each target to find corresponding metadata
    for target in sorted(targets):
        # Check for META_LIC in all_modules first
        module_info = all_modules.get(target, {})
        meta_lic = module_info.get("META_LIC")

        # If not found in all_modules, check in all_targets
        if not meta_lic:
            target_info = all_targets.get(target, {})
            meta_lic = target_info.get("META_LIC")

        # If META_LIC is found, add to license_metadata_paths dictionary
        if meta_lic and meta_lic != "0p":    # Exclude "0p" entries
            license_metadata_paths[target] = meta_lic
        else:
            # Add the target to the missing metadata dictionary
            targets_missing_license_metadata[target] = ""

    return license_metadata_paths, targets_missing_license_metadata


def declare_copy_target_license_metadata(target, sources, all_copied_targets,
                                         out_dir):
    """
    Record a target copied from another source(s) that will need license metadata.

    Args:
        target (str): The target that will need license metadata.
        sources (list of str): List of source paths for the target.
        all_copied_targets (dict): Dictionary representing copied targets that need license metadata.
                                   Format: {target_name: {"target": target_name, "sources": [source1, source2, ...]}}
        out_dir (str): The base output directory (similar to `OUT_DIR` in the Makefile).

    Returns:
        None: Updates the `all_copied_targets` dictionary in place.
    """
    # Filter sources to only include those within the output directory.
    filtered_sources = [
        source for source in sources if source.startswith(out_dir)
    ]

    # If there are sources within the output directory, proceed to record the target.
    if filtered_sources:
        # Strip whitespace from the target to ensure consistency.
        target = target.strip()

        # Check if the target already exists in the dictionary.
        if target not in all_copied_targets:
            # If the target doesn't exist, add it with the initial sources.
            all_copied_targets[target] = {"target": target, "sources": []}

        # Update the 'sources' field by adding the new sources and keeping them sorted and unique.
        existing_sources = all_copied_targets[target]["sources"]
        all_copied_targets[target]["sources"] = sorted(
            set(existing_sources + filtered_sources))


def _license_metadata_rule(target, meta_lic, all_modules, all_targets,
                           build_license_metadata_cmd, intermediates_dir,
                           out_dir, argument_file_dir):
    """
    Internal function to process license metadata rules for a given target and meta_lic.

    Args:
        target (str): The target for which the license metadata rule applies.
        meta_lic (str): The specific meta license being processed.
        all_modules (dict): Dictionary representing all modules with their attributes.
        all_targets (dict): Dictionary representing all targets with their attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        intermediates_dir (str): Directory path for intermediate files.
        out_dir (str): The base output directory for the build.
        argument_file_dir (str): Directory path for the arguments file.

    Returns:
        tuple: The output and error messages from the build command.
    """
    # Retrieve module attributes
    module = all_modules.get(target)
    if not module:
        return None, f"Module '{target}' not found"

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
    path = module.get("path", [])

    # Ensure license_install_map is a dictionary
    license_install_map = module.get("license_install_map", {})
    install_map = {}
    if not isinstance(license_install_map, dict):
        for entry in license_install_map:
            if ':' in entry:
                src, dest = entry.split(':', 1)
                install_map[src] = dest
            else:
                print(f"Invalid entry in license_install_map: {entry}")
    else:
        install_map = license_install_map

    # Retrieve dependencies and sources
    sources = {
        dep_name: all_modules.get(dep_name, {}).get("installed", dep_name)
        for dep_name in notice_deps
    }
    deps = {
        dep_name: all_targets.get(dep_name, {}).get("meta_lic")
        for dep_name in notice_deps if dep_name in all_targets
    }

    # Prepare license_install_map entries
    for src, dest in install_map.items():
        src_module = all_modules.get(src)
        if src_module:
            source_files = src_module.get("installed", src_module.get("built", src))
            install_map[src] = [f"{file}:{dest}" for file in source_files]

    # Prepare the argument file path
    argument_file = os.path.join(argument_file_dir, "arguments")

    sources_values = [v if isinstance(v, list) else [v] for v in sources.values()]
    flattened_sources = sum(sources_values, [])

    # Prepare argument file contents
    args_to_dump = {
        "-mn": target,
        "-mt": f'"{module_type}"' if module_type else "",
        "-mc": f'"{module_class}"' if module_class else "",
        "-k": f'"{" ".join(sorted(license_kinds))}"' if license_kinds else "",
        "-c": f'"{" ".join(sorted(license_conditions))}"' if license_conditions else "",
        "-n": f'"{" ".join(sorted(notices))}"' if notices else "",
        "-d": f'"{",".join(sorted(deps.values()))}"' if deps else "",
        "-s": f'"{",".join(sorted(flattened_sources))}"' if flattened_sources else "",
        "-m": f'"{",".join(sorted(sum(install_map.values(), [])))}"' if install_map else "",
        "-t": f'"{" ".join(sorted(built))}"' if built else "",
        "-i": f'"{" ".join(sorted(installed))}"' if installed else "",
        "-r": f'"{" ".join(sorted(path))}"' if path else "",
    }
    args_to_dump = {k: v for k, v in args_to_dump.items() if v}
    print(argument_file)
    # Write the arguments to the file
    os.makedirs(os.path.dirname(argument_file), exist_ok=True)
    with open(argument_file, 'w') as file:
        file.write("\n".join([f"{k} {v}" for k, v in args_to_dump.items()]))

    # Read the argument file for the build command
    with open(argument_file, 'r') as file:
        argument_content = " ".join(line.strip() for line in file if line.strip())

    # Update all_targets with metadata
    all_targets[target] = {
        "name": target,
        "meta_lic": meta_lic,
        "private_kinds": sorted(license_kinds),
        "private_conditions": sorted(license_conditions),
        "private_notices": sorted(notices),
        "private_notice_deps": sorted(deps.keys()),
        "private_sources": sorted(sources.keys()),
        "private_targets": sorted(built),
        "private_installed": sorted(installed),
        "private_path": sorted(path),
        "private_is_container": is_container,
        "private_package_name": license_package_name,
        "private_install_map": sorted(install_map.keys()),
        "private_module_name": target,
        "private_module_type": module_type,
        "private_module_class": module_class,
        "private_argument_file": argument_file,
    }

    # Construct the build command
    build_command = f"OUT_DIR={out_dir} {build_license_metadata_cmd} "
    if is_container:
        build_command += "--is_container "
    build_command += f"-p '{license_package_name}' {argument_content} -o {meta_lic}"

    # Execute the build command
    try:
        result = subprocess.run(build_command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr


def license_metadata_rule(
    target: str,
    all_modules: dict,
    all_targets: dict,
    build_license_metadata_cmd: str,
    intermediates_dir: str,
    out_dir: str,
    argument_file_dir: str = None
):
    """
    License metadata build rule for the given target.

    Args:
        target (str): The target for which license metadata needs to be built.
        all_modules (dict): Dictionary of all module attributes.
        all_targets (dict): Dictionary of all target attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        intermediates_dir (str): Directory path for intermediate files.
        out_dir (str): The base output directory for the build.
        argument_file_dir (str): Optional path to the argument file directory.

    Returns:
        None: Updates the `all_targets` dictionary in place.
    """
    # Use the provided argument file directory or construct it from arguments
    argument_file_dir = argument_file_dir or os.path.join(
        out_dir, "intermediates", "PACKAGING", "notice", target
    )

    # Get delayed meta licenses from the module
    module = all_modules.get(target, {})
    delayed_meta_lics = module.get("delayed_meta_lic", [])

    # Process each delayed meta license
    for meta_lic in delayed_meta_lics:
        _license_metadata_rule(
            target, meta_lic, all_modules, all_targets,
            build_license_metadata_cmd, intermediates_dir,
            out_dir, argument_file_dir
        )

def non_module_license_metadata_rule(target, all_non_modules, all_targets,
                                     build_license_metadata_cmd, out_dir):
    """
    License metadata build rule for a non-module target.

    Args:
        target (str): The non-module target for which the license metadata needs to be built.
        all_non_modules (dict): Dictionary representing all non-module targets with their attributes.
                                Keys are non-module target names and values are dictionaries of attributes.
        all_targets (dict): Dictionary representing all targets with their attributes.
                            Keys are target names and values are dictionaries of attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        out_dir (str): The base output directory for the build.

    Returns:
        None: The function updates the `all_targets` dictionary in place.
    """
    # Retrieve the non-module target dictionary from all_non_modules using the target as the key
    non_module_target = all_non_modules.get(target)
    if not non_module_target:
        print(
            f"Non-module target '{target}' not found in all_non_modules dictionary."
        )
        return

    # Define the directory and metadata path
    dir_path = license_metadata_dir(target, out_dir)
    meta_path = os.path.join(dir_path, f"{os.path.basename(target)}.meta_lic")

    # Retrieve dependencies, notices, paths, and root mappings for the target
    deps = sorted([
        f"{all_targets.get(dep, {}).get('meta_lic', '')}:{':'.join(dep.split(':')[1:])}"
        for dep in non_module_target.get("dependencies", [])
        if dep
    ])
    notices = sorted(non_module_target.get("notices", []))
    path = sorted(non_module_target.get("path", []))
    install_map = non_module_target.get("root_mappings", "")

    # Create the argument file directory
    intermediate_dir = os.path.join(out_dir, "intermediates",
                                    "PACKAGING", "notice",
                                    os.path.basename(meta_path), "arguments")
    os.makedirs(os.path.dirname(intermediate_dir), exist_ok=True)

    # Create argument file content
    args_to_dump = {
        "-k":
            " ".join(sorted(non_module_target.get("license_kinds", []))),
        "-c":
            " ".join(sorted(non_module_target.get("license_conditions", []))),
        "-n":
            " ".join(notices),
        "-d":
            " ".join(deps),
        "-s":
            " ".join(non_module_target.get("dependencies", [])),
        "-m":
            " ".join(install_map)
            if isinstance(install_map, list) else install_map,
        "-t":
            target,
        "-r":
            " ".join(path)
    }

    # Remove empty arguments
    args_to_dump = {k: v for k, v in args_to_dump.items() if v}

    # Write the arguments to the file
    with open(intermediate_dir, 'w') as file:
        file.write("\n".join([f"{k} {v}" for k, v in args_to_dump.items()]))

    # Construct the build command
    build_command = f"OUT_DIR={out_dir} {build_license_metadata_cmd} -mt raw -mc unknown "
    if non_module_target.get("is_container", False):
        build_command += "--is_container "
    build_command += f"-r {' '.join(path)} "
    build_command += f"@{intermediate_dir} -o {meta_path}"

    # Update the all_targets dictionary with metadata
    all_targets[target] = {
        "name":
            target,
        "private_kinds":
            sorted(non_module_target.get("license_kinds", [])),
        "private_conditions":
            sorted(non_module_target.get("license_conditions", [])),
        "private_notices":
            notices,
        "private_notice_deps":
            deps,
        "private_sources":
            non_module_target.get("dependencies", []),
        "private_targets": [target],
        "private_path":
            path,
        "private_is_container":
            non_module_target.get("is_container", False),
        "private_package_name":
            non_module_target.get("license_package_name", ""),
        "private_install_map":
            install_map,
        "private_argument_file":
            intermediate_dir
    }

    print(f"Updated target metadata for: {target}")


def record_missing_non_module_dependencies(target, all_non_modules, all_targets,
                                           missing_dependencies):
    """
    Record missing dependencies for a non-module target.

    Args:
        target (str): The non-module target for which the dependencies need to be checked.
        all_non_modules (dict): Dictionary of all non-module targets with their attributes.
        all_targets (dict): Dictionary of all targets with their attributes.
        missing_dependencies (list): List to accumulate non-modules without license metadata.

    Returns:
        None: The function updates the `missing_dependencies` list in-place.
    """
    # Check if `all_non_modules` and `all_targets` are dictionaries
    if not isinstance(all_non_modules, dict) or not isinstance(
            all_targets, dict):
        print(
            f"Error: `all_non_modules` or `all_targets` is not a dictionary. Received: {all_non_modules}, {all_targets}"
        )
        return

    # Retrieve the dictionary entry for the given non-module target from `all_non_modules`
    non_module_target = all_non_modules.get(target, {})

    # Get dependencies for the non-module target
    dependencies = non_module_target.get("dependencies", [])

    # Iterate over each dependency to check if it has metadata
    for dep in dependencies:
        # Check if the dependency exists in `all_targets` and has `meta_lic` metadata
        dep_target = all_targets.get(dep)
        if dep_target is None or "meta_lic" not in dep_target:
            # Record the dependency if it does not have license metadata
            missing_dependencies.append(dep)


def copied_target_license_metadata_rule(
        target_name: str,
        all_targets: dict,
        all_copied_targets: dict,
        copy_license_metadata_cmd: str,
        out_dir: str,
        intermediates_base_dir: str) -> None:
    """
    Wrapper function to check if the given target's `meta_lic` attribute is defined.
    If not, calls `_copied_target_license_metadata_rule` for further processing.

    Args:
        target_name (str): The name of the target to check.
        all_targets (dict): Dictionary of target attributes with target names as keys.
        all_copied_targets (dict): Dictionary of copied target attributes.
        copy_license_metadata_cmd (str): Command for copying license metadata.
        out_dir (str): Base output directory for the build.
        intermediates_base_dir (str): Base directory for intermediate files.

    Returns:
        None
    """
    target = all_targets.get(target_name)
    if not target:
        print(f"{Fore.RED}Target '{target_name}' not found in all_targets.{Style.RESET_ALL}")
        return

    if not target.get("meta_lic"):
        print(f"{Fore.CYAN}Calling _copied_target_license_metadata_rule for '{target_name}'...{Style.RESET_ALL}")
        _copied_target_license_metadata_rule(
            target_name,
            all_targets,
            all_copied_targets,
            copy_license_metadata_cmd,
            out_dir,
            intermediates_base_dir
        )
    else:
        print(f"{Fore.YELLOW}'meta_lic' already defined for '{target_name}', no action required.{Style.RESET_ALL}")


def _copied_target_license_metadata_rule(
        target_name: str,
        all_targets: dict,
        all_copied_targets: dict,
        copy_license_metadata_cmd: str,
        out_dir: str,
        intermediates_base_dir: str) -> None:
    """
    License metadata build rule for copied targets.

    Args:
        target_name (str): The name of the target to check and update.
        all_targets (dict): Dictionary where keys are target names and values are dictionaries with attributes.
        all_copied_targets (dict): Dictionary of copied target attributes with sources.
        copy_license_metadata_cmd (str): Command for copying license metadata.
        out_dir (str): Base output directory for the build.
        intermediates_base_dir (str): Base directory for intermediate files.

    Returns:
        None
    """
    target = all_targets.get(target_name)
    if not target:
        print(f"{Fore.RED}Target '{target_name}' not found in all_targets.{Style.RESET_ALL}")
        return

    packaging_dir = os.path.join(intermediates_base_dir, "PACKAGING", "copynotice", target_name)
    meta_lic_file = os.path.join(packaging_dir, f"{target_name}.meta_lic")
    dep_metadata = None

    target["meta_lic"] = meta_lic_file

    copied_target = all_copied_targets.get(target_name)
    if not copied_target:
        print(f"{Fore.RED}Copied target '{target_name}' not found in all_copied_targets.{Style.RESET_ALL}")
        return

    sources = copied_target.get("sources", [])
    if not sources:
        print(f"{Fore.RED}No sources found for copied target '{target_name}'.{Style.RESET_ALL}")
        return

    for source_name in sources:
        source_target = all_targets.get(source_name)
        source_meta = source_target.get("meta_lic") if source_target else None

        if dep_metadata is None:
            dep_metadata = source_meta
        elif dep_metadata != source_meta:
            raise ValueError(
                f"Cannot copy target '{target_name}' from multiple modules: {dep_metadata} and {source_meta}"
            )

    if not dep_metadata:
        raise ValueError(
            f"Cannot copy target '{target_name}' from unknown module: {sources}"
        )

    argument_file_path = os.path.join(packaging_dir, "arguments")
    os.makedirs(os.path.dirname(argument_file_path), exist_ok=True)

    args_to_dump = [
        f"-i {target_name}",
        f"-s {' '.join(sources)}",
        f"-d {dep_metadata}"
    ]
    with open(argument_file_path, 'w') as file:
        file.write("\n".join(args_to_dump))

    build_command = (
        f"OUT_DIR={out_dir} {copy_license_metadata_cmd} "
        f"@{argument_file_path} -o {meta_lic_file}"
    )

    # Uncomment to execute the command if needed:
    # subprocess.run(build_command, shell=True, check=True, capture_output=True, text=True)

    target.update({
        "private_dest_target": target_name,
        "private_source_targets": sources,
        "private_source_metadata": dep_metadata,
        "private_argument_file": argument_file_path
    })

    # print(f"Updated target metadata for copied target: {target_name}")

def declare_license_metadata(
        target, license_kinds, license_conditions, notices, package_name, project_path, all_non_modules, all_targets, out_dir):
    """
    Declare the license metadata for a non-module target.

    Args:
        target (str): The non-module target for which the license metadata is being declared.
        license_kinds (str): License kinds (e.g., 'SPDX-license-identifier-Apache-2.0').
        license_conditions (str): License conditions (e.g., 'notice', 'by_exception_only').
        notices (str): License text filenames (notices).
        package_name (str): The package name associated with the license metadata.
        project_path (str): The project path associated with the target.
        all_non_modules (dict): Dictionary representing all non-module attributes.
        all_targets (dict): Dictionary representing all target attributes.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the dictionaries `all_non_modules` and `all_targets` in place.
    """
    # Strip and normalize the target name, replacing '//' with '/'
    target_name = target.strip().replace("//", "/")

    # Initialize the non-module target if not present
    if target_name not in all_non_modules:
        all_non_modules[target_name] = {}

    # Add the target to the list of non-modules
    all_non_modules.setdefault('all_non_modules', set()).add(target_name)

    # Define the path for license metadata
    meta_lic_dir = f"{out_dir}/META/lic/{target_name}"
    meta_lic_path = f"{meta_lic_dir}/{target_name}.meta_lic"

    # Store the META_LIC path in `all_targets`
    if target_name not in all_targets:
        all_targets[target_name] = {}

    all_targets[target_name]["META_LIC"] = meta_lic_path

    # Store the license-related metadata in `all_non_modules`
    all_non_modules[target_name]["license_kinds"] = license_kinds.strip().split()
    all_non_modules[target_name]["license_conditions"] = license_conditions.strip().split()
    all_non_modules[target_name]["notices"] = notices.strip().split()
    all_non_modules[target_name]["license_package_name"] = package_name.strip()
    all_non_modules[target_name]["path"] = project_path.strip()

    print(f"Declared license metadata for non-module target: {target_name}")

def declare_copy_files_license_metadata(
        project, suffix, license_kinds, license_conditions, notices, package_name, product_copy_files, all_non_modules, all_targets, out_dir):
    """
    Declare that non-module targets copied from a project have specific license metadata.

    Args:
        project (str): The project path from which the files are copied (e.g., "vendor/config").
        suffix (str): Optional suffix to filter specific files (e.g., ".conf").
        license_kinds (str): License kinds (e.g., "SPDX-license-identifier-Apache-2.0").
        license_conditions (str): License conditions (e.g., "notice", "by_exception_only").
        notices (str): License text filenames (notices).
        package_name (str): The package name associated with the license metadata.
        product_copy_files (list of str): List of files copied to the product, with paths formatted as "source:destination".
        all_non_modules (dict): Dictionary representing all non-module attributes.
        all_targets (dict): Dictionary representing all target attributes.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the dictionaries `all_non_modules` and `all_targets` in place.
    """
    # Strip and format the project name to match the convention used in product_copy_files
    project = project.strip()

    # Iterate through each copied file pair in `product_copy_files`
    for pair in product_copy_files:
        # Check if the source file matches the project and suffix pattern
        source, destination = pair.split(':')
        if source.startswith(project) and source.endswith(suffix):
            # Construct the full destination path
            destination_path = f"{out_dir}/{destination.lstrip('/')}"

            # Declare license metadata for this non-module target
            declare_license_metadata(
                target=destination_path,
                license_kinds=license_kinds,
                license_conditions=license_conditions,
                notices=notices,
                package_name=package_name,
                project_path=project,
                all_non_modules=all_non_modules,
                all_targets=all_targets,
                out_dir=out_dir
            )

    print(f"Declared license metadata for copied files from project: {project}")


def declare_container_license_metadata(
        target, license_kinds, license_conditions, notices, package_name, project_path, all_non_modules, all_targets, out_dir):
    """
    Declare the license metadata for a non-module container-type target.

    Container-type targets are targets like `.zip` files that merely aggregate other files.

    Args:
        target (str): The non-module container target for which license metadata is being declared.
        license_kinds (str): License kinds (e.g., "SPDX-license-identifier-Apache-2.0").
        license_conditions (str): License conditions (e.g., "notice", "by_exception_only").
        notices (str): License text filenames (notices).
        package_name (str): The package name associated with the license metadata.
        project_path (str): The project path for the non-module container target.
        all_non_modules (dict): Dictionary representing all non-module attributes.
        all_targets (dict): Dictionary representing all target attributes.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the dictionaries `all_non_modules` and `all_targets` in place.
    """
    # Format and clean up the target path
    target_path = target.replace("//", "/").strip()

    # Add the target to the non-modules dictionary
    all_non_modules[target_path] = all_non_modules.get(target_path, {})

    # Define the META_LIC path for the target
    meta_lic_path = f"{out_dir}/META/lic/{target_path}.meta_lic"
    all_targets[target_path] = all_targets.get(target_path, {})
    all_targets[target_path]["META_LIC"] = meta_lic_path

    # Update the license metadata attributes for the non-module container target
    all_non_modules[target_path]["license_kinds"] = license_kinds.strip()
    all_non_modules[target_path]["license_conditions"] = license_conditions.strip()
    all_non_modules[target_path]["notices"] = notices.strip()
    all_non_modules[target_path]["license_package_name"] = package_name.strip()
    all_non_modules[target_path]["path"] = project_path.strip()
    all_non_modules[target_path]["is_container"] = True

    # Print confirmation of the declared license metadata
    print(f"Declared container license metadata for target: {target_path}")


def declare_0p_target(target, all_0p_targets):
    """
    Declare that a non-module target is a non-copyrightable file.

    For example, an information-only file that merely lists other files.

    Args:
        target (str): The non-module target to be marked as a non-copyrightable file.
        all_0p_targets (dict): Dictionary to store all non-copyrightable targets.

    Returns:
        None: Updates the `all_0p_targets` dictionary in place.
    """
    # Format and clean up the target path
    target_path = target.replace("//", "/").strip()

    # Add the target to the non-copyrightable targets dictionary
    all_0p_targets[target_path] = True

    # Print confirmation of the declared non-copyrightable target
    print(f"Declared non-copyrightable target: {target_path}")

def declare_1p_target(target, project_path, all_non_modules, all_targets, out_dir):
    """
    Declare that a non-module target has a first-party license (e.g., Linux Apache 2.0).

    Args:
        target (str): The non-module target to be declared.
        project_path (str): The project path associated with the target.
        all_non_modules (dict): Dictionary to store all non-module attributes.
        all_targets (dict): Dictionary to store all targets and their attributes.
        out_dir (str): The base output directory.

    Returns:
        None: Updates `all_non_modules` and `all_targets` dictionaries in place.
    """
    # Define first-party license attributes
    license_kinds = "SPDX-license-identifier-Apache-2.0"
    license_conditions = "notice"
    notices = "build/soong/licenses/LICENSE"
    package_name = "Linux"

    # Call the existing declare_license_metadata function with the first-party license attributes
    declare_license_metadata(
        target=target,
        license_kinds=license_kinds,
        license_conditions=license_conditions,
        notices=notices,
        package_name=package_name,
        project_path=project_path,
        all_non_modules=all_non_modules,
        all_targets=all_targets,
        out_dir=out_dir
    )

# Define the declare_1p_copy_files function using the earlier provided logic
def declare_1p_copy_files(project_path, suffix, product_copy_files, all_non_modules, all_targets, out_dir):
    """
    Declare that non-module targets copied from a project path (and optionally ending in a suffix) have first-party licenses.

    Args:
        project_path (str): The base project path to filter files from.
        suffix (str): Optional suffix to match specific files (e.g., '.so').
        product_copy_files (list): List of product copy files, where each element is a tuple (src_path, dest_path).
        all_non_modules (dict): Dictionary representing all non-module attributes.
        all_targets (dict): Dictionary representing all target attributes.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the dictionaries `all_non_modules` and `all_targets` in place.
    """
    # Iterate over product copy files that match the project path and suffix
    for src, dest in product_copy_files:
        if src.startswith(project_path) and (suffix == "" or src.endswith(suffix)):
            # Construct the full target path by joining output directory with destination path
            target = f"{out_dir}/{dest.lstrip('/')}"

            # Declare the target as first-party licensed using `declare_1p_target`
            declare_1p_target(target, project_path, all_non_modules, all_targets, out_dir)
            print(f"Declared 1P copy file target: {target} from project path: {project_path}")


def declare_1p_container(target, project_path, all_non_modules, all_targets, out_dir):
    """
    Declare a non-module container-type target to have a first-party license (Linux Apache 2.0).

    Container-type targets are targets like .zip files that merely aggregate other files.

    Args:
        target (str): The non-module container target for which the license metadata is being declared.
        project_path (str): The project path associated with the target.
        all_non_modules (dict): Dictionary representing all non-module attributes.
        all_targets (dict): Dictionary representing all target attributes.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the dictionaries `all_non_modules` and `all_targets` in place.
    """
    # Define first-party license attributes
    license_kinds = "SPDX-license-identifier-Apache-2.0"
    license_conditions = "notice"
    notices = "build/soong/licenses/LICENSE"
    package_name = "Linux"

    # Use the existing `declare_container_license_metadata` function to declare container target attributes
    declare_container_license_metadata(
        target,
        license_kinds,
        license_conditions,
        notices,
        package_name,
        project_path,
        all_non_modules,
        all_targets,
        out_dir,
    )

    print(f"Declared 1P container license metadata for target: {target} with project path: {project_path}")

def declare_license_deps(target, deps, all_non_modules, all_targets, out_dir):
    """
    Declare license dependencies with optional colon-separated annotations for a non-module target.

    Args:
        target (str): The non-module target for which the license dependencies are being declared.
        deps (str): Space-separated list of dependencies with optional colon-separated annotations.
        all_non_modules (dict): Dictionary representing all non-module attributes.
        all_targets (dict): Dictionary representing all target attributes.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the dictionaries `all_non_modules` and `all_targets` in place.
    """
    # Normalize target name
    target_name = target.strip().replace("//", "/")

    # Initialize non-module target and ensure it's registered
    non_module = all_non_modules.setdefault(target_name, {})
    all_non_modules.setdefault("all_non_modules", set()).add(target_name)

    # Define and set the META_LIC path for the target
    meta_lic_path = f"{out_dir}/META/lic/{target_name}/{target_name}.meta_lic"
    all_targets.setdefault(target_name, {})["META_LIC"] = meta_lic_path

    # Update dependencies for the target
    non_module["dependencies"] = sorted(set(non_module.get("dependencies", []) + deps.split()))

    print(f"Declared license dependencies for non-module target: {target_name}")


def declare_container_license_deps(target, dependencies, root_mappings, all_non_modules, all_targets, out_dir):
    """
    Declare license dependencies with optional colon-separated annotations for a non-module container-type target.

    Container-type targets are targets like .zip files that aggregate other files.

    Args:
        target (str): The non-module container target for which the license dependencies are being declared.
        dependencies (str): Space-separated list of dependencies with optional colon-separated annotations.
        root_mappings (str): Space-separated root mappings in the form of source:target.
        all_non_modules (dict): Dictionary representing all non-module attributes.
        all_targets (dict): Dictionary representing all target attributes.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the dictionaries `all_non_modules` and `all_targets` in place.
    """
    # Normalize target name
    target_name = target.strip().replace("//", "/")

    # Initialize non-module container target and ensure it's registered
    non_module = all_non_modules.setdefault(target_name, {})
    all_non_modules.setdefault("all_non_modules", set()).add(target_name)

    # Define and set the META_LIC path for the target
    meta_lic_path = f"{out_dir}/META/lic/{target_name}/{target_name}.meta_lic"
    all_targets.setdefault(target_name, {})["META_LIC"] = meta_lic_path

    # Update dependencies and root mappings for the container target
    non_module["dependencies"] = sorted(set(non_module.get("dependencies", []) + dependencies.split()))
    non_module["is_container"] = True
    non_module["root_mappings"] = sorted(set(non_module.get("root_mappings", []) + root_mappings.split()))

    print(f"Declared container license dependencies for non-module target: {target_name}")


def report_missing_licenses_rule(non_modules_without_metadata, targets_missing_metadata, product_copy_files, product_out_dir):
    """
    Report targets and copied files with no license metadata.

    Args:
        non_modules_without_metadata (list): List of non-module targets without license metadata.
        targets_missing_metadata (list): List of targets missing license metadata.
        product_copy_files (list): List of product copy files, where each element is a tuple (src_path, dest_path).
        product_out_dir (str): Base output directory for product files.

    Returns:
        None: Prints a report of targets and copied files without license metadata.
    """
    # Combine non-modules and targets missing metadata into a single set
    private_non_modules = sorted(set(non_modules_without_metadata + targets_missing_metadata))

    # Create a list of copied files missing metadata based on private_non_modules
    private_copied_files = sorted(
        product_out_dir + "/" + dest.lstrip("/")
        for src, dest in product_copy_files
        if (product_out_dir + "/" + dest.lstrip("/")) in private_non_modules
    )

    # Report the number of targets without license metadata
    print(f"Reporting {len(private_non_modules)} targets without license metadata")

    # Report each non-module without metadata
    for target in private_non_modules:
        if not os.path.islink(target):  # Skip symbolic links
            print(f"No license metadata for {target}", file=sys.stderr)

    # Report each copied file without metadata
    for target in private_copied_files:
        if not os.path.islink(target):  # Skip symbolic links
            print(f"No license metadata for copied file {target}", file=sys.stderr)

    # Print summary of missing metadata
    print(f"{len(private_non_modules)} targets missing license metadata", file=sys.stderr)

def all_license_metadata(all_non_modules, all_targets, all_modules):
    """
    Returns the unique list of license metadata files, ensuring only 'meta_lic' paths are captured.

    Args:
        all_non_modules (dict): Dictionary of non-module attributes.
        all_targets (dict): Dictionary of target attributes.
        all_modules (dict): Dictionary of module attributes.

    Returns:
        list: Sorted list of unique 'meta_lic' file paths.
    """
    # Collect meta_lic paths from non-modules that exist in all_targets
    non_module_meta_lics = [
        os.path.join(target_data["META_LIC"])
        for target, target_data in all_non_modules.items()
        if target in all_targets and "META_LIC" in all_targets[target]
    ]

    # Collect meta_lic paths from modules
    module_meta_lics = [
        os.path.join(module_data["META_LIC"])
        for module_data in all_modules.values()
        if "META_LIC" in module_data
    ]

    # Combine the lists, remove duplicates, and sort
    unique_meta_lics = sorted(set(non_module_meta_lics + module_meta_lics))

    # Log the result
    print(f"Found {len(unique_meta_lics)} 'meta_lic' files.")
    return unique_meta_lics



def report_all_notice_library_names_rule(all_non_modules, all_targets, all_modules, out_dir, compliance_notice_shipped_libs):
    """
    Report all library names used in any notice files based on license metadata.

    Args:
        all_non_modules (dict): Dictionary of all non-module attributes.
        all_targets (dict): Dictionary of all target attributes.
        all_modules (dict): Dictionary of all module attributes.
        out_dir (str): Base output directory for the build.
        compliance_notice_shipped_libs (str): Command or path to compliance notice shipped libraries executable.

    Returns:
        None: Reports library names used in notice files and prints results to the console.
    """
    # Get the list of all license metadata files using the `all_license_metadata` function
    all_meta_lic_files = all_license_metadata(all_non_modules, all_targets, all_modules)

    # Define the path for the list file to store all meta_lic file paths
    common_license_metadata_dir = os.path.join(out_dir, "META", "lic", "COMMON")
    private_list_file = os.path.join(common_license_metadata_dir, "filelist")

    # Print the number of license metadata files found
    print(f"Reporting notice library names for at least {len(all_meta_lic_files)} license metadata files")

    # Remove existing list file if it exists
    if os.path.exists(private_list_file):
        os.remove(private_list_file)

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(private_list_file), exist_ok=True)

    # Write all license metadata file paths to the private list file
    with open(private_list_file, 'w') as file:
        for meta_lic in all_meta_lic_files:
            file.write(f'"{meta_lic}"\n')

    # Define the command to run using the list of meta_lic files
    build_command = f"OUT_DIR={out_dir} {compliance_notice_shipped_libs} @{private_list_file}"

    # Execute the build command and capture the output
    try:
        result = subprocess.run(build_command, shell=True, check=True, capture_output=True, text=True)
        print(f"Command output:\n{result.stdout}")
        if result.stderr:
            print(f"Command errors:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute compliance notice shipped libraries command.\nError: {e.stderr}")


def build_all_license_metadata(all_non_modules, all_targets, all_modules, out_dir):
    """
    Builds all license metadata files by creating dummy files to simulate the build process.

    Args:
        all_non_modules (dict): Dictionary of all non-module attributes.
        all_targets (dict): Dictionary of all target attributes.
        all_modules (dict): Dictionary of all module attributes.
        out_dir (str): Output directory where metadata files will be created.
    """
    all_metadata_files = all_license_metadata(all_non_modules, all_targets, all_modules)

    if not all_metadata_files:
        print("No valid license metadata files found to build.")
        return

    # Ensure the output directory exists
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Simulate the build process by creating dummy files
    for metadata_file in all_metadata_files:
        metadata_path = Path(out_dir) / metadata_file
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w') as f:
            f.write(f"Simulated content for {metadata_file}")
        print(f"Built license metadata for: {metadata_path}")

    print(f"Built all {len(all_metadata_files)} license metadata files.")

def build_license_metadata(all_non_modules: dict,
                           all_targets: dict,
                           all_modules: dict,
                           all_copied_targets: dict,
                           copy_license_metadata_cmd: str,
                           out_dir: str) -> list:
    """
    Builds all license metadata for modules, non-modules, and copied targets.

    Args:
        all_non_modules (dict): Dictionary of non-module targets.
        all_targets (dict): Dictionary of all targets with attributes.
        all_modules (dict): Dictionary of module attributes.
        all_copied_targets (dict): Dictionary of copied targets.
        copy_license_metadata_cmd (str): Command for copying license metadata.
        out_dir (str): Output directory for license metadata.

    Returns:
        list: List of paths to all built license metadata files.
    """

    # Collect all built metadata paths
    built_metadata_files = []

    # Process non-module targets
    for target_name, target_attributes in all_non_modules.items():
        # Ensure required arguments are passed correctly to the rule
        non_module_license_metadata_rule(
            target_name, all_non_modules, all_targets, copy_license_metadata_cmd, out_dir
        )

        # Collect 'meta_lic' path if available
        meta_lic_path = all_targets.get(target_name, {}).get("meta_lic")
        if meta_lic_path:
            built_metadata_files.append(meta_lic_path)

    # Process copied targets
    for target_name, target_attributes in all_copied_targets.items():
        copied_target_license_metadata_rule(
            target_name, all_targets, all_copied_targets,
            copy_license_metadata_cmd, out_dir
        )

        # Collect 'meta_lic' path if available
        meta_lic_path = all_targets.get(target_name, {}).get("meta_lic")
        if meta_lic_path:
            built_metadata_files.append(meta_lic_path)

    # Process modules
    for module_name, module_attributes in all_modules.items():
        license_metadata_rule(module_name, all_modules, all_targets, out_dir)

        # Collect 'meta_lic' path if available
        meta_lic_path = all_targets.get(module_name, {}).get("meta_lic")
        if meta_lic_path:
            built_metadata_files.append(meta_lic_path)

    print(f"Built {len(built_metadata_files)} 'meta_lic' files.")
    return built_metadata_files

common_module_classes = ["TARGET_NOTICE_FILES", "HOST_NOTICE_FILES"]
per_arch_module_classes = [
    "SHARED_LIBRARIES", "STATIC_LIBRARIES", "EXECUTABLES", "GYP",
    "NATIVE_TESTS", "HEADER_LIBRARIES", "RLIB_LIBRARIES", "DYLIB_LIBRARIES"
]

def find_idf_prefix(target_type, host_cross_os):
    """
    Determine the prefix for the intermediate directory based on the target type and host cross OS.

    Args:
        target_type (str): Target type (e.g., HOST, HOST_CROSS, TARGET).
        host_cross_os (bool): Indicates if the target is for host cross OS.

    Returns:
        str: Prefix for the intermediate directory.
    """
    if host_cross_os:
        return f"host_cross_{target_type.lower()}"
    return target_type.lower() if target_type else "target"

def intermediates_dir_for(target_class, target_name, target_type=None,
                          force_common=False, second_arch=False, host_cross_os=False,
                          target_product_out=None):
    """
    Calculate the intermediate directory for a given target.

    Args:
        target_class (str): Class of the target (e.g., "APPS").
        target_name (str): Name of the target (e.g., "NotePad").
        target_type (str): Type of the target (e.g., "HOST", "TARGET"). Default is None.
        force_common (bool): If True, force the intermediate directory to be COMMON.
        second_arch (bool): If True, use the 2nd architecture prefix.
        host_cross_os (bool): If True, force intermediates to be for host cross OS.
        target_product_out (str): Optional path to the product output directory.

    Returns:
        str: The calculated path to the intermediate directory.
    Raises:
        ValueError: If target class or target name is not provided.
    """
    if not target_class:
        raise ValueError("Class not defined in call to intermediates_dir_for.")
    if not target_name:
        raise ValueError("Name not defined in call to intermediates_dir_for.")

    # Use the provided product output directory or default to the current working directory
    base_out_dir = target_product_out or os.getcwd()

    # Calculate the prefix based on target type and host cross OS
    prefix = find_idf_prefix(target_type, host_cross_os)

    # Determine the 2nd arch prefix if applicable
    second_arch_prefix = "2nd_arch_" if second_arch else ""

    # Calculate the base intermediate directory
    if force_common or f"{prefix}_{target_class}" in common_module_classes:
        intermediate_base = f"{prefix}_out_common_intermediates"
    elif target_class in per_arch_module_classes:
        intermediate_base = f"{second_arch_prefix}{prefix}_out_intermediates"
    else:
        intermediate_base = f"{prefix}_out_intermediates"

    # Join paths correctly and return the final directory
    return os.path.join(base_out_dir, "obj", target_class, f"{target_name}_intermediates")

def local_intermediates_dir(local_module_class, local_module, local_is_host_module=False,
                            force_common=False, second_arch=False, host_cross_os=False,
                            target_product_out=None):
    """
    Determine the intermediates directory based on the provided module class and name.

    Args:
        local_module_class (str): Class of the local module (e.g., "APPS").
        local_module (str): Name of the local module (e.g., "NotePad").
        local_is_host_module (bool): If True, treat it as a host module.
        force_common (bool): If True, force the intermediates to be COMMON.
        second_arch (bool): If True, use the 2nd architecture prefix.
        host_cross_os (bool): If True, force intermediates to be for the host cross OS.
        target_product_out (str): Optional path to the product output directory.

    Returns:
        str: The calculated path to the intermediates directory.
    Raises:
        ValueError: If required parameters are not provided.
    """
    if not local_module_class:
        raise ValueError("LOCAL_MODULE_CLASS not defined before call to local_intermediates_dir.")
    if not local_module:
        raise ValueError("LOCAL_MODULE not defined before call to local_intermediates_dir.")

    # Determine the target type based on whether it's a host module
    target_type = "HOST" if local_is_host_module else "TARGET"

    # Call intermediates_dir_for with the resolved parameters
    return intermediates_dir_for(
        target_class=local_module_class,
        target_name=local_module,
        target_type=target_type,
        force_common=force_common,
        second_arch=second_arch,
        host_cross_os=host_cross_os,
        target_product_out=target_product_out
    )

def local_meta_intermediates_dir(local_module_class, local_module, local_is_host_module=False,
                                 force_common=False, second_arch=False, host_cross_os=False,
                                 target_product_out=None):
    """
    Calculate the meta intermediates directory for a local module.

    Args:
        local_module_class (str): Class of the local module (e.g., "APPS").
        local_module (str): Name of the local module (e.g., "NotePad").
        local_is_host_module (bool): If True, treat it as a host module.
        force_common (bool): If True, force the intermediates directory to be COMMON.
        second_arch (bool): If True, use the 2nd architecture prefix.
        host_cross_os (bool): If True, force intermediates to be for the host cross OS.
        target_product_out (str): Optional base directory for the product output.

    Returns:
        str: The calculated path to the meta intermediates directory.

    Raises:
        ValueError: If required parameters are not provided.
    """
    if not local_module_class:
        raise ValueError("LOCAL_MODULE_CLASS not defined before call to local_meta_intermediates_dir.")
    if not local_module:
        raise ValueError("LOCAL_MODULE not defined before call to local_meta_intermediates_dir.")

    # Prefix the module class with 'META'
    meta_class = f"META_{local_module_class}"

    # Determine the target type based on the host module flag
    target_type = "HOST" if local_is_host_module else "TARGET"

    # Call the intermediates_dir_for function with resolved parameters
    return intermediates_dir_for(
        target_class=meta_class,
        target_name=local_module,
        target_type=target_type,
        force_common=force_common,
        second_arch=second_arch,
        host_cross_os=host_cross_os,
        target_product_out=target_product_out
    )

def generated_sources_dir_for(
    target_class,
    target_name,
    target_type=None,
    force_common=False,
    common_module_classes=None,
    out_common_gen=None,
    out_gen=None,
    host_cross_os=None,
):
    """
    Calculate the generated sources directory for a given target.

    Args:
        target_class (str): Class of the target (e.g., "APPS").
        target_name (str): Name of the target (e.g., "NotePad").
        target_type (str): Type of the target (e.g., "HOST", "TARGET"). Default is None.
        force_common (bool): If True, force the generated sources directory to be COMMON.
        common_module_classes (list): List of common module classes to consider.
        out_common_gen (Path or str): Base path for common generated sources.
        out_gen (Path or str): Base path for non-common generated sources.
        host_cross_os (bool): If True, force host cross OS prefix.

    Returns:
        str: The calculated path to the generated sources directory.

    Raises:
        ValueError: If required parameters are not provided.
    """
    if not target_class:
        raise ValueError("Class not defined in call to generated_sources_dir_for.")
    if not target_name:
        raise ValueError("Name not defined in call to generated_sources_dir_for.")

    # Resolve base paths from arguments (ensure Path objects for consistency)
    out_common_gen = Path(out_common_gen) if out_common_gen else Path.cwd() / "obj/common_gen"
    out_gen = Path(out_gen) if out_gen else Path.cwd() / "obj/gen"

    # Determine the prefix based on the target type
    idf_prefix = find_idf_prefix(target_type, host_cross_os)

    # Default to an empty list if no specific common classes are provided
    common_module_classes = common_module_classes or []

    # Choose the base directory for generated sources
    if force_common or f"{idf_prefix}_{target_class}" in common_module_classes:
        int_base = out_common_gen
    else:
        int_base = out_gen

    # Construct and return the final path
    return str(int_base / target_class / f"{target_name}_intermediates")

def local_generated_sources_dir(
        local_module_class: str,
        local_module: str,
        local_is_host_module: bool = False,
        force_common: bool = False,
        common_module_classes: list = None,
        out_common_gen: Path = None,
        out_gen: Path = None,
        host_cross_os: bool = False) -> str:
    """
    Determine the generated sources directory for a local module.

    Args:
        local_module_class (str): Class of the local module (e.g., "APPS").
        local_module (str): Name of the local module (e.g., "NotePad").
        local_is_host_module (bool): If True, treat as a host module.
        force_common (bool): If True, force the generated sources directory to be COMMON.
        common_module_classes (list): List of common module classes to consider.
        out_common_gen (Path): Base path for common generated sources.
        out_gen (Path): Base path for non-common generated sources.
        host_cross_os (bool): If True, applies host cross OS prefix.

    Returns:
        str: The calculated path to the generated sources directory.

    Raises:
        ValueError: If required parameters are not provided.
    """
    if not local_module_class:
        raise ValueError(
            "LOCAL_MODULE_CLASS not defined before call to "
            "local_generated_sources_dir."
        )
    if not local_module:
        raise ValueError(
            "LOCAL_MODULE not defined before call to "
            "local_generated_sources_dir."
        )

    target_type = "HOST" if local_is_host_module else "TARGET"

    return generated_sources_dir_for(
        target_class=local_module_class,
        target_name=local_module,
        target_type=target_type,
        force_common=force_common,
        common_module_classes=common_module_classes,
        out_common_gen=out_common_gen,
        out_gen=out_gen,
        host_cross_os=host_cross_os
    )

def packaging_dir_for(
    subdir: str,
    target_class: str,
    target_name: str,
    target_type: str = None,
    target_product_out: Path = None
) -> str:
    """
    Determine the packaging directory for a given target.

    Args:
        subdir (str): Subdirectory inside PACKAGING.
        target_class (str): Class of the target (e.g., "APPS").
        target_name (str): Name of the target (e.g., "NotePad").
        target_type (str): Target type (e.g., "HOST", "HOST_CROSS", "TARGET"). Default is None.
        target_product_out (Path): Base path for the product output. Must be provided.

    Returns:
        str: The calculated path to the packaging directory.

    Raises:
        ValueError: If required parameters are not provided.
    """
    # Validate required parameters
    if not target_product_out:
        raise ValueError("Base packaging path must be provided.")
    if not target_class:
        raise ValueError("Class not defined in call to packaging_dir_for.")
    if not target_name:
        raise ValueError("Name not defined in call to packaging_dir_for.")

    # Construct the packaging base path
    packaging_base = target_product_out / "obj" / "PACKAGING" / subdir

    # Return the final path with target class and target name
    return str(packaging_base / target_class / f"{target_name}_intermediates")


def local_packaging_dir(
    subdir: str,
    local_module_class: str,
    local_module: str,
    local_is_host_module: bool = False,
    target_product_out: Path = None
) -> str:
    """
    Determine the local packaging directory for a given module.

    Args:
        subdir (str): Subdirectory inside PACKAGING.
        local_module_class (str): Class of the local module (e.g., "APPS").
        local_module (str): Name of the local module (e.g., "NotePad").
        local_is_host_module (bool): If True, treat the module as a host module.
        target_product_out (Path): Base path for the product output. Must be provided.

    Returns:
        str: The calculated path to the packaging directory.

    Raises:
        ValueError: If required parameters are not provided.
    """
    if not target_product_out:
        raise ValueError("Base packaging path must be provided.")

    # Determine the target type based on whether it's a host module
    target_type = "HOST" if local_is_host_module else "TARGET"

    # Call packaging_dir_for with the resolved parameters
    return packaging_dir_for(
        subdir=subdir,
        target_class=local_module_class,
        target_name=local_module,
        target_type=target_type,
        target_product_out=target_product_out
    )

def module_built_files(modules_list, all_modules):
    """
    Convert a list of short module names (e.g., "framework", "Browser")
    into the list of files built for those modules.

    Args:
        modules_list (list): List of module names.
        all_modules (dict): Dictionary containing all module information
                            with built files under 'BUILT'.

    Returns:
        list: List of files built for the specified modules.

    Example:
        all_modules = {
            "framework": {"BUILT": ["framework.jar", "framework-res.apk"]},
            "Browser": {"BUILT": ["Browser.apk"]},
        }
        result = module_built_files(["framework", "Browser"], all_modules)
        print(result)  # Output: ['framework.jar', 'framework-res.apk', 'Browser.apk']
    """
    # Collect built files for all specified modules
    built_files = []
    for module in modules_list:
        module_info = all_modules.get(module, {})
        built_files.extend(module_info.get("BUILT", []))
    return built_files

def module_installed_files(module_names, all_modules):
    """
    Convert a list of module names into the list of files installed for those modules.

    Args:
        module_names (list): List of module names (e.g., ["coreutils", "networking"]).
        all_modules (dict): Dictionary containing module attributes, including 'INSTALLED' files.

    Returns:
        list: List of installed files for the specified modules.
    """
    installed_files = []
    for module in module_names:
        files = all_modules.get(module, {}).get("INSTALLED", [])
        installed_files.extend(files)
    return installed_files


def get_host_2nd_arch():
    host_arch = platform.machine().lower()
    if host_arch == 'x86_64':
        return 'i686'
    elif host_arch in ['arm64', 'aarch64']:
        return 'arm'
    return 'unknown'

def module_target_built_files(module_names, all_modules):
    """
    Convert a list of module names into the list of files built for the target for those modules.

    Args:
        module_names (list): List of module names (e.g., ["coreutils", "networking"]).
        all_modules (dict): Dictionary containing module attributes, including 'TARGET_BUILT' files.

    Returns:
        list: List of target-built files for the specified modules.
    """
    target_built_files = []
    for module in module_names:
        files = all_modules.get(module, {}).get("TARGET_BUILT", [])
        target_built_files.extend(files)
    return target_built_files

def doc_timestamp_for(doc_module, out_docs):
    """
    Evaluates to the timestamp file for a doc module.

    Args:
        doc_module (str): The name of the documentation module.
        out_docs (Path): Path to the output directory for documentation.

    Returns:
        str: The path to the timestamp file for the specified doc module.
    """
    if not doc_module:
        raise ValueError("Doc module name must be provided.")

    # Construct the timestamp file path
    timestamp_path = out_docs / f"{doc_module}-timestamp"
    return str(timestamp_path)

def append_path(base_path: str, leaf_path: str) -> str:
    """
    Append a leaf path to a base path, properly handling slashes.

    Args:
        base_path (str): The base path to append to.
        leaf_path (str): The leaf path to append.

    Returns:
        str: The combined path with proper slashes.
    """
    # Ensure the leaf path does not start with a slash
    leaf_path = leaf_path.lstrip('/')

    # Join paths and normalize any double slashes
    combined_path = os.path.join(base_path, leaf_path)
    return os.path.normpath(combined_path)

esc_bold = Style.BRIGHT
esc_warning = Fore.MAGENTA
esc_error = Fore.RED
esc_reset = Style.RESET_ALL

def echo_warning(path_info: str, message: str) -> None:
    """
    Print a formatted warning message with path information.

    Args:
        path_info (str): The path (and optionally line) information.
        message (str): The warning message to print.
    """
    # Format the warning message
    formatted_message = (
        f"{esc_bold}{path_info}: {esc_warning}warning:{esc_reset}{esc_bold} "
        f"{message.replace("'", r'\'')}{esc_reset}"
    )


    # Print the message to stderr
    print(formatted_message, file=sys.stderr)

def echo_error(path_info: str, message: str) -> None:
    """
    Print a formatted error message with path information.

    Args:
        path_info (str): The path (and optionally line) information.
        message (str): The error message to print.
    """
    # Format the error message
    formatted_message = (
        f"{esc_bold}{path_info}: {esc_error}error:{esc_reset}{esc_bold} "
        f"{message.replace("'", r'\'')}{esc_reset}"
    )

    # Print the message to stderr
    print(formatted_message, file=sys.stderr)

def pretty(message: str) -> None:
    """
    Print a message to mimic legacy showcommands compatibility.

    Args:
        message (str): The message to print.
    """
    print(message)

def include_depfile(depfile, obj, all_targets, depfile_key="DEPFILE"):
    """
    Include a single dependency file for an object file.

    Args:
        depfile (Path): Path to the dependency file.
        obj (Path): Path to the object file.
        all_targets (dict): Dictionary to store targets and their dependencies.
        depfile_key (str): Key used to store the dependency file path.

    Returns:
        None: Updates the `all_targets` dictionary in place.
    """
    all_targets[str(obj)] = {depfile_key: str(depfile)}

def include_depfiles_for_objs(object_files, all_targets, depfile_key="DEPFILE"):
    """
    Include dependency files for a list of object files.

    Args:
        object_files (list): List of object files (.o files).
        all_targets (dict): Dictionary to store targets and their dependencies.
        depfile_key (str): Key used to store the dependency file path (default is 'DEPFILE').

    Returns:
        None: Updates the `all_targets` dictionary in place.
    """
    # Iterate through the object files and map each to its dependency file
    for obj in object_files:
        depfile = obj.with_suffix(".d")  # Replace .o with .d
        include_depfile(depfile, obj, all_targets, depfile_key=depfile_key)

# Track source files, generated files, and their corresponding objects
tracked_src_files = []
tracked_gen_files = []
src_file_obj_mapping = defaultdict(str)
src_file_gen_mapping = defaultdict(str)

def track_src_file_obj(sources, objects):
    """
    Track source files and their corresponding object files.

    Args:
        sources (list): List of source files.
        objects (list): List of matching object files.
    """
    for i, src in enumerate(sources):
        tracked_src_files.append(src)
        if i < len(objects):
            src_file_obj_mapping[src] = objects[i]

def track_src_file_gen(sources, generated_files):
    """
    Track source files and their corresponding generated files.

    Args:
        sources (list): List of source files.
        generated_files (list): List of matching generated files.
    """
    for i, src in enumerate(sources):
        tracked_gen_files.append(src)
        if i < len(generated_files):
            src_file_gen_mapping[src] = generated_files[i]

def track_gen_file_obj(generated_files, objects):
    """
    Track generated files and their corresponding object files.

    Args:
        generated_files (list): List of generated files.
        objects (list): List of matching object files.
    """
    sources = [
        src_file_gen_mapping.get(gen, gen) for gen in generated_files
    ]
    track_src_file_obj(sources, objects)

def transform_l_to_c_or_cpp(lex_file: str, output_file: str, private_module: str, lex: str = "lex", m4: str = "m4"):
    """
    Transform a .l file into a .c or .cpp file using Lex.

    Args:
        lex_file (str): Path to the input .l file.
        output_file (str): Path to the output .c or .cpp file.
        private_module (str): Name of the private module being processed.
        lex (str): Lex command to use. Default is 'lex'.
        m4 (str): M4 command to use. Default is 'm4'.

    Raises:
        FileNotFoundError: If the input lex file does not exist.
        subprocess.CalledProcessError: If the lex command fails.
    """
    if not os.path.exists(lex_file):
        raise FileNotFoundError(f"Lex file not found: {lex_file}")

    # Create the output directory if it doesn't exist
    output_dir = Path(output_file).parent
    os.makedirs(output_dir, exist_ok=True)

    # Print the transformation message
    print(f"Lex: {private_module} <= {lex_file}")

    # Construct the lex command
    command = f"{m4} | {lex} -o{output_file} {lex_file}"

    # Execute the lex command
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during Lex transformation: {e}")
        raise

def transform_y_to_c_or_cpp(yacc_file: str, output_file: str, private_module: str,
                            yacc: str = "yacc", m4: str = "m4", yacc_flags: str = ""):
    """
    Transform a .y file into a .c or .cpp file using Yacc.

    Args:
        yacc_file (str): Path to the input .y file.
        output_file (str): Path to the output .c or .cpp file.
        private_module (str): Name of the private module being processed.
        yacc (str): Yacc command to use. Default is 'yacc'.
        m4 (str): M4 command to use. Default is 'm4'.
        yacc_flags (str): Additional Yacc flags.

    Raises:
        FileNotFoundError: If the input Yacc file does not exist.
        subprocess.CalledProcessError: If the Yacc command fails.
    """
    if not os.path.exists(yacc_file):
        raise FileNotFoundError(f"Yacc file not found: {yacc_file}")

    # Create the output directory if it doesn't exist
    output_dir = Path(output_file).parent
    os.makedirs(output_dir, exist_ok=True)

    # Print the transformation message
    print(f"Yacc: {private_module} <= {yacc_file}")

    # Generate the header file path from the output file's basename
    header_file = f"{Path(output_file).stem}.h"

    # Construct the Yacc command
    command = f"{m4} | {yacc} {yacc_flags} --defines={header_file} -o {output_file} {yacc_file}"

    # Execute the Yacc command
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during Yacc transformation: {e}")
        raise

def c_includes(
    private_c_includes=None,
    private_imported_includes=None,
    exports=None,
    private_global_c_includes=None,
    private_global_c_system_includes=None,
    private_no_default_compiler_flags=False,
):
    """
    Generate a list of include paths for compiling C/C++ code.

    Args:
        private_c_includes (list): List of private include paths.
        private_imported_includes (list): List of imported includes to be resolved from exports.
        exports (dict): Dictionary of export mappings for imported includes.
        private_global_c_includes (list): Global include paths.
        private_global_c_system_includes (list): Global system include paths.
        private_no_default_compiler_flags (bool): If True, do not add default compiler flags.

    Returns:
        list: A list of formatted include paths for the compiler.
    """

    # Ensure inputs are lists if not provided
    private_c_includes = private_c_includes or []
    private_imported_includes = private_imported_includes or []
    exports = exports or {}
    private_global_c_includes = private_global_c_includes or []
    private_global_c_system_includes = private_global_c_system_includes or []

    # Resolve imported includes from exports dictionary
    imported_includes = [
        exports.get(include, "") for include in private_imported_includes
    ]

    # Format private includes with '-I ' prefix
    include_paths = [f"-I {inc}" for inc in private_c_includes]

    # Add imported includes to the paths list
    include_paths.extend(imported_includes)

    # If no default compiler flags, skip the global includes
    if not private_no_default_compiler_flags:
        # Add global includes, excluding any that overlap with private includes
        filtered_global_includes = [
            inc for inc in private_global_c_includes if inc not in private_c_includes
        ]
        include_paths.extend([f"-I {inc}" for inc in filtered_global_includes])

        # Add global system includes with '-isystem ' prefix
        filtered_system_includes = [
            inc
            for inc in private_global_c_system_includes
            if inc not in private_c_includes
        ]
        include_paths.extend([f"-isystem {inc}" for inc in filtered_system_includes])

    return include_paths

def transform_cpp_to_o_compiler_args(
    private_c_includes,
    private_imported_includes=None,
    exports=None,
    private_no_default_compiler_flags=False,
    private_target_global_cflags=None,
    private_target_global_cppflags=None,
    private_arm_cflags=None,
    private_rtti_flag=None,
    private_cflags=None,
    private_cppflags=None,
    private_debug_cflags=None,
    private_cflags_no_override=None,
    private_cppflags_no_override=None,
    private_global_c_includes=None,
    private_global_c_system_includes=None
):
    """
    Generate compiler arguments for transforming a C++ file into an object file.

    This function uses the provided variables to build compiler arguments,
    ensuring it matches the Makefile logic for flexibility and correctness.
    """

    # Generate include paths
    includes = " ".join([f"-I {path}" for path in private_c_includes])
    imported_includes = " ".join(
        [exports.get(i, "") for i in (private_imported_includes or [])]
    )
    global_includes = (
        "" if private_no_default_compiler_flags else
        " ".join([f"-I {path}" for path in private_global_c_includes or []])
    )
    system_includes = (
        "" if private_no_default_compiler_flags else
        " ".join([f"-isystem {path}" for path in private_global_c_system_includes or []])
    )

    # Assemble compiler arguments
    args = [
        includes,
        imported_includes,
        global_includes,
        system_includes,
        "-c"
    ]

    if not private_no_default_compiler_flags:
        if private_target_global_cflags:
            args.append(private_target_global_cflags)
        if private_target_global_cppflags:
            args.append(private_target_global_cppflags)
        if private_arm_cflags:
            args.append(private_arm_cflags)

    if private_rtti_flag:
        args.append(private_rtti_flag)
    if private_cflags:
        args.append(private_cflags)
    if private_cppflags:
        args.append(private_cppflags)
    if private_debug_cflags:
        args.append(private_debug_cflags)
    if private_cflags_no_override:
        args.append(private_cflags_no_override)
    if private_cppflags_no_override:
        args.append(private_cppflags_no_override)

    # Join all arguments into a single string
    return " ".join(filter(None, args))

def call_clang_tidy(
    path_to_clang_tidy,
    private_tidy_flags=None,
    private_tidy_checks=None
):
    """
    Generate the command for running clang-tidy with specific flags and checks.

    Args:
        path_to_clang_tidy (str): Path to the clang-tidy binary.
        private_tidy_flags (str): Additional flags for clang-tidy.
        private_tidy_checks (str): List of checks to run with clang-tidy.

    Returns:
        str: The assembled clang-tidy command.
    """

    # Initialize the command with the path to clang-tidy
    command = [path_to_clang_tidy]

    # Add optional flags if provided
    if private_tidy_flags:
        command.append(private_tidy_flags)

    # Add the checks if provided
    if private_tidy_checks:
        command.append(f"-checks={private_tidy_checks}")

    # Join the command components into a single string
    return " ".join(command)

def clang_tidy_cpp(
    source_file,
    path_to_clang_tidy="clang-tidy",
    private_tidy_flags=None,
    private_tidy_checks=None,
    private_c_includes=None,
    private_imported_includes=None,
    exports=None,
    private_no_default_compiler_flags=False,
    private_target_global_cflags=None,
    private_target_global_cppflags=None,
    private_arm_cflags=None,
    private_rtti_flag=None,
    private_cflags=None,
    private_cppflags=None,
    private_debug_cflags=None,
    private_cflags_no_override=None,
    private_cppflags_no_override=None,
    private_global_c_includes=None,
    private_global_c_system_includes=None
):
    """
    Run clang-tidy on the given C++ source file with dynamically generated
    compiler arguments using the provided functions.
    """

    # Generate the clang-tidy command
    clang_tidy_command = call_clang_tidy(
        path_to_clang_tidy,
        private_tidy_flags,
        private_tidy_checks
    )

    # Generate compiler arguments
    compiler_args = transform_cpp_to_o_compiler_args(
        private_c_includes or [],
        private_imported_includes,
        exports,
        private_no_default_compiler_flags,
        private_target_global_cflags,
        private_target_global_cppflags,
        private_arm_cflags,
        private_rtti_flag,
        private_cflags,
        private_cppflags,
        private_debug_cflags,
        private_cflags_no_override,
        private_cppflags_no_override,
        private_global_c_includes,
        private_global_c_system_includes
    )

    # Construct the full clang-tidy command with arguments
    full_command = f"{clang_tidy_command} {source_file} -- {compiler_args}"

    try:
        # Execute the command
        result = subprocess.run(full_command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Clang-tidy failed with error:\n{e.stderr}")

def clang_tidy_cpp_if_needed(
    source_file,
    output_file,
    with_tidy_only=False,
    path_to_clang_tidy="clang-tidy",
    private_prefix=None,
    private_tidy_flags=None,
    private_tidy_checks=None,
    private_arm_mode=None,
    private_module=None,
    private_cxx=None,
    private_c_includes=None,
    private_imported_includes=None,
    exports=None,
    private_no_default_compiler_flags=False,
    private_target_global_cflags=None,
    private_target_global_cppflags=None,
    private_arm_cflags=None,
    private_rtti_flag=None,
    private_cflags=None,
    private_cppflags=None,
    private_debug_cflags=None,
    private_cflags_no_override=None,
    private_cppflags_no_override=None,
    private_global_c_includes=None,
    private_global_c_system_includes=None
):
    """
    Executes either clang-tidy or the C++ compiler command based on conditions.
    """

    def echo_message(message):
        """Utility to print messages in a controlled way."""
        print(message)

    def run_clang_tidy():
        """Run clang-tidy if checks are enabled."""
        if private_tidy_checks:
            echo_message(f"{private_prefix} tidy {private_arm_mode} C++: {source_file}")
            clang_tidy_cpp(
                source_file=source_file,
                path_to_clang_tidy=path_to_clang_tidy,
                private_tidy_flags=private_tidy_flags,
                private_tidy_checks=private_tidy_checks,
                private_c_includes=private_c_includes,
                private_imported_includes=private_imported_includes,
                exports=exports,
                private_no_default_compiler_flags=private_no_default_compiler_flags,
                private_target_global_cflags=private_target_global_cflags,
                private_target_global_cppflags=private_target_global_cppflags,
                private_arm_cflags=private_arm_cflags,
                private_rtti_flag=private_rtti_flag,
                private_cflags=private_cflags,
                private_cppflags=private_cppflags,
                private_debug_cflags=private_debug_cflags,
                private_cflags_no_override=private_cflags_no_override,
                private_cppflags_no_override=private_cppflags_no_override,
                private_global_c_includes=private_global_c_includes,
                private_global_c_system_includes=private_global_c_system_includes
            )

    def run_cpp_compiler():
        """Run the C++ compiler command."""
        echo_message(f"{private_prefix} {private_arm_mode} C++: {private_module} <= {source_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Build the compilation command
        compiler_args = transform_cpp_to_o_compiler_args(
            private_c_includes or [],
            private_imported_includes,
            exports,
            private_no_default_compiler_flags,
            private_target_global_cflags,
            private_target_global_cppflags,
            private_arm_cflags,
            private_rtti_flag,
            private_cflags,
            private_cppflags,
            private_debug_cflags,
            private_cflags_no_override,
            private_cppflags_no_override,
            private_global_c_includes,
            private_global_c_system_includes
        )

        command = f"{private_cxx} {compiler_args} -MD -MF {output_file.replace('.o', '.d')} -o {output_file} {source_file}"

        # Run clang-tidy if checks are enabled
        if private_tidy_checks:
            run_clang_tidy()

        # Execute the compilation command
        subprocess.run(command, shell=True, check=True)

    # Determine which path to take based on `with_tidy_only` flag
    if with_tidy_only:
        run_clang_tidy()
    else:
        run_cpp_compiler()

def transform_c_or_s_to_o_compiler_args(
    extra_flags="",
    private_c_includes=None,
    private_no_default_compiler_flags=False,
    private_target_global_cflags=None,
    private_target_global_conlyflags=None,
    private_arm_cflags=None
):
    """
    Generate compiler arguments for compiling C or assembly files to object files.
    Args:
        extra_flags (str): Additional compiler flags.
        private_c_includes (list): List of include directories.
        private_no_default_compiler_flags (bool): If True, omit default flags.
        private_target_global_cflags (str): Global compiler flags for C.
        private_target_global_conlyflags (str): C-only flags.
        private_arm_cflags (str): ARM-specific compiler flags.
    Returns:
        str: Assembled compiler argument string.
    """
    # Collect all includes
    includes = " ".join([f"-I {path}" for path in private_c_includes or []])

    # Base compiler arguments
    args = [includes, "-c"]

    # Add optional flags if default flags are not disabled
    if not private_no_default_compiler_flags:
        if private_target_global_cflags:
            args.append(private_target_global_cflags)
        if private_target_global_conlyflags:
            args.append(private_target_global_conlyflags)
        if private_arm_cflags:
            args.append(private_arm_cflags)

    # Append any extra flags provided
    args.append(extra_flags)

    # Join and return all arguments as a single string
    return " ".join(filter(None, args))

def transform_c_to_o_compiler_args(
    private_cflags="",
    private_conlyflags="",
    private_debug_cflags="",
    private_cflags_no_override="",
    **kwargs  # Additional arguments passed to transform_c_or_s_to_o_compiler_args
):
    """
    Generate compiler arguments specifically for C files using the
    transform_c_or_s_to_o_compiler_args function.

    Args:
        private_cflags (str): C compiler flags.
        private_conlyflags (str): C-only compiler flags.
        private_debug_cflags (str): Debugging flags.
        private_cflags_no_override (str): Flags that must not be overridden.
        **kwargs: Additional keyword arguments for transform_c_or_s_to_o_compiler_args.

    Returns:
        str: Assembled compiler argument string.
    """
    # Combine C-specific flags into a single string
    extra_flags = " ".join(
        filter(None, [private_cflags, private_conlyflags, private_debug_cflags, private_cflags_no_override])
    )

    # Use transform_c_or_s_to_o_compiler_args to generate the full compiler arguments
    return transform_c_or_s_to_o_compiler_args(extra_flags=extra_flags, **kwargs)

def clang_tidy_c(
    source_file,
    path_to_clang_tidy="clang-tidy",
    **kwargs  # Pass additional arguments to transform_c_to_o_compiler_args
):
    """
    Run clang-tidy on the given C source file with dynamically generated compiler arguments.

    Args:
        source_file (str): The source C file to be processed.
        path_to_clang_tidy (str): Path to the clang-tidy binary. Default is 'clang-tidy'.
        **kwargs: Additional arguments for the compiler argument generation.
    """
    # Generate compiler arguments using transform_c_to_o_compiler_args
    compiler_args = transform_c_to_o_compiler_args(**kwargs)

    # Construct the full clang-tidy command
    command = f"{path_to_clang_tidy} {source_file} -- {compiler_args}"

    print(f"Running: {command}")

    # Execute the clang-tidy command
    subprocess.run(command, shell=True, check=True)

def transform_c_to_o(
    source_file,
    output_file,
    with_tidy_only=False,
    private_prefix="[BUILD]",
    private_tidy_checks=None,
    private_arm_mode=None,
    private_module=None,
    private_cc="clang",  # Using clang instead of gcc
    **kwargs  # Pass additional arguments to compiler functions
):
    """
    Run clang-tidy and/or compile a C file to an object file based on the given conditions.

    Args:
        source_file (str): The source C file to process.
        output_file (str): The output object file path.
        with_tidy_only (bool): If True, only run clang-tidy.
        private_prefix (str): Prefix for displayed messages.
        private_tidy_checks (str): If set, enable clang-tidy checks.
        private_arm_mode (str): ARM mode (e.g., arm64).
        private_module (str): Name of the module being processed.
        private_cc (str): The C compiler command to use.
        **kwargs: Additional arguments for compiler argument generation.
    """
    def echo_message(message):
        """Utility to print messages."""
        print(message)

    def run_clang_tidy():
        """Run clang-tidy on the source file."""
        echo_message(f"{private_prefix} tidy {private_arm_mode} C: {source_file}")
        clang_tidy_c(source_file=source_file, **kwargs)

    def compile_c_file():
        """Compile the C file to an object file."""
        echo_message(f"{private_prefix} {private_arm_mode} C: {private_module} <= {source_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Generate compiler arguments
        compiler_args = transform_c_to_o_compiler_args(**kwargs)

        # Build and run the compilation command
        command = f"{private_cc} {compiler_args} -MD -MF {output_file.replace('.o', '.d')} -o {output_file} {source_file}"
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True)

    # Logic matching the Makefile
    if with_tidy_only:
        if private_tidy_checks:
            run_clang_tidy()
    else:
        if private_tidy_checks:
            run_clang_tidy()
        compile_c_file()

def transform_s_to_o(
    source_file,
    output_file,
    private_prefix="[BUILD]",
    private_module=None,
    private_cc="clang",  # Using clang as the compiler
    private_asflags="",
    **kwargs  # Additional arguments for compiler argument generation
):
    """
    Compile an assembly (.s) source file into an object file.

    Args:
        source_file (str): Path to the assembly (.s) source file.
        output_file (str): Path to the output object file.
        private_prefix (str): Prefix for displayed messages.
        private_module (str): The name of the private module being processed.
        private_cc (str): The C compiler command (e.g., 'clang').
        private_asflags (str): Additional flags for assembly compilation.
        **kwargs: Additional arguments for compiler argument generation.
    """
    def echo_message(message):
        """Utility function to print formatted messages."""
        print(message)

    # Print the processing message
    echo_message(f"{private_prefix} asm: {private_module} <= {source_file}")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Generate the compiler arguments for assembly compilation
    compiler_args = transform_c_or_s_to_o_compiler_args(
        extra_flags=private_asflags, **kwargs
    )

    # Construct the full compilation command
    command = f"{private_cc} {compiler_args} -MD -MF {output_file.replace('.o', '.d')} -o {output_file} {source_file}"

    print(f"Running: {command}")

    # Execute the compilation command
    subprocess.run(command, shell=True, check=True)

def transform_asm_to_o(
    source_file,
    output_file,
    yasm="yasm",
    private_c_includes=None,
    target_global_yasm_flags="",
    private_asflags="",
    **kwargs  # Additional keyword arguments (if any)
):
    """
    Compile an assembly (.asm) file into an object file using YASM.

    Args:
        source_file (str): Path to the assembly (.asm) source file.
        output_file (str): Path to the output object file.
        yasm (str): YASM command to use. Default is 'yasm'.
        private_c_includes (list): List of include directories for YASM.
        target_global_yasm_flags (str): Global YASM flags for the target.
        private_asflags (str): Additional assembly flags.
        **kwargs: Additional keyword arguments (if any).
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Construct include paths
    include_args = " ".join([f"-I {inc}" for inc in private_c_includes or []])

    # Construct the full YASM command
    command = (
        f"{yasm} {include_args} {target_global_yasm_flags} "
        f"{private_asflags} -o {output_file} {source_file}"
    )

    print(f"Running: {command}")

    # Execute the YASM command
    subprocess.run(command, shell=True, check=True)

def transform_m_to_o(
    source_file,
    output_file,
    private_prefix="[BUILD]",
    private_module=None,
    private_cc="clang",  # Using clang for ObjC compilation
    private_cflags="",
    private_debug_cflags="",
    **kwargs  # Additional arguments for compiler argument generation
):
    """
    Compile an Objective-C (.m) file into an object file.

    Args:
        source_file (str): Path to the Objective-C (.m) source file.
        output_file (str): Path to the output object file.
        private_prefix (str): Prefix for displayed messages.
        private_module (str): The name of the private module being processed.
        private_cc (str): Compiler command to use. Default is 'clang'.
        private_cflags (str): Flags for the C compiler.
        private_debug_cflags (str): Debugging flags for the compiler.
        **kwargs: Additional keyword arguments for compiler argument generation.
    """
    def echo_message(message):
        """Utility function to print formatted messages."""
        print(message)

    # Print the processing message
    echo_message(f"{private_prefix} ObjC: {private_module} <= {source_file}")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Generate the compiler arguments for Objective-C compilation
    extra_flags = f"{private_cflags} {private_debug_cflags}"
    compiler_args = transform_c_or_s_to_o_compiler_args(extra_flags=extra_flags, **kwargs)

    # Construct the full compilation command
    command = f"{private_cc} {compiler_args} -o {output_file} {source_file}"

    print(f"Running: {command}")

    # Execute the compilation command
    subprocess.run(command, shell=True, check=True)

def transform_host_cpp_to_o_compiler_args(
    private_cflags="",
    private_cppflags="",
    private_debug_cflags="",
    private_cflags_no_override="",
    private_cppflags_no_override="",
    private_no_default_compiler_flags=False,
    private_host_global_cflags="",
    private_host_global_cppflags="",
    private_c_includes=None,
):
    """
    Generate compiler arguments for compiling host C++ files to object files.

    Args:
        private_cflags (str): C flags.
        private_cppflags (str): C++ flags.
        private_debug_cflags (str): Debugging flags.
        private_cflags_no_override (str): Non-overridable C flags.
        private_cppflags_no_override (str): Non-overridable C++ flags.
        private_no_default_compiler_flags (bool): If True, omit default flags.
        private_host_global_cflags (str): Global C flags for host.
        private_host_global_cppflags (str): Global C++ flags for host.
        private_c_includes (list): Include directories.

    Returns:
        str: The assembled compiler argument string.
    """
    includes = " ".join([f"-I {path}" for path in private_c_includes or []])

    args = [includes, "-c"]

    if not private_no_default_compiler_flags:
        args.append(private_host_global_cflags)
        args.append(private_host_global_cppflags)

    args.extend([
        private_cflags,
        private_cppflags,
        private_debug_cflags,
        private_cflags_no_override,
        private_cppflags_no_override,
    ])

    return " ".join(filter(None, args))

def clang_tidy_host_cpp(
    source_file,
    path_to_clang_tidy="clang-tidy",
    **kwargs
):
    """
    Run clang-tidy on a host C++ file with dynamically generated compiler arguments.

    Args:
        source_file (str): The C++ source file to process.
        path_to_clang_tidy (str): Path to the clang-tidy binary.
        **kwargs: Additional arguments for compiler flags.
    """
    compiler_args = transform_host_cpp_to_o_compiler_args(**kwargs)
    command = f"{path_to_clang_tidy} {source_file} -- {compiler_args}"
    print(f"Running: {command}")
    subprocess.run(command, shell=True, check=True)

def transform_host_cpp_to_o_c(
    source_file,
    output_file,
    with_tidy_only=False,
    private_prefix="[BUILD]",
    private_tidy_checks=True,
    private_module=None,
    private_cxx="clang++",
    **kwargs
):
    """
    Compile a host C++ file to an object file, optionally with clang-tidy checks.

    Args:
        source_file (str): The source C++ file to process.
        output_file (str): The path to the output object file.
        with_tidy_only (bool): If True, only run clang-tidy.
        private_prefix (str): Prefix for displayed messages.
        private_tidy_checks (bool): If True, run clang-tidy checks.
        private_module (str): Name of the module being processed.
        private_cxx (str): Compiler command to use.
        **kwargs: Additional arguments for compiler flags.
    """
    def echo_message(message):
        """Utility function to print formatted messages."""
        print(message)

    def run_clang_tidy():
        """Run clang-tidy if enabled."""
        echo_message(f"tidy {private_prefix} C++: {source_file}")
        clang_tidy_host_cpp(source_file=source_file, **kwargs)

    def compile_cpp_file():
        """Compile the C++ source file to an object file."""
        echo_message(f"{private_prefix} C++: {private_module} <= {source_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        compiler_args = transform_host_cpp_to_o_compiler_args(**kwargs)
        command = f"{private_cxx} {compiler_args} -MD -MF {output_file.replace('.o', '.d')} -o {output_file} {source_file}"
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True)

    if with_tidy_only:
        if private_tidy_checks:
            run_clang_tidy()
    else:
        if private_tidy_checks:
            run_clang_tidy()
        compile_cpp_file()

def transform_host_c_or_s_to_o_common_args(
    private_c_includes=None,
    private_no_default_compiler_flags=False,
    private_host_global_cflags="",
    private_host_global_conlyflags=""
):
    """
    Generate common compiler arguments for host C or assembly files.
    """
    includes = " ".join([f"-I {path}" for path in private_c_includes or []])
    args = [includes, "-c"]

    if not private_no_default_compiler_flags:
        args.extend([private_host_global_cflags, private_host_global_conlyflags])

    return " ".join(filter(None, args))

def transform_host_c_to_o_compiler_args(
    private_cflags="",
    private_conlyflags="",
    private_debug_cflags="",
    private_cflags_no_override="",
    **kwargs
):
    """
    Generate full compiler arguments for host C files.
    """
    common_args = transform_host_c_or_s_to_o_common_args(**kwargs)
    return f"{common_args} {private_cflags} {private_conlyflags} {private_debug_cflags} {private_cflags_no_override}"

def clang_tidy_host_c(source_file, **kwargs):
    """
    Run clang-tidy for host C files.
    """
    compiler_args = transform_host_c_to_o_compiler_args(**kwargs)
    command = f"clang-tidy {source_file} -- {compiler_args}"
    print(f"Running: {command}")
    subprocess.run(command, shell=True, check=True)

def transform_host_c_to_o(
    source_file,
    output_file,
    with_tidy_only=False,
    private_prefix="[BUILD]",
    private_tidy_checks=True,
    private_module=None,
    private_cc="clang",
    **kwargs
):
    """
    Compile host C files with optional clang-tidy checks.
    """
    def echo_message(message):
        """Utility to print formatted messages."""
        print(message)

    def run_clang_tidy():
        """Run clang-tidy if enabled."""
        echo_message(f"tidy {private_prefix} C: {source_file}")
        clang_tidy_host_c(source_file=source_file, **kwargs)

    def compile_c_file():
        """Compile the host C file to an object file."""
        echo_message(f"{private_prefix} C: {private_module} <= {source_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        compiler_args = transform_host_c_to_o_compiler_args(**kwargs)
        command = f"{private_cc} {compiler_args} -MD -MF {output_file.replace('.o', '.d')} -o {output_file} {source_file}"
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True)

    # Execute based on tidy-only flag
    if with_tidy_only and private_tidy_checks:
        run_clang_tidy()
    else:
        if private_tidy_checks:
            run_clang_tidy()
        compile_c_file()

def transform_host_s_to_o(
    source_file,
    output_file,
    private_prefix="[BUILD]",
    private_module=None,
    private_cc="clang",
    private_asflags="",
    **kwargs
):
    """
    Compile host assembly (.s) files to object files.
    """
    def echo_message(message):
        """Utility function to print formatted messages."""
        print(message)

    echo_message(f"{private_prefix} asm: {private_module} <= {source_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    common_args = transform_host_c_or_s_to_o_common_args(**kwargs)
    command = f"{private_cc} {common_args} {private_asflags} -MD -MF {output_file.replace('.o', '.d')} -o {output_file} {source_file}"
    print(f"Running: {command}")
    subprocess.run(command, shell=True, check=True)

def transform_host_m_to_o(
    source_file,
    output_file,
    private_prefix="[BUILD]",
    private_module=None,
    private_cc="clang",  # Using clang for ObjC compilation
    private_cflags="",
    private_debug_cflags="",
    private_cflags_no_override="",
    **kwargs
):
    """
    Compile a host Objective-C (.m) file into an object file.

    Args:
        source_file (str): Path to the Objective-C (.m) source file.
        output_file (str): Path to the output object file.
        private_prefix (str): Prefix for displayed messages.
        private_module (str): The name of the module being processed.
        private_cc (str): Compiler command (e.g., 'clang').
        private_cflags (str): Flags for the compiler.
        private_debug_cflags (str): Debugging flags for the compiler.
        private_cflags_no_override (str): Non-overridable C flags.
        **kwargs: Additional keyword arguments for compiler argument generation.
    """
    def echo_message(message):
        """Utility function to print formatted messages."""
        print(message)

    # Print the processing message
    echo_message(f"{private_prefix} ObjC: {private_module} <= {source_file}")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Generate the common compiler arguments
    common_args = transform_host_c_or_s_to_o_common_args(**kwargs)

    # Construct the full compiler arguments
    extra_flags = f"{private_cflags} {private_debug_cflags} {private_cflags_no_override}"
    compiler_args = f"{common_args} {extra_flags}"

    # Construct and run the compilation command
    command = f"{private_cc} {compiler_args} -o {output_file} {source_file}"
    print(f"Running: {command}")
    subprocess.run(command, shell=True, check=True)

DOTDOT_REPLACEMENT = "dotdot/"

def replace_dotdot_in_path(path):
    """Replace '../' in the path with the defined DOTDOT_REPLACEMENT."""
    return path.replace("../", DOTDOT_REPLACEMENT)

def compile_dotdot_file(
    source_file,
    output_file,
    dependencies=None,
    compiler="clang",
    compile_flags="",
    ninja_pool=None,
):
    """
    Compile a source file (C/C++/Assembly) to an object file.

    Args:
        source_file (str): The source file path.
        output_file (str): The output object file path.
        dependencies (list): Additional dependencies (if any).
        compiler (str): The compiler to use (e.g., clang, clang++).
        compile_flags (str): Additional flags for the compiler.
        ninja_pool (str): Ninja pool (if used for parallelism).
    """
    dependencies = dependencies or []

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Print the compilation command
    command = f"{compiler} {compile_flags} -o {output_file} {source_file}"
    print(f"Running: {command}")

    # Run the compilation command
    subprocess.run(command, shell=True, check=True)

def compile_dotdot_cpp_file(source_file, intermediates, ninja_pool=None):
    """Compile a C++ source file with '../' in the path."""
    object_file = Path(intermediates) / replace_dotdot_in_path(source_file).with_suffix(".o")
    compile_dotdot_file(source_file, str(object_file), compiler="clang++", ninja_pool=ninja_pool)
    return object_file

def compile_dotdot_c_file(source_file, intermediates, ninja_pool=None):
    """Compile a C source file with '../' in the path."""
    object_file = Path(intermediates) / replace_dotdot_in_path(source_file).with_suffix(".o")
    compile_dotdot_file(source_file, str(object_file), compiler="clang", ninja_pool=ninja_pool)
    return object_file

def compile_dotdot_s_file(source_file, intermediates, ninja_pool=None):
    """Compile a .S source file with '../' in the path."""
    object_file = Path(intermediates) / replace_dotdot_in_path(source_file).with_suffix(".o")
    compile_dotdot_file(source_file, str(object_file), compiler="clang", ninja_pool=ninja_pool)
    return object_file

def compile_dotdot_s_file_no_deps(source_file, intermediates, ninja_pool=None):
    """Compile a .s source file with '../' in the path, without dependencies."""
    object_file = Path(intermediates) / replace_dotdot_in_path(source_file).with_suffix(".o")
    compile_dotdot_file(source_file, str(object_file), compiler="clang", ninja_pool=ninja_pool)
    return object_file

def concat_if_arg2_not_empty(cmd, args):
    """Run the command if args is not empty."""
    if args:
        print(f"Running: {cmd} {args}")
        subprocess.run(f"{cmd} {args}", shell=True, check=True)

def split_long_arguments(cmd, args):
    """
    Split a long list of arguments into smaller groups and call the command multiple times.
    At least one call is made, even if there are no arguments, to ensure the output is created.
    """
    groups = [args[i:i + 500] for i in range(0, len(args), 500)]
    for group in groups:
        concat_if_arg2_not_empty(cmd, " ".join(group))

def extract_and_include_single_target_whole_static_lib(src_lib, dest_lib, ar="ar"):
    """
    Extracts the contents of a static library and includes them into a new destination library.
    """
    ldir = f"{os.path.splitext(os.path.basename(src_lib))[0]}_objs"
    if os.path.exists(ldir):
        shutil.rmtree(ldir)
    os.makedirs(ldir)

    shutil.copy(src_lib, ldir)
    lib_to_include = os.path.join(ldir, os.path.basename(src_lib))

    # Extract and repackage each file
    filelist = []
    subdir = 0
    extracted_files = subprocess.check_output([ar, "t", src_lib], text=True).splitlines()
    for f in extracted_files:
        if os.path.exists(os.path.join(ldir, f)):
            subdir_path = os.path.join(ldir, str(subdir))
            os.makedirs(subdir_path, exist_ok=True)
            subdir += 1
            ar_cmd = [ar, "m", lib_to_include, f]
            print(f"Running: {' '.join(ar_cmd)}")
            subprocess.run(ar_cmd, check=True)

        ext_path = os.path.join(ldir, f)
        ar_cmd = [ar, "p", lib_to_include, f]
        with open(ext_path, "w") as out_file:
            subprocess.run(ar_cmd, stdout=out_file, check=True)
        filelist.append(ext_path)

    ar_cmd = [ar, "rcs", dest_lib] + filelist
    print(f"Running: {' '.join(ar_cmd)}")
    subprocess.run(ar_cmd, check=True)

def extract_and_include_whole_static_libs_first(src_lib, dest_lib):
    """Copy the source static library to the destination if it exists."""
    if src_lib:
        print(f"Copying {src_lib} to {dest_lib}")
        shutil.copy(src_lib, dest_lib)

def extract_and_include_target_whole_static_libs(dest_lib, ar="ar"):
    """Extract and include all target whole static libraries."""
    static_libs = os.environ.get("PRIVATE_ALL_WHOLE_STATIC_LIBRARIES", "").split()
    if static_libs:
        extract_and_include_whole_static_libs_first(static_libs[0], dest_lib)
        for lib in static_libs[1:]:
            extract_and_include_single_target_whole_static_lib(lib, dest_lib, ar)

def transform_o_to_static_lib(
    output_lib,
    private_prefix="[BUILD]",
    private_module="static_module",
    ar="ar",
    private_arflags="",
    object_files=None
):
    """Create a static library from object files."""
    object_files = object_files or []

    # Print processing message
    print(f"{private_prefix} StaticLib: {private_module} ({output_lib})")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_lib), exist_ok=True)

    # Remove any existing static library
    tmp_lib = f"{output_lib}.tmp"
    if os.path.exists(output_lib):
        os.remove(output_lib)
    if os.path.exists(tmp_lib):
        os.remove(tmp_lib)

    # Extract and include all static libraries into a temporary archive
    extract_and_include_target_whole_static_libs(tmp_lib, ar)

    # Split object files into smaller groups and add them to the temporary archive
    split_long_arguments(f"{ar} rcs {tmp_lib}", object_files)

    # Move the temporary archive to the final output
    print(f"Moving {tmp_lib} to {output_lib}")
    shutil.move(tmp_lib, output_lib)

def extract_and_include_single_host_whole_static_lib(src_lib, dest_lib, ar="ar"):
    """
    Extract and include the contents of a single host static library into the destination library.
    """
    ldir = f"WHOLE/{os.path.splitext(os.path.basename(src_lib))[0]}_objs"
    if os.path.exists(ldir):
        shutil.rmtree(ldir)
    os.makedirs(ldir)

    shutil.copy(src_lib, ldir)
    lib_to_include = os.path.join(ldir, os.path.basename(src_lib))

    filelist = []
    subdir = 0

    # Extract object files from the archive
    extracted_files = subprocess.check_output([ar, "t", src_lib], text=True).splitlines()
    for f in [file for file in extracted_files if file.endswith('.o')]:
        if os.path.exists(os.path.join(ldir, f)):
            subdir_path = os.path.join(ldir, str(subdir))
            os.makedirs(subdir_path, exist_ok=True)
            subdir += 1
            ar_cmd = [ar, "m", lib_to_include, f]
            print(f"Running: {' '.join(ar_cmd)}")
            subprocess.run(ar_cmd, check=True)

        ext_path = os.path.join(ldir, f)
        ar_cmd = [ar, "p", lib_to_include, f]
        with open(ext_path, "w") as out_file:
            subprocess.run(ar_cmd, stdout=out_file, check=True)
        filelist.append(ext_path)

    ar_cmd = [ar, "rcs", dest_lib] + filelist
    print(f"Running: {' '.join(ar_cmd)}")
    subprocess.run(ar_cmd, check=True)

def extract_and_include_host_whole_static_libs(dest_lib, ar="ar"):
    """Extract and include all host whole static libraries."""
    static_libs = os.environ.get("PRIVATE_ALL_WHOLE_STATIC_LIBRARIES", "").split()
    if static_libs:
        extract_and_include_single_host_whole_static_lib(static_libs[0], dest_lib, ar)
        for lib in static_libs[1:]:
            extract_and_include_single_host_whole_static_lib(lib, dest_lib, ar)

def create_dummy_o_if_no_objs(output_lib):
    """Create a dummy object file if there are no objects (for Darwin)."""
    if not os.environ.get("PRIVATE_ALL_OBJECTS"):
        dummy_path = os.path.join(os.path.dirname(output_lib), "dummy.o")
        print(f"Creating dummy object: {dummy_path}")
        Path(dummy_path).touch()

def get_dummy_o_if_no_objs(output_lib):
    """Get the path to the dummy object file (for Darwin)."""
    if not os.environ.get("PRIVATE_ALL_OBJECTS"):
        return os.path.join(os.path.dirname(output_lib), "dummy.o")
    return ""

def delete_dummy_o_if_no_objs(output_lib, ar="ar"):
    """Delete the dummy object file if it was created (for Darwin)."""
    dummy_path = get_dummy_o_if_no_objs(output_lib)
    if dummy_path:
        ar_cmd = [ar, "d", output_lib, dummy_path]
        print(f"Running: {' '.join(ar_cmd)}")
        subprocess.run(ar_cmd, check=True)
        os.remove(dummy_path)

def transform_host_o_to_static_lib(output_lib, ar="ar", global_arflags="", object_files=None):
    """
    Create a static library from object files, handling dummy objects on Darwin.
    """
    object_files = object_files or []
    tmp_lib = f"{output_lib}.tmp"

    print(f"[BUILD] StaticLib: {os.path.basename(output_lib)} ({output_lib})")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_lib), exist_ok=True)

    # Remove existing archive files
    if os.path.exists(output_lib):
        os.remove(output_lib)
    if os.path.exists(tmp_lib):
        os.remove(tmp_lib)

    # Extract and include all host whole static libraries into the temporary archive
    extract_and_include_host_whole_static_libs(tmp_lib, ar)

    # Handle dummy object on Darwin
    if os.uname().sysname == "Darwin":
        create_dummy_o_if_no_objs(tmp_lib)

    # Build the command to add all objects to the temporary archive
    dummy_obj = get_dummy_o_if_no_objs(tmp_lib)
    all_objects = object_files + ([dummy_obj] if dummy_obj else [])
    ar_cmd = [ar, "rcs", global_arflags, tmp_lib] + all_objects
    print(f"Running: {' '.join(ar_cmd)}")
    subprocess.run(ar_cmd, check=True)

    # Delete the dummy object if it was created (on Darwin)
    if os.uname().sysname == "Darwin":
        delete_dummy_o_if_no_objs(tmp_lib, ar)

    # Move the temporary archive to the final output
    print(f"Moving {tmp_lib} to {output_lib}")
    shutil.move(tmp_lib, output_lib)

def transform_host_o_to_shared_lib_inner(output, private_cxx_link, private_rpath_1, private_rpath_2,
                                         private_host_global_ldflags, private_ldflags, private_crtbegin,
                                         private_all_objects, private_all_whole_static_libraries,
                                         private_group_static_libraries, private_all_static_libraries,
                                         native_coverage, private_host_libprofile_rt, private_libcrt_builtins,
                                         private_all_shared_libraries, private_crtend, private_ldlibs):
    """Transform .o files into a shared library."""

    command = [
        private_cxx_link,
        f"-Wl,-rpath,{private_rpath_1}",
        f"-Wl,-rpath,{private_rpath_2}",
        "-shared",
        f"-Wl,-soname,{os.path.basename(output)}",
        private_host_global_ldflags,
        private_ldflags,
        private_crtbegin,
        private_all_objects,
        "-Wl,--whole-archive",
        private_all_whole_static_libraries,
        "-Wl,--no-whole-archive",
    ]

    if private_group_static_libraries:
        command.extend([
            "-Wl,--start-group",
            private_all_static_libraries,
            "-Wl,--end-group"
        ])
    else:
        command.append(private_all_static_libraries)

    if native_coverage == "true":
        command.append(private_host_libprofile_rt)

    command.extend([
        private_libcrt_builtins,
        private_all_shared_libraries,
        "-o", output,
        private_crtend,
        private_ldlibs
    ])

    return " ".join(command)

def transform_host_o_to_shared_lib(output, display, private_module, private_cxx_link, private_rpath_1,
                                   private_rpath_2, private_host_global_ldflags, private_ldflags,
                                   private_crtbegin, private_all_objects, private_all_whole_static_libraries,
                                   private_group_static_libraries, private_all_static_libraries,
                                   native_coverage, private_host_libprofile_rt, private_libcrt_builtins,
                                   private_all_shared_libraries, private_crtend, private_ldlibs):
    """Wrapper to execute the shared library transformation."""

    # Print message and create directory for the output
    print(f"{display} SharedLib: {private_module} ({output})")
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # Get the full command from the inner transformation
    command = transform_host_o_to_shared_lib_inner(
        output, private_cxx_link, private_rpath_1, private_rpath_2,
        private_host_global_ldflags, private_ldflags, private_crtbegin,
        private_all_objects, private_all_whole_static_libraries,
        private_group_static_libraries, private_all_static_libraries,
        native_coverage, private_host_libprofile_rt, private_libcrt_builtins,
        private_all_shared_libraries, private_crtend, private_ldlibs
    )

    print(f"Command: {command}")
    # Normally, you'd execute the command here using subprocess or equivalent if needed.

def transform_host_o_to_package(output, display, private_module, **kwargs):
    """Transform .o files into a package."""

    # Print message and create directory for the output
    print(f"{display} Package: {private_module} ({output})")
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # Reuse the shared library transformation logic for the package
    transform_host_o_to_shared_lib(output, display, private_module, **kwargs)

def transform_o_to_shared_lib_inner(output, private_cxx_link, private_target_crtbegin_so_o,
                                    private_all_objects, private_all_whole_static_libraries,
                                    private_group_static_libraries, private_all_static_libraries,
                                    native_coverage, private_target_coverage_lib, private_target_libcrt_builtins,
                                    private_target_global_ldflags, private_ldflags, private_all_shared_libraries,
                                    private_target_crtend_so_o, private_ldlibs):
    """Transform .o files into a shared library."""

    command = [
        private_cxx_link,
        "-nostdlib",
        f"-Wl,-soname,{os.path.basename(output)}",
        "-Wl,--gc-sections",
        "-shared",
        private_target_crtbegin_so_o,
        private_all_objects,
        "-Wl,--whole-archive",
        private_all_whole_static_libraries,
        "-Wl,--no-whole-archive",
    ]

    if private_group_static_libraries:
        command.extend([
            "-Wl,--start-group",
            private_all_static_libraries,
            "-Wl,--end-group"
        ])
    else:
        command.append(private_all_static_libraries)

    if native_coverage == "true":
        command.append(private_target_coverage_lib)

    command.extend([
        private_target_libcrt_builtins,
        private_target_global_ldflags,
        private_ldflags,
        private_all_shared_libraries,
        "-o", output,
        private_target_crtend_so_o,
        private_ldlibs
    ])

    return " ".join(command)

def transform_o_to_shared_lib(output, display, private_module, private_cxx_link,
                              private_target_crtbegin_so_o, private_all_objects,
                              private_all_whole_static_libraries, private_group_static_libraries,
                              private_all_static_libraries, native_coverage,
                              private_target_coverage_lib, private_target_libcrt_builtins,
                              private_target_global_ldflags, private_ldflags,
                              private_all_shared_libraries, private_target_crtend_so_o, private_ldlibs):
    """Wrapper to execute the shared library transformation."""

    # Print message and create directory for the output
    print(f"{display} SharedLib: {private_module} ({output})")
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # Get the full command from the inner transformation
    command = transform_o_to_shared_lib_inner(
        output, private_cxx_link, private_target_crtbegin_so_o, private_all_objects,
        private_all_whole_static_libraries, private_group_static_libraries, private_all_static_libraries,
        native_coverage, private_target_coverage_lib, private_target_libcrt_builtins,
        private_target_global_ldflags, private_ldflags, private_all_shared_libraries,
        private_target_crtend_so_o, private_ldlibs
    )

    print(f"Command: {command}")
    # Normally, you'd execute the command here using subprocess or equivalent if needed.

def transform_o_to_static_executable_inner(output, private_cxx_link, private_ldflags,
                                           private_target_crtbegin_static_o, private_target_global_ldflags,
                                           private_all_objects, private_all_whole_static_libraries,
                                           private_all_static_libraries, native_coverage,
                                           private_target_coverage_lib, private_target_libcrt_builtins,
                                           private_target_crtend_o):
    """Transform .o files into a static executable."""

    # Base command using clang++
    command = [
        private_cxx_link,
        "-nostdlib",
        "-Bstatic"
    ]

    # If PRIVATE_LDFLAGS does not include -shared, add -static
    if "-shared" not in private_ldflags:
        command.append("-static")

    # Continue adding the necessary linker and object files
    command.extend([
        "-Wl,--gc-sections",
        "-o", output,
        private_target_crtbegin_static_o,
        private_target_global_ldflags,
        private_ldflags,
        private_all_objects,
        "-Wl,--whole-archive",
        private_all_whole_static_libraries,
        "-Wl,--no-whole-archive"
    ])

    # Filtering out certain libraries
    filtered_static_libs = [lib for lib in private_all_static_libraries.split()
                            if lib not in ["libcompiler_rt.hwasan.a", "libc_nomalloc.hwasan.a", "libc.hwasan.a",
                                           "libcompiler_rt.a", "libc_nomalloc.a", "libc.a"]]

    command.extend(filtered_static_libs)

    # Start group for certain static libraries
    command.append("-Wl,--start-group")

    # Including only specific libc libraries
    command.extend([lib for lib in private_all_static_libraries.split()
                    if lib in ["libc.a", "libc.hwasan.a"]])

    # Adding specific libc_nomalloc libraries
    command.extend([lib for lib in private_all_static_libraries.split()
                    if lib in ["libc_nomalloc.a", "libc_nomalloc.hwasan.a"]])

    # Add coverage library if enabled
    if native_coverage == "true":
        command.append(private_target_coverage_lib)

    # Add specific compiler runtime libraries
    command.extend([lib for lib in private_all_static_libraries.split()
                    if lib in ["libcompiler_rt.a", "libcompiler_rt.hwasan.a"]])

    # Add built-ins and end group
    command.extend([
        private_target_libcrt_builtins,
        "-Wl,--end-group",
        private_target_crtend_o
    ])

    return " ".join(command)

def transform_o_to_static_executable(output, display, private_prefix, private_module, private_cxx_link,
                                     private_ldflags, private_target_crtbegin_static_o,
                                     private_target_global_ldflags, private_all_objects,
                                     private_all_whole_static_libraries, private_all_static_libraries,
                                     native_coverage, private_target_coverage_lib, private_target_libcrt_builtins,
                                     private_target_crtend_o):
    """Wrapper to execute the static executable transformation."""

    # Print message
    print(f"{private_prefix} StaticExecutable: {private_module} ({output})")

    # Create the output directory
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # Get the full command from the inner transformation
    command = transform_o_to_static_executable_inner(
        output, private_cxx_link, private_ldflags, private_target_crtbegin_static_o,
        private_target_global_ldflags, private_all_objects, private_all_whole_static_libraries,
        private_all_static_libraries, native_coverage, private_target_coverage_lib,
        private_target_libcrt_builtins, private_target_crtend_o
    )

    print(f"Command: {command}")
    # Normally, you'd execute the command here using subprocess or equivalent if needed.

def transform_host_o_to_executable_inner(output, private_cxx_link, private_crtbegin, private_all_objects,
                                         private_all_whole_static_libraries, private_group_static_libraries,
                                         private_all_static_libraries, native_coverage, private_host_libprofile_rt,
                                         private_libcrt_builtins, private_all_shared_libraries, private_rpaths,
                                         private_no_default_compiler_flags, private_host_global_ldflags,
                                         private_ldflags, private_crtend, private_ldlibs):
    """Transform .o files into a host executable."""

    # Base command
    command = [
        private_cxx_link,
        private_crtbegin,
        private_all_objects,
        "-Wl,--whole-archive",
        private_all_whole_static_libraries,
        "-Wl,--no-whole-archive"
    ]

    # Check if PRIVATE_GROUP_STATIC_LIBRARIES is enabled
    if private_group_static_libraries:
        command.extend([
            "-Wl,--start-group",
            private_all_static_libraries,
            "-Wl,--end-group"
        ])
    else:
        command.append(private_all_static_libraries)

    # If native coverage is enabled, add the profile runtime library
    if native_coverage == "true":
        command.append(private_host_libprofile_rt)

    # Add built-in libraries and shared libraries
    command.extend([
        private_libcrt_builtins,
        private_all_shared_libraries
    ])

    # Add rpath for each path in PRIVATE_RPATHS
    for path in private_rpaths:
        command.append(f"-Wl,-rpath,\\$$ORIGIN/{path}")

    # Add host global LDFLAGS if PRIVATE_NO_DEFAULT_COMPILER_FLAGS is not set
    if not private_no_default_compiler_flags:
        command.append(private_host_global_ldflags)

    # Add LDFLAGS, output, CRT end, and additional linker libraries
    command.extend([
        private_ldflags,
        "-o", output,
        private_crtend,
        private_ldlibs
    ])

    return " ".join(command)

def transform_host_o_to_executable(output, display, private_prefix, private_module, private_cxx_link,
                                   private_crtbegin, private_all_objects, private_all_whole_static_libraries,
                                   private_group_static_libraries, private_all_static_libraries, native_coverage,
                                   private_host_libprofile_rt, private_libcrt_builtins,
                                   private_all_shared_libraries, private_rpaths,
                                   private_no_default_compiler_flags, private_host_global_ldflags,
                                   private_ldflags, private_crtend, private_ldlibs):
    """Wrapper to execute the host executable transformation."""

    # Print message
    print(f"{private_prefix} Executable: {private_module} ({output})")

    # Create the output directory
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # Get the full command from the inner transformation
    command = transform_host_o_to_executable_inner(
        output, private_cxx_link, private_crtbegin, private_all_objects,
        private_all_whole_static_libraries, private_group_static_libraries, private_all_static_libraries,
        native_coverage, private_host_libprofile_rt, private_libcrt_builtins,
        private_all_shared_libraries, private_rpaths, private_no_default_compiler_flags,
        private_host_global_ldflags, private_ldflags, private_crtend, private_ldlibs
    )

    print(f"Command: {command}")
    # Normally, you'd execute the command here using subprocess or equivalent if needed.

def package_coverage_files(output, private_all_objects, soong_zip, out_dir, merge_zips,
                           private_all_whole_static_libraries):
    """Package native coverage files."""

    # Remove any existing output and related files
    if os.path.exists(output):
        os.remove(output)
    if os.path.exists(f"{output}.lst"):
        os.remove(f"{output}.lst")
    if os.path.exists(f"{output}.premerged"):
        os.remove(f"{output}.premerged")

    # Create a new .lst file and populate it with object files
    with open(f"{output}.lst", "w") as lst_file:
        for obj in private_all_objects:
            lst_file.write(f"{obj}\n")

    # Run SOONG_ZIP to create the .premerged zip file
    soong_zip_command = f"{soong_zip} -o {output}.premerged -C {out_dir} -l {output}.lst"
    print(f"Running SOONG_ZIP command: {soong_zip_command}")
    # subprocess.run(soong_zip_command, shell=True, check=True)  # Uncomment to run

    # Run MERGE_ZIPS to merge the premerged zip with the static libraries
    merge_zips_command = f"{merge_zips} -ignore-duplicates {output} {output}.premerged {' '.join(private_all_whole_static_libraries)}"
    print(f"Running MERGE_ZIPS command: {merge_zips_command}")
    # subprocess.run(merge_zips_command, shell=True, check=True)  # Uncomment to run

def emit_line(word_list, output_file):
    """Appends words from the word_list to the output file."""
    if word_list:
        with open(output_file, 'a') as f:
            f.write(f"{' '.join(word_list)} ")

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd,
                 **kwargs)

def product_copy_files(src: Union[str, Path], dest: Union[str, Path]) -> None:
    """
    Copy all files from the source directory to the destination directory,
    maintaining the directory structure.

    Args:
        src (Union[str, Path]): Source directory to copy files from.
        dest (Union[str, Path]): Destination directory to copy files to.
    """
    src = str(src)    # Ensure src is of type str
    dest = str(dest)    # Ensure dest is of type str

    for root, dirs, files in os.walk(src):
        for file in files:
            src_file = os.path.join(root,
                                    file)    # Use str type for path joining
            rel_path = os.path.relpath(src_file, src)
            dest_file = os.path.join(dest, rel_path)

            # Create destination directory if it does not exist
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)

            # Copy file using shutil.copy2 for better handling
            shutil.copy2(src_file, dest_file)
            print(f"Copied {src_file} to {dest_file}")


def parse_and_copy_files(file_list):
    for entry in file_list:
        if ':' in entry:
            src, dest = entry.split(':')
            dest = dest.format(
                target_product_out=os.environ.get('TARGET_PRODUCT_OUT', ''))
            product_copy_files(src, dest)


def include(module_path):
    module_name = os.path.splitext(os.path.basename(module_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    globals().update(vars(module))
