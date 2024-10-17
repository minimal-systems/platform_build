import importlib
import os
from envsetup import build_top
from llvm_env import *

# Define a function that replicates the convert-to-clang-flags
def convert_to_clang_flags(flags, unknown_cflags):
    """Filters out unknown clang flags from the provided flags."""
    return list(filter(lambda flag: flag not in unknown_cflags, flags))

clang_config_unknown_cflags = sorted([
    "-finline-functions",
    "-finline-limit=64",
    "-fno-canonical-system-headers",
    "-Wno-clobbered",
    "-fno-devirtualize",
    "-fno-tree-sra",
    "-fprefetch-loop-arrays",
    "-funswitch-loops",
    "-Wmaybe-uninitialized",
    "-Wno-error=clobbered",
    "-Wno-error=maybe-uninitialized",
    "-Wno-extended-offsetof",
    "-Wno-free-nonheap-object",
    "-Wno-literal-suffix",
    "-Wno-maybe-uninitialized",
    "-Wno-old-style-declaration",
    "-Wno-unused-local-typedefs",
    "-fdiagnostics-color",
    "-fuse-init-array",  # http://b/153759688

    # ARM + ARM64
    "-fgcse-after-reload",
    "-frerun-cse-after-loop",
    "-frename-registers",
    "-fno-strict-volatile-bitfields",
    "-fno-align-jumps",

    # ARM
    "-mthumb-interwork",
    "-fno-builtin-sin",
    "-fno-caller-saves",
    "-fno-early-inlining",
    "-fno-move-loop-invariants",
    "-fno-partial-inlining",
    "-fno-tree-copy-prop",
    "-fno-tree-loop-optimize",

    # x86 + x86_64
    "-finline-limit=300",
    "-fno-inline-functions-called-once",
    "-mfpmath=sse",
    "-mbionic",

    # Windows
    "--enable-stdcall-fixup",


])

# clang_default_ub_checks
clang_default_ub_checks = [
    "bool",
    "integer-divide-by-zero",
    "return",
    "returns-nonnull-attribute",
    "shift-exponent",
    "unreachable",
    "vla-bound",
]

# Uncomment the following lines if you decide to include the checks with performance issues
# clang_default_ub_checks += ["alignment", "bounds", "enum", "float-cast-overflow"]
# clang_default_ub_checks += ["float-divide-by-zero", "nonnull-attribute", "null",
#                             "shift-base", "signed-integer-overflow"]

# host config
clang_2nd_arch_prefix = ""

# Example paths for includes, host and target architecture
build_system = f"{build_top}/build/core"
host_2nd_arch = False  # Change to True if using second architecture

# Call function to get target architecture after all imports are done
target_2nd_arch = os.environ.get("TARGET_2ND_ARCH")
target_arch = os.environ.get("TARGET_ARCH")

# Function to dynamically import a module from a file path
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Host and Target configurations
def include_host_config(host_arch):
    host_file_path = f"{build_system}/clang/HOST_{host_arch}.py"
    return import_module_from_path(f"HOST_{host_arch}", host_file_path)

def include_target_config(target_arch):
    target_file_path = f"{build_system}/clang/TARGET_{target_arch}.py"
    return import_module_from_path(f"TARGET_{target_arch}", target_file_path)
# host_2nd_arch config
if host_2nd_arch:
    host_2nd_arch_var_prefix = "host_2nd_prefix"  # Example value
    clang_2nd_arch_prefix = host_2nd_arch_var_prefix
    host_2nd_arch_include = include_host_config("x86_64")  # Example second host arch

# target_2nd_arch config
if target_2nd_arch:
    target_2nd_arch_var_prefix = "target_2nd_prefix"  # Example value
    clang_2nd_arch_prefix = target_2nd_arch_var_prefix
    target_2nd_arch_include = include_target_config("x86_64")  # Example second target arch

from tidy import *