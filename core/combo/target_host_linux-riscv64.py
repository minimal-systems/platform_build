import os
import importlib.util
from envsetup import *

# Function to get environment variable with default
def get_env(var, default=''):
    return os.environ.get(var, default)

# Function to handle errors and print messages
def pretty_error(message):
    print(f"Error: {message}")
    exit(1)

# Inputs
target_arch = get_env('target_arch', 'riscv64')
target_arch_variant = get_env('target_arch_variant', '')

# Provide a default variant if not set
if not target_arch_variant.strip():
    target_arch_variant = 'rv64imafdc'

# Determine the path to the arch-variant-specific configuration file
build_combos_dir = get_env('build_combos', f'build/make/core/combo')
target_arch_specific_python_file = os.path.join(build_combos_dir, 'arch', target_arch, f"{target_arch_variant}.py")
#print(f"Including {target_arch_specific_python_file}")

# Check if the configuration file exists
if not os.path.isfile(target_arch_specific_python_file):
    pretty_error(f"Unknown {target_arch} architecture version: {target_arch_variant}")

# Function to dynamically include a Python file
def include_python_file(filepath):
    spec = importlib.util.spec_from_file_location("arch_config", filepath)
    arch_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch_config)
    return arch_config

# Include the arch-variant-specific configuration
arch_config = include_python_file(target_arch_specific_python_file)import os
import importlib.util
from envsetup import *

# Function to get environment variable with default
def get_env(var, default=''):
    return os.environ.get(var, default)

# Function to handle errors and print messages
def pretty_error(message):
    print(f"Error: {message}")
    exit(1)

# Inputs
target_arch = get_env('target_arch', 'riscv64')
target_arch_variant = get_env('target_arch_variant', '')

# Provide a default variant if not set
if not target_arch_variant.strip():
    target_arch_variant = 'rv64imafdc'  # Default RISC-V variant with standard extensions

# Determine the path to the arch-variant-specific configuration file
build_combos_dir = get_env('build_combos', 'build/make/core/combo')
target_arch_specific_python_file = os.path.join(build_combos_dir, 'arch', target_arch, f"{target_arch_variant}.py")

# Check if the configuration file exists
if not os.path.isfile(target_arch_specific_python_file):
    pretty_error(f"Unknown {target_arch} architecture version: {target_arch_variant}")

# Function to dynamically include a Python file
def include_python_file(filepath):
    spec = importlib.util.spec_from_file_location("arch_config", filepath)
    arch_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch_config)
    return arch_config

# Include the arch-variant-specific configuration
arch_config = include_python_file(target_arch_specific_python_file)

# Target-specific flags for RISC-V 64-bit architecture
target_linker = "/usr/bin/riscv64-linux-gnu-ld"
target_global_yasm_flags = "-f elf64 -m rv64imafdc"
target_cflags = [
    "-march=rv64imafdc",
    "-mabi=lp64d",
    "-mcmodel=medany",
    "-O2",  # Optimization flag for performance
    "-fno-plt",  # Avoid PLT (Procedure Linkage Table) for performance and security
    "-fno-exceptions",  # Disable exceptions to reduce binary size
    "-fno-rtti",  # Disable runtime type information
]
target_ldflags = [
    "-Wl,-O1",  # Linker optimization
    "-Wl,--hash-style=gnu",  # Use GNU hash style for faster symbol resolution
    "-Wl,--no-undefined",  # Ensure all symbols are defined at link time
    "-Wl,--build-id",  # Add build ID for easier debugging
]

# Define the transform-shared-lib-to-toc function
def transform_shared_lib_to_toc(input_file, output_file):
    # Simulate the _gen_toc_command_for_elf function
    print(f"Generating TOC for ELF file: {input_file} -> {output_file}")
    # Command simulation (replace with actual command logic if needed)
    command = f"riscv64-linux-gnu-objcopy --add-gnu-debuglink={input_file} {output_file}"
    print(f"Command: {command}")
    # Execute the command (uncomment the following line if you want to execute it)
    # os.system(command)

# Print out variables for debugging purposes
def print_variables():
    variables = {
        'target_arch': target_arch,
        'target_arch_variant': target_arch_variant,
        'target_linker': target_linker,
        'target_global_yasm_flags': target_global_yasm_flags,
        'target_cflags': target_cflags,
        'target_ldflags': target_ldflags
    }
    for key, value in variables.items():
        print(f"{key} = {value}")

# Example usage of the transform function
def example_usage():
    input_file = "libexample.so"
    output_file = "libexample.toc"
    transform_shared_lib_to_toc(input_file, output_file)

if __name__ == "__main__":
    try:
        print_variables()
        example_usage()
    except ValueError as e:
        pretty_error(str(e))


target_linker = "/usr/bin/ld",
target_global_yasm_flags = "-f elf64 -m rv64imafdc"

# Define the transform-shared-lib-to-toc function
def transform_shared_lib_to_toc(input_file, output_file):
    # Simulate the _gen_toc_command_for_elf function
    print(f"Generating TOC for ELF file: {input_file} -> {output_file}")
    # Command simulation (replace with actual command logic if needed)
    command = f"objcopy --add-gnu-debuglink={input_file} {output_file}"
    print(f"Command: {command}")
    # Execute the command (uncomment the following line if you want to execute it)
    # os.system(command)

# Print out variables for debugging purposes
def print_variables():
    for key, value in variables.items():
        print(f"{key} = {value}")

# Example usage of the transform function
def example_usage():
    input_file = "libexample.so"
    output_file = "libexample.toc"
    transform_shared_lib_to_toc(input_file, output_file)

if __name__ == "__main__":
    try:
        print_variables()
        example_usage()
    except ValueError as e:
        pretty_error(str(e))
