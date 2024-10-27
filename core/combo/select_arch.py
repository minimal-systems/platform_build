import os
import importlib.util
import platform
#from envsetup import *

def get_env(var, default=''):
    """
    Retrieve an environment variable with a default value if not set.
    """
    return os.environ.get(var, default)

def pretty_error(message):
    """
    Print an error message and exit the program.
    """
    print(f"Error: {message}")
    exit(1)

def include_python_file(filepath):
    """
    Dynamically include a Python file based on its path.
    """
    spec = importlib.util.spec_from_file_location("arch_config", filepath)
    arch_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch_config)
    return arch_config

def setup_combo_configuration():
    """
    Set up the combo configuration based on system details and environment variables.
    """
    combo_os = platform.system().lower()
    combo_arch = platform.machine().lower()
    combo_target = 'TARGET_' + get_env('combo_target', 'HOST_').upper()
    combo_2nd_arch_prefix = get_env('combo_2nd_arch_prefix', '')
    combo_os_arch = combo_os if combo_target == 'HOST_' else f"{combo_os}-{combo_arch}"
    combo_var_prefix = f"{combo_2nd_arch_prefix}{combo_target}"

    # Error if cross-compiling for the host is attempted
    if combo_target == 'HOST_CROSS_':
        pretty_error(f"{combo_var_prefix}GLOBAL_ARFLAGS and {combo_var_prefix}STATIC_LIB_SUFFIX are not supported in Make")

    # Set default values for archiver flags and static library suffix
    variables = {
        f"{combo_var_prefix}global_arflags": "crsPD --format=gnu",
        f"{combo_var_prefix}static_lib_suffix": ".a"
    }

    build_combos_dir = get_env('BUILD_COMBOS', 'build/make/core/combo')
    combo_file = os.path.join(build_combos_dir, f"{combo_target.lower()}{combo_os_arch}.py")

    # Check if the combo file exists, and include it if found
    if os.path.isfile(combo_file):
        # Uncomment the following line if debugging information about included files is needed
        # print(f"Including combo file: {combo_file}")
        include_python_file(combo_file)
    else:
        pretty_error(f"Combo file not found: {combo_file}")

    return variables

def print_variables(variables):
    """
    Print variables for debugging purposes.
    """
    for key, value in variables.items():
        print(f"{key} = {value}")

if __name__ == "__main__":
    try:
        # Set up configuration and print variables
        variables = setup_combo_configuration()
        print_variables(variables)
    except ValueError as e:
        pretty_error(str(e))
