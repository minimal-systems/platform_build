# Copyright (C) 2024 The Minimal Systems Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import subprocess

# Host-specific flags
HOST_GLOBAL_ARFLAGS = "cqs"
HOST_CUSTOM_LD_COMMAND = True

def transform_shared_lib_to_toc(lib_path, output_path):
    """Generates a table of contents (TOC) for a shared library (Mach-O format)."""
    _gen_toc_command_for_macho(lib_path, output_path)

def _gen_toc_command_for_macho(lib_path, output_path):
    """
    Placeholder for the function that generates TOC for Mach-O binaries.
    
    This function would typically contain the logic or call a tool
    that processes the shared library and generates the TOC.
    """
    # Example command for generating TOC. Adjust or replace with actual implementation/tool:
    command = f"otool -L {lib_path} > {output_path}"
    result = os.system(command)
    
    if result != 0:
        raise RuntimeError(f"Failed to generate TOC for {lib_path}")

def transform_host_o_to_shared_lib(output_file, private_cxx, objects, static_libs, shared_libs, ldlibs, ldflags, no_default_flags=False):
    """Transforms object files to a shared library for Darwin systems."""
    command = [
        private_cxx,
        "-dynamiclib",
        "-single_module",
        "-read_only_relocs", "suppress"
    ]
    
    # Add default compiler flags if not disabled
    if not no_default_flags:
        command.extend(ldflags)
    
    command.extend(objects)
    command.extend(f"-force_load {lib}" for lib in static_libs)
    command.extend(shared_libs)
    command.extend(ldlibs)
    
    command.extend([
        "-o", output_file,
        "-install_name", f"@rpath/{os.path.basename(output_file)}",
        "-Wl,-rpath,@loader_path/../lib",
        "-Wl,-rpath,@loader_path/lib"
    ])
    
    # Run the command
    result = subprocess.run(command, shell=False)
    if result.returncode != 0:
        raise RuntimeError("Failed to transform object files to shared library.")

def transform_host_o_to_executable(output_file, private_cxx, objects, static_libs, shared_libs, ldlibs, ldflags, rpaths, no_default_flags=False):
    """Transforms object files to an executable for Darwin systems."""
    command = [
        private_cxx,
        "-o", output_file,
        "-Wl,-headerpad_max_install_names"
    ]
    
    # Add RPATHs
    for path in rpaths:
        command.append(f"-Wl,-rpath,@loader_path/{path}")
    
    # Add default compiler flags if not disabled
    if not no_default_flags:
        command.extend(ldflags)
    
    command.extend(shared_libs)
    command.extend(objects)
    command.extend(static_libs)
    command.extend(ldlibs)
    
    # Run the command
    result = subprocess.run(command, shell=False)
    if result.returncode != 0:
        raise RuntimeError("Failed to transform object files to executable.")

# Example usage:
# transform_shared_lib_to_toc('/path/to/shared/lib.dylib', '/path/to/output/toc.txt')
# transform_host_o_to_shared_lib('output.dylib', 'clang++', ['obj1.o', 'obj2.o'], ['lib1.a'], ['shared1.dylib'], ['-framework CoreFoundation'], ['-arch x86_64'])
# transform_host_o_to_executable('output_executable', 'clang++', ['obj1.o', 'obj2.o'], ['lib1.a'], ['shared1.dylib'], ['-framework CoreFoundation'], ['-arch x86_64'], ['/usr/local/lib'])
