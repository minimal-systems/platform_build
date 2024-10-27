# Function to get environment variable with default
import os
import importlib.util

def get_env(var, default=''):
    return os.environ.get(var, default)

# Function to handle errors and print messages
def pretty_error(message):
    print(f"Error: {message}")
    exit(1)

# Function to dynamically include a Python file
def include_python_file(filepath):
    spec = importlib.util.spec_from_file_location("arch_config", filepath)
    arch_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch_config)
    return arch_config


# Define the transform-shared-lib-to-toc function
def transform_shared_lib_to_toc(input_file, output_file):
    # Simulate the _gen_toc_command_for_elf function
    #print(f"Generating TOC for ELF file: {input_file} -> {output_file}")
    # Command simulation (replace with actual command logic if needed)
    command = f"objcopy --add-gnu-debuglink={input_file} {output_file}"
    #print(f"Command: {command}")
    # Execute the command (uncomment the following line if you want to execute it)
    #os.system(command)

# Print out variables for debugging purposes
def print_variables():
    for key, value in variables.items():
        print(f"{key} = {value}")

# Example usage of the transform function
def example_usage():
    input_file = "libexample.so"
    output_file = "libexample.toc"
    transform_shared_lib_to_toc(input_file, output_file)

# Determine the path to the arch-variant-specific configuration file
build_combos_dir = get_env('build_combos', f'build/make/core/combo')