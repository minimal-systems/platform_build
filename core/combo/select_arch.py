import os
import importlib.util
import platform
from envsetup import *

"""
Function to get an environment variable with a default value if not set
"""
def get_env(var, default=''):
    return os.environ.get(var, default)

"""
Function to handle errors and print messages
This function prints the error message and exits the program
"""
def pretty_error(message):
    print(f"Error: {message}")
    exit(1)

combo_os = platform.system().lower()
combo_arch = platform.machine().lower()
combo_target = 'TARGET_' + get_env('combo_target', 'HOST_').upper()
combo_2nd_arch_prefix = get_env('combo_2nd_arch_prefix', '')
combo_os_arch = combo_os if combo_target == 'HOST_' else f"{combo_os}-{combo_arch}"
combo_var_prefix = f"{combo_2nd_arch_prefix}{combo_target}"

variables = {}

"""
Error if cross-compiling for the host is attempted
"""
if combo_target == 'HOST_CROSS_':
    pretty_error(f"{combo_var_prefix}GLOBAL_ARFLAGS and {combo_var_prefix}STATIC_LIB_SUFFIX are not supported in Make")
else:
    """
    Set default values for archiver flags and static library suffix
    """
    variables[f"{combo_var_prefix}global_arflags"] = "crsPD --format=gnu"
    variables[f"{combo_var_prefix}static_lib_suffix"] = ".a"

    build_combos_dir = get_env('BUILD_COMBOS', 'build/make/core/combo')
    combo_file = os.path.join(build_combos_dir, f"{combo_target.lower()}{combo_os_arch}.py")

    """
    Function to dynamically include a Python file based on its path
    """
    def include_python_file(filepath):
        spec = importlib.util.spec_from_file_location("arch_config", filepath)
        arch_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arch_config)
        return arch_config

    """
    Check if the combo file exists, and include it if found
    """
    if os.path.isfile(combo_file):
        # Uncomment the following line if debugging information about included files is needed
        # print(f"Including combo file: {combo_file}")
        arch_config = include_python_file(combo_file)
    else:
        """
        If the combo file does not exist, raise an error
        """
        pretty_error(f"Combo file not found: {combo_file}")

"""
Print out variables for debugging purposes
Iterates over the dictionary and prints each key-value pair
"""
def print_variables():
    for key, value in variables.items():
        print(f"{key} = {value}")

"""
Main script entry point
If the script is run directly, attempt to print variables and catch any ValueError
"""
if __name__ == "__main__":
    try:
        print_variables()
    except ValueError as e:
        pretty_error(str(e))
