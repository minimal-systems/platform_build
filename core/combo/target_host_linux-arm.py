import os
import importlib.util
#from envsetup import *
from combo_vars import *
# Inputs
target_arch = get_env('target_arch', 'arm')
target_arch_variant = get_env('target_arch_variant', '')

# Provide a default variant if not set
if not target_arch_variant.strip():
    target_arch_variant = 'arm'

target_arch_specific_python_file = os.path.join(build_combos_dir, 'arch', target_arch, f"{target_arch_variant}.py")

# Include the arch-variant-specific configuration
arch_config = include_python_file(target_arch_specific_python_file)

target_linker = "/usr/bin/ld",
target_global_yasm_flags = "-f elf64 -m amd64"