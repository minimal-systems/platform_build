import os
import inspect
from os import mkdir
from pathlib import Path

from cola.widgets.standard import progress
from colorama import Fore, Style, init
from ninja_printer import NinjaStyleTqdm
import sys
from envsetup import *
from definitions import (
    license_metadata_rule,
    non_module_license_metadata_rule,
    record_missing_non_module_dependencies,
    copied_target_license_metadata_rule,
    _copied_target_license_metadata_rule,
    build_all_license_metadata,
    build_license_metadata,
    find_idf_prefix,
    intermediates_dir_for,
    local_intermediates_dir,
    generated_sources_dir_for
)


# Initialize colorama for cross-platform support
init(autoreset=True)

TOTAL_TASKS = 10
progress_bar = NinjaStyleTqdm(TOTAL_TASKS)

# Control printing of detailed information and assertions
PRINT_CONDITIONS = False
def print_result(condition, success_msg, failure_msg):
    emoji = "✅" if condition else "❌"
    progress_bar.print_log(f"{emoji} {Fore.GREEN}{success_msg}" if condition else f"{emoji} {Fore.RED}{failure_msg}")


def setup_modules():
    """Provide a consistent setup for all_modules."""
    return {
        "environment": {
            "name": "environment",
            "delayed_meta_lic": ["meta_lic1", "meta_lic2"],
            "notice_deps": ["vendor_init:dep_suffix"],
            "built": ["out/target/product/generic/rootfs/etc/environment"],
            "installed": ["environment.installed"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
            "license_conditions": ["notice"],
            "notices": ["build/soong/licenses/license"],
            "license_package_name": "package_name1",
            "is_container": True,
            "module_type": "type1",
            "module_class": "class1",
            "license_install_map": {"vendor_init": "/destination/path"},
            "path": ["out/target/product/generic/rootfs/etc/environment"],
        },
        "vendor_init": {
            "name": "vendor_init",
            "built": ["vendor_init.built"],
            "installed": ["vendor_init.installed"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
            "meta_lic": "vendor_init.meta_lic",  # This module has metadata
        },
        "vendor_config": {
            "name": "vendor_config",
            "built": ["vendor_config.built"],
            "installed": ["vendor_config.installed"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
        },
    }


def setup_non_modules():
    """Provide a consistent setup for all_non_modules."""
    return {
        "vendor_config": {
            "name": "vendor_config",
            "dependencies": ["vendor_init", "missing_target"],  # Includes a missing dependency
            "notices": ["build/soong/licenses/notice_vendor"],
            "path": ["out/target/product/generic/rootfs/vendor/etc/config"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
            "license_conditions": ["notice"],
            "root_mappings": ["vendor_init:system/core/init"],
            "is_container": True,
            "license_package_name": "package_name_vendor",
        }
    }


def setup_targets():
    """Initialize an empty dictionary to represent all_targets."""
    return {}


def setup_paths():
    """Provide build paths and command."""
    build_license_metadata_cmd = "build/soong/compliance/build_license_metadata"
    intermediates_dir = "out/target/product/generic/obj/PACKAGING"
    out_dir = "out/target/product/generic"
    return build_license_metadata_cmd, intermediates_dir, out_dir

def print_target_details(all_targets):
    """Print details of all targets if printing conditions are enabled."""
    if PRINT_CONDITIONS:
        progress_bar.print_log(f"{Fore.CYAN}Updated all_targets:{Style.RESET_ALL}")
        for target_name, target_data in all_targets.items():
            progress_bar.print_log(f"{Fore.CYAN}Target: {target_name}{Style.RESET_ALL}")
            for key, value in target_data.items():
                progress_bar.print_log(f"  {key}: {value}")


def run_license_metadata_test():
    """Test the license metadata rule for a module target."""
    progress_bar.display_task("test", "license_metadata_test")

    # Setup modules, targets, and paths
    all_modules = setup_modules()
    all_targets = setup_targets()
    build_license_metadata_cmd, intermediates_dir, out_dir = setup_paths()

    # Prepare the argument file directory path for the target
    target = "environment"
    argument_file_dir = os.path.join(intermediates_dir, "notice", target)

    # Run the license metadata rule for the target
    license_metadata_rule(
        target,
        all_modules,
        all_targets,
        build_license_metadata_cmd,
        intermediates_dir,
        out_dir
    )

    # Print the updated target details
    print_target_details(all_targets)

    # Validate the results with assertions
    print_result(
        len(all_targets) == 2,
        "Expected 2 targets to be added for 'environment'",
        f"Expected 2 targets, but got {len(all_targets)}"
    )
    print_result(
        "environment" in all_targets,
        "'environment' is in the target names",
        "'environment' is not in the target names"
    )



def run_non_module_license_metadata_test():
    """Test the license metadata rule for a non-module target."""
    progress_bar.display_task("Running", "non_module_license_metadata_test")
    all_non_modules = setup_non_modules()
    all_targets = setup_targets()
    build_license_metadata_cmd, out_dir = setup_paths()[:2]

    non_module_license_metadata_rule("vendor_config", all_non_modules, all_targets, build_license_metadata_cmd, out_dir)

    print_target_details(all_targets)
    print_result(len(all_targets) == 1, "Expected 1 target to be added for 'vendor_config'", f"Expected 1 target, but got {len(all_targets)}")


def run_record_missing_dependencies_test():
    """Test recording missing dependencies for non-module targets."""
    progress_bar.display_task("Running", "record_missing_dependencies_test")
    all_non_modules = setup_non_modules()
    all_targets = setup_modules()
    missing_dependencies = []

    record_missing_non_module_dependencies("vendor_config", all_non_modules, all_targets, missing_dependencies)

    progress_bar.print_log(f"{Fore.CYAN}Missing dependencies:{Style.RESET_ALL}")
    for dep in missing_dependencies:
        progress_bar.print_log(f"  {Fore.RED}{dep}{Style.RESET_ALL}")

    print_result(len(missing_dependencies) == 1, "Expected 1 missing dependency for 'vendor_config'", f"Expected 1 missing dependency, but got {len(missing_dependencies)}")


def run_copied_target_license_metadata_test():
    """Test copied target license metadata rule."""
    progress_bar.display_task("Running", "copied_target_license_metadata_test")
    all_targets = setup_modules()
    all_copied_targets = {"vendor_config": {"sources": ["vendor_init"]}}
    copy_license_metadata_cmd = "build/soong/compliance/copy_license_metadata"
    out_dir = "out/target/product/generic"

    _copied_target_license_metadata_rule("vendor_config", all_targets, all_copied_targets, copy_license_metadata_cmd, out_dir)

    print_target_details(all_targets)
    vendor_config_target = all_targets.get("vendor_config", None)
    has_meta_lic = vendor_config_target and "meta_lic" in vendor_config_target
    print_result(has_meta_lic, "'meta_lic' attribute is correctly set for 'vendor_config'", "'meta_lic' attribute is not set for 'vendor_config'")

def run_build_all_license_metadata_test(out_dir):
    """Test the build_all_license_metadata function with a focus on meta_lic files."""
    progress_bar.display_task("Running", "build_all_license_metadata_test")
    all_non_modules = setup_non_modules()
    all_targets = setup_targets()
    all_modules = setup_modules()


    # Run the build process
    build_all_license_metadata(all_non_modules, all_targets, all_modules, out_dir)

    # Verify that only 'meta_lic' files are created
    built_files = list(Path(out_dir).rglob("*.meta_lic"))
    print_result(
        len(built_files) > 0,
        f"Expected at least 1 'meta_lic' file, found {len(built_files)}",
        "No 'meta_lic' files were built."
    )

    # Print details of built 'meta_lic' files
    if built_files:
        progress_bar.print_log("Built 'meta_lic' files:")
        for file in built_files:
            print(f" - {file}")

def run_build_license_metadata_test(out_dir: str):
    """
    Runs the test for building license metadata.

    Args:
        out_dir (str): Output directory where metadata files are expected to be generated.

    Returns:
        None
    """
    progress_bar.display_task("Running", "build_license_metadata_test")

    # Sample data for the test
    all_non_modules = {"vendor_config": {}}
    all_targets = {
        "environment": {
            "name": "environment",
            "meta_lic": ["meta_lic1", "meta_lic2"],
        },
        "vendor_init": {
            "name": "vendor_init",
            "meta_lic": "vendor_init.meta_lic",
        },
    }
    all_modules = {}
    all_copied_targets = {}

    # Ensure the output directory exists
    os.makedirs(out_dir, exist_ok=True)


    try:
        # Call the function to build license metadata
        built_metadata_files = build_license_metadata(
            all_non_modules,
            all_targets,
            all_modules,
            all_copied_targets,
            copy_license_metadata_cmd="",
            out_dir=out_dir,
        )

        # Validate built metadata files
        if not built_metadata_files:
            print("No valid license metadata files found to build.")
        else:
            print(f"✅ Expected at least 1 'meta_lic' file, found {len(built_metadata_files)} \n")
            print("Built 'meta_lic' files:")
            for f in built_metadata_files:
                print(f" - {f}")

    except TypeError as e:
        progress_bar.print_log(f"❌ TypeError occurred: {e}")


def run_idf_prefix_test():
    progress_bar.print_log(find_idf_prefix("", host_cross_os))  # Output: target
    progress_bar.print_log(find_idf_prefix("HOST_CROSS", host_cross_os))  # Output: host_cross
    progress_bar.print_log(find_idf_prefix("something", host_cross_os))  # Output: host_cross
    progress_bar.print_log(find_idf_prefix("something", host_cross_os))  # Output: host

def run_intermediates_dir_for_test():
    """Test the intermediates_dir_for function."""
    progress_bar.display_task("Running", "intermediates_dir_for_test")

    # Simulate target_product_out dynamically (replace with actual if needed)

    # Define the expected directory structure
    expected_dir = os.path.join(target_product_out, "obj", "APPS", "NotePad_intermediates")

    try:
        # Call the function with the test parameters
        result = intermediates_dir_for(
            target_class="APPS",
            target_name="NotePad",
            target_type="TARGET",
            force_common=False,
            second_arch=False,
            host_cross_os=False,
            target_product_out=target_product_out  # Pass the product out directory
        )

        # Compare the result with the expected directory
        if result == expected_dir:
            progress_bar.print_log(f"✅ Expected directory '{expected_dir}' matches the result.")
            os.makedirs(result, exist_ok=True)
        else:
            progress_bar.print_log(f"❌ Expected directory '{expected_dir}' but got '{result}'.")

    except ValueError as e:
        progress_bar.print_log(f"❌ Test failed with error: {e}")

def run_local_intermediates_dir_test():
    """Test the local_intermediates_dir function."""
    progress_bar.display_task("Running", "local_intermediates_dir_test")

    # Simulate target_product_out dynamically (replace with actual if needed)
    target_product_out = os.path.join(os.getcwd(), "out/target/product/generic")

    # Define the expected directory structure
    expected_dir = os.path.join(target_product_out, "obj", "APPS", "NotePad_intermediates")

    try:
        # Call the function with the test parameters
        result = local_intermediates_dir(
            local_module_class="APPS",
            local_module="NotePad",
            local_is_host_module=False,  # Treat it as a target module
            force_common=False,
            second_arch=False,
            host_cross_os=False,
            target_product_out=target_product_out  # Pass the product output directory
        )

        # Compare the result with the expected directory
        if result == expected_dir:
            progress_bar.print_log(f"✅ Expected directory '{expected_dir}' matches the result.")
        else:
            progress_bar.print_log(f"❌ Expected directory '{expected_dir}' but got '{result}'.")

    except ValueError as e:
        print(f"❌ Test failed with error: {e}")

def run_generated_sources_dir_for_test():
    """Test the generated_sources_dir_for function."""
    progress_bar.display_task("Running", "generated_sources_dir_for_test")

    # Define paths following the Android build structure
    target_common_out = out_dir / "target" / "product" / "common"
    out_common_gen = target_common_out / "obj" / "common_gen"
    out_gen = target_common_out / "obj" / "gen"

    try:
        # Test 1: Non-common target directory
        result = generated_sources_dir_for(
            target_class="APPS",
            target_name="NotePad",
            target_type="HOST",
            force_common=False,
            out_gen=out_gen,
            out_common_gen=out_common_gen,
            host_cross_os=False,
            common_module_classes=["target_LIBS"]
        )
        expected_dir = str(out_gen / "APPS" / "NotePad_intermediates")
        print_result(
            result == expected_dir,
            f"Expected directory '{expected_dir}' matches the result.",
            f"Expected {expected_dir}, but got {result}"
        )

        # Test 2: Common target directory (forced common)
        result = generated_sources_dir_for(
            target_class="APPS",
            target_name="NotePad",
            target_type="TARGET",
            force_common=True,
            out_gen=out_gen,
            out_common_gen=out_common_gen
        )
        expected_dir = str(out_common_gen / "APPS" / "NotePad_intermediates")
        print_result(
            result == expected_dir,
            f"Expected directory '{expected_dir}' matches the result.",
            f"Expected {expected_dir}, but got {result}"
        )
        os.makedirs(result, exist_ok=True)

    except ValueError as e:
        progress_bar.print_log(f"Test failed with error: {e}")



if __name__ == "__main__":
    run_copied_target_license_metadata_test()
    run_license_metadata_test()
    run_non_module_license_metadata_test()
    run_record_missing_dependencies_test()
    run_build_all_license_metadata_test(out_dir)
    run_build_license_metadata_test(out_dir)
    run_idf_prefix_test()
    run_intermediates_dir_for_test()
    run_local_intermediates_dir_test()
    run_generated_sources_dir_for_test()
    progress_bar.finish()
