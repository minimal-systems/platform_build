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
                           out_dir):
    """
    Internal function to process license metadata rules for a given target and meta_lic.

    Args:
        target (str): The target for which the license metadata rule applies.
        meta_lic (str): The specific meta license being processed.
        all_modules (dict): Dictionary representing all modules with their attributes, where keys are module names
                            and values are dictionaries of attributes.
        all_targets (dict): Dictionary representing all targets with their attributes, where keys are target names
                            and values are dictionaries of attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        intermediates_dir (str): Directory path for intermediate files.
        out_dir (str): The base output directory for the build.

    Returns:
        tuple: The output and error messages from the build command.
    """
    # Retrieve the module attributes from all_modules
    module = all_modules.get(target)
    if not module:
        return None, f"Module '{target}' not found"

    # Extract module attributes
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

    # Ensure license_install_map is a dictionary, convert if necessary
    license_install_map = module.get("license_install_map", {})
    if not isinstance(license_install_map, dict):
        install_map = {}
        for entry in license_install_map:
            if ':' in entry:
                src, dest = entry.split(':', 1)
                install_map[src] = dest
            else:
                print(f"Invalid entry in license_install_map: {entry}")
    else:
        install_map = license_install_map

    # Retrieve sources for the notice_deps
    sources = {}
    for dep_name in notice_deps:
        dep_module = all_modules.get(dep_name)
        if dep_module:
            sources[dep_name] = dep_module.get(
                "installed", dep_module.get("built", dep_name))

    # Retrieve dependencies for the notice_deps
    deps = {}
    for dep_name in notice_deps:
        dep_meta_lic = all_targets.get(dep_name, {}).get("meta_lic")
        if dep_meta_lic:
            deps[dep_name] = dep_meta_lic

    # Prepare license_install_map entries
    for src, dest in install_map.items():
        src_module = all_modules.get(src)
        if src_module:
            source_files = src_module.get("installed",
                                          src_module.get("built", src))
            install_map[src] = [f"{file}:{dest}" for file in source_files]

    # Prepare argument file path
    argument_file = os.path.join(out_dir, "intermediates", "PACKAGING",
                                 "notice", target, "arguments")

    # Prepare command arguments to dump into the file
    args_to_dump = {
        "-mn":
            module_name if (module_name := target) else "",
        "-mt":
            f'"{module_type}"' if module_type else "",
        "-mc":
            f'"{module_class}"' if module_class else "",
        "-k":
            f'"{" ".join(sorted(license_kinds))}"' if license_kinds else "",
        "-c":
            f'"{" ".join(sorted(license_conditions))}"'
            if license_conditions else "",
        "-n":
            f'"{" ".join(sorted(notices))}"' if notices else "",
        "-d":
            f'"{",".join(sorted(deps.values()))}"' if deps else "",
        "-s":
            f'"{",".join(sorted(sum(sources.values(), [])))}"'
            if sources else "",
        "-m":
            f'"{",".join(sorted(sum(install_map.values(), [])))}"'
            if install_map else "",
        "-t":
            f'"{" ".join(sorted(built))}"' if built else "",
        "-i":
            f'"{" ".join(sorted(installed))}"' if installed else "",
        "-r":
            f'"{" ".join(sorted(path))}"' if path else ""
    }

    # Remove empty arguments
    args_to_dump = {k: v for k, v in args_to_dump.items() if v}

    # Create directories and write arguments to the argument file
    os.makedirs(os.path.dirname(argument_file), exist_ok=True)
    with open(argument_file, 'w') as file:
        file.write("\n".join([f"{k} {v}" for k, v in args_to_dump.items()]))

    # Read the argument file and format arguments correctly
    with open(argument_file, 'r') as file:
        argument_content = " ".join(
            line.strip() for line in file if line.strip())

    # Update all_targets with the metadata (as a dictionary entry)
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
        "private_module_name": module_name,
        "private_module_type": module_type,
        "private_module_class": module_class,
        "private_argument_file": argument_file
    }

    # Construct the build command with correctly formatted arguments
    build_command = f"OUT_DIR={out_dir} {build_license_metadata_cmd} "
    if is_container:
        build_command += "--is_container "
    build_command += f"-p '{license_package_name}' {argument_content} -o {meta_lic}"

    try:
        # Execute the build command and capture the output and error
        result = subprocess.run(build_command,
                                shell=True,
                                check=True,
                                capture_output=True,
                                text=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr


def license_metadata_rule(target, all_modules, all_targets,
                          build_license_metadata_cmd, intermediates_dir,
                          out_dir):
    """
    License metadata build rule for the given target.

    Args:
        target (str): The target for which license metadata needs to be built.
        all_modules (dict): Dictionary of all module attributes, where keys are module names and values are dictionaries of attributes.
        all_targets (dict): Dictionary of all target attributes, where keys are target names and values are dictionaries of attributes.
        build_license_metadata_cmd (str): Command to build license metadata.
        intermediates_dir (str): Directory path for intermediate files.
        out_dir (str): The base output directory for the build.

    Returns:
        None: The function updates the `all_targets` dictionary in place.
    """
    # Retrieve the module information from all_modules using the target as the key
    module = all_modules.get(target, {})

    # Retrieve the delayed meta licenses from the module if it exists, otherwise use an empty list
    delayed_meta_lics = module.get("delayed_meta_lic", [])

    # Call the _license_metadata_rule function for each delayed_meta_lic found in the module attributes
    for meta_lic in delayed_meta_lics:
        _license_metadata_rule(
            target=target,
            meta_lic=meta_lic,
            all_modules=all_modules,
            all_targets=all_targets,
            build_license_metadata_cmd=build_license_metadata_cmd,
            intermediates_dir=intermediates_dir,
            out_dir=out_dir,
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
                                    "packaging", "notice",
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


def copied_target_license_metadata_rule(target_name: str,
                                        all_targets: dict) -> None:
    """
    Wrapper function to check if the given target's `meta_lic` attribute is defined.
    If not, calls `_copied_target_license_metadata_rule` for further processing.

    Args:
        target_name (str): The name of the target to check.
        all_targets (dict): Dictionary of target attributes with target names as keys.

    Returns:
        None: Calls `_copied_target_license_metadata_rule` if `meta_lic` is not defined.
    """
    # Directly retrieve the target from the dictionary
    target = all_targets.get(target_name)

    if not target:
        print(
            f"{Fore.RED}Target '{target_name}' not found in all_targets.{Style.RESET_ALL}"
        )
        return

    # Check if the target has a 'meta_lic' attribute
    if not target.get("meta_lic"):
        # Call the internal function to handle further operations
        print(
            f"{Fore.CYAN}Calling _copied_target_license_metadata_rule for '{target_name}'...\n{Style.RESET_ALL}"
        )
        # You would pass additional arguments required for _copied_target_license_metadata_rule here.
        # Replace `None` placeholders with actual arguments as needed.
        _copied_target_license_metadata_rule(target_name,
                                             all_targets,
                                             all_copied_targets={},
                                             copy_license_metadata_cmd="",
                                             out_dir="")
    else:
        print(
            f"{Fore.YELLOW}'meta_lic' is already defined for target '{target_name}', no action required.{Style.RESET_ALL}"
        )


def _copied_target_license_metadata_rule(target_name, all_targets,
                                         all_copied_targets,
                                         copy_license_metadata_cmd, out_dir):
    """
    License metadata build rule for copied target, using dictionaries.

    Args:
        target_name (str): The name of the target to check and update.
        all_targets (dict): Dictionary where keys are target names and values are dictionaries with attributes.
        all_copied_targets (dict): Dictionary where keys are copied target names and values are dictionaries with attributes and source dependencies.
        copy_license_metadata_cmd (str): Command to copy license metadata.
        out_dir (str): The base output directory for the build.

    Returns:
        None: Updates the `all_targets` dictionary in place if necessary.
    """
    # Retrieve the target dictionary from all_targets
    target = all_targets.get(target_name, None)
    if not target:
        print(
            f"{Fore.RED}Target '{target_name}' not found in all_targets.{Style.RESET_ALL}"
        )
        return

    # Set intermediate variables
    _dir = os.path.join(out_dir, "intermediates", "PACKAGING", "copynotice",
                        target_name)
    _meta = os.path.join(_dir, f"{target_name}.meta_lic")
    _dep = None

    # Assign `meta_lic` to the target
    target["meta_lic"] = _meta

    # Retrieve the copied target information from all_copied_targets
    copied_target = all_copied_targets.get(target_name, None)
    if not copied_target:
        print(
            f"{Fore.RED}Copied target '{target_name}' not found in all_copied_targets.{Style.RESET_ALL}"
        )
        return

    # Retrieve sources for the copied target
    sources = copied_target.get("sources", [])
    if not sources:
        print(
            f"{Fore.RED}No sources found for copied target '{target_name}'.{Style.RESET_ALL}"
        )
        return

    # Find metadata of each source target in all_targets
    for source_name in sources:
        source_target = all_targets.get(source_name, None)
        source_meta = source_target.get("meta_lic") if source_target else None

        if _dep is None:
            _dep = source_meta
        elif _dep != source_meta:
            raise ValueError(
                f"Cannot copy target from multiple modules: {target_name} from {_dep} and {source_meta}"
            )

    if not _dep:
        raise ValueError(
            f"Cannot copy target from unknown module: {target_name} from {sources}"
        )

    # Create argument file directory
    argument_file = os.path.join(_dir, "arguments")
    os.makedirs(os.path.dirname(argument_file), exist_ok=True)

    # Create argument file content
    args_to_dump = [
        f"-i {target_name}", f"-s {' '.join(sources)}", f"-d {_dep}"
    ]
    with open(argument_file, 'w') as file:
        file.write("\n".join(args_to_dump))

    # Construct the build command
    build_command = f"OUT_DIR={out_dir} {copy_license_metadata_cmd} "
    build_command += f"@{argument_file} -o {_meta}"

    print(f"Executing: {build_command}")
    # Uncomment to execute the command if needed:
    # subprocess.run(build_command, shell=True, check=True, capture_output=True, text=True)

    # Update the target metadata with additional information
    target.update({
        "private_dest_target": target_name,
        "private_source_targets": sources,
        "private_source_metadata": _dep,
        "private_argument_file": argument_file
    })
    print(f"Updated target metadata for copied target: {target_name}")

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
