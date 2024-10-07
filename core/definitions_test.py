# test_definitions.py

from definitions import license_metadata_rule, non_module_license_metadata_rule, record_missing_non_module_dependencies, copied_target_license_metadata_rule
import os
from colorama import Fore, Style, init

# Initialize colorama for cross-platform support
init(autoreset=True)

# Setup sample data for module and non-module tests
def setup_modules():
    """Provide a consistent setup for all_modules."""
    return [
        {
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
            "license_install_map": ["vendor_init:/destination/path"],
            "path": ["out/target/product/generic/rootfs/etc/environment"],
        },
        {
            "name": "vendor_init",
            "built": ["vendor_init.built"],
            "installed": ["vendor_init.installed"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
            "meta_lic": "vendor_init.meta_lic"  # This module has metadata
        }
    ]

def setup_non_modules():
    """Provide a consistent setup for all_non_modules."""
    return [
        {
            "name": "vendor_config",
            "dependencies": ["vendor_init", "missing_target"],  # Includes a missing dependency
            "notices": ["build/soong/licenses/notice_vendor"],
            "path": ["out/target/product/generic/rootfs/vendor/etc/config"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
            "license_conditions": ["notice"],
            "root_mappings": ["vendor_init:/vendor/path"],
            "is_container": True,
            "license_package_name": "package_name_vendor"
        }
    ]

def setup_targets(is_non_module=False):
    """
    Initialize an empty all_targets structure.

    Args:
        is_non_module (bool): If True, return a dictionary for non-module targets.
                              If False, return a list for module targets.

    Returns:
        list or dict: An empty list for module targets, and an empty dictionary for non-module targets.
    """
    return []  # Always return a list as targets, since we're using lists instead of dicts

def setup_paths():
    """Provide build paths and command."""
    build_license_metadata_cmd = "build/soong/compliance/build_license_metadata"
    intermediates_dir = "out/target/product/generic"
    out_dir = "out/target/product/generic"
    return build_license_metadata_cmd, intermediates_dir, out_dir

def print_result(condition, success_msg, failure_msg):
    """Prints result based on condition with colors."""
    if condition:
        print(f"{Fore.GREEN}PASS: {success_msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}FAIL: {failure_msg}{Style.RESET_ALL}")

def run_license_metadata_test():
    """Run the license metadata test for module target using print statements."""
    # Setup the sample modules, targets, and paths
    all_modules = setup_modules()
    all_targets = setup_targets()
    build_license_metadata_cmd, intermediates_dir, out_dir = setup_paths()

    # Run the license metadata rule for the target "environment"
    print(f"{Fore.CYAN}Running license metadata rule for 'environment'...\n{Style.RESET_ALL}")
    license_metadata_rule("environment", all_modules, all_targets, build_license_metadata_cmd, intermediates_dir, out_dir)

    # Print the results of all_targets
    print(f"{Fore.CYAN}Updated all_targets:{Style.RESET_ALL}")
    for target in all_targets:
        print(f"{Fore.CYAN}Target: {target['name']}{Style.RESET_ALL}")
        for key, value in target.items():
            print(f"  {key}: {value}")

    # Perform manual assertions with colored print statements
    print_result(len(all_targets) == 2, "Expected 2 targets to be added for 'environment'", f"Expected 2 targets, but got {len(all_targets)}")

    # Check that target names are correct
    target_names = [target["name"] for target in all_targets]
    print_result("environment" in target_names, "'environment' is in the target names", "'environment' is not in the target names")

    # Find the target for environment
    environment_target = next((target for target in all_targets if target["name"] == "environment"), None)
    print_result(environment_target is not None, "'environment' target found", "'environment' target not found")

    # Validate individual fields
    print_result(environment_target["meta_lic"] in ["meta_lic1", "meta_lic2"], "meta_lic set correctly", "meta_lic not set correctly")
    print_result(environment_target["private_kinds"] == ["spdx-license-identifier-apache-2.0"], "License kinds set correctly", "License kinds not set correctly")
    print_result(environment_target["private_conditions"] == ["notice"], "License conditions set correctly", "License conditions not set correctly")
    print_result(environment_target["private_notices"] == ["build/soong/licenses/license"], "Notices set correctly", "Notices not set correctly")
    print_result(environment_target["private_installed"] == ["environment.installed"], "Installed paths set correctly", "Installed paths not set correctly")

    # Check that built and installed paths are set correctly
    print_result(environment_target["private_targets"] == ["out/target/product/generic/rootfs/etc/environment"], "Built paths set correctly", "Built paths not set correctly")
    print_result(environment_target["private_path"] == ["out/target/product/generic/rootfs/etc/environment"], "Path set correctly", "Path not set correctly")

    # Validate notice dependencies and install map
    print_result(environment_target["private_notice_deps"] == ["meta_lic1:dep_suffix", "meta_lic2:dep_suffix"], "Notice dependencies set correctly", f"Notice dependencies not set correctly, got {environment_target['private_notice_deps']}")
    print_result(environment_target["private_install_map"] == ["vendor_init:/destination/path"], "Install map set correctly", "Install map not set correctly")

    print(f"\n{Fore.CYAN}All assertions completed for license_metadata_rule!{Style.RESET_ALL}")

def run_non_module_license_metadata_test():
    """Run the license metadata test for non-module target using print statements."""
    # Setup the sample non-modules, targets, and paths
    all_non_modules = setup_non_modules()  # Now returns a dictionary
    all_targets = setup_targets()  # This will be a list for non-modules
    build_license_metadata_cmd, out_dir = setup_paths()[:2]  # Get paths without intermediates_dir

    # Run the non-module license metadata rule for the target "vendor_config"
    print(f"{Fore.CYAN}Running non-module license metadata rule for 'vendor_config'...\n{Style.RESET_ALL}")
    non_module_license_metadata_rule("vendor_config", all_non_modules, all_targets, build_license_metadata_cmd, out_dir)

    # Print the results of all_targets
    print(f"{Fore.CYAN}Updated all_targets (Non-Module):{Style.RESET_ALL}")
    for target in all_targets:  # Iterate over list elements instead of dictionary items
        print(f"{Fore.CYAN}Target: {target['name']}{Style.RESET_ALL}")
        for key, value in target.items():
            print(f"  {key}: {value}")

    # Perform manual assertions with colored print statements
    print_result(len(all_targets) == 1, "Expected 1 target to be added for 'vendor_config'", f"Expected 1 target, but got {len(all_targets)}")

    # Validate individual fields for "vendor_config"
    vendor_config_target = next((t for t in all_targets if t["name"] == "vendor_config"), {})
    print_result(vendor_config_target.get("private_notice_deps") == ["vendor_init:dep_suffix"], "Notice dependencies set correctly", f"Notice dependencies not set correctly, got {vendor_config_target.get('private_notice_deps')}")
    print_result(vendor_config_target.get("private_notices") == ["build/soong/licenses/notice_vendor"], "Notices set correctly", f"Notices not set correctly, got {vendor_config_target.get('private_notices')}")
    print_result(vendor_config_target.get("private_is_container"), "Is container set correctly", "Is container not set correctly")
    print_result(vendor_config_target.get("private_install_map") == "vendor_init:/vendor/path", "Install map set correctly", "Install map not set correctly")

    print(f"\n{Fore.CYAN}All assertions completed for non_module_license_metadata_rule!{Style.RESET_ALL}")


def run_record_missing_dependencies_test():
    """Run the record missing dependencies test for non-module targets using print statements."""
    # Setup the sample non-modules, targets, and missing dependencies
    all_non_modules = setup_non_modules()
    all_targets = setup_modules()  # Use modules as targets to simulate the environment
    missing_dependencies = []  # Empty list to collect missing dependencies

    # Run the record_missing_non_module_dependencies function for "vendor_config"
    print(f"{Fore.CYAN}Running record missing dependencies for 'vendor_config'...\n{Style.RESET_ALL}")
    record_missing_non_module_dependencies("vendor_config", all_non_modules, all_targets, missing_dependencies)

    # Print the results of missing_dependencies
    print(f"{Fore.CYAN}Missing dependencies:{Style.RESET_ALL}")
    for dep in missing_dependencies:
        print(f"  {Fore.RED}{dep}{Style.RESET_ALL}")

    # Perform manual assertions with colored print statements
    print_result(len(missing_dependencies) == 1, "Expected 1 missing dependency for 'vendor_config'", f"Expected 1 missing dependency, but got {len(missing_dependencies)}")
    print_result("missing_target" in missing_dependencies, "'missing_target' is in the missing dependencies list", "'missing_target' is not in the missing dependencies list")

    print(f"\n{Fore.CYAN}All assertions completed for record_missing_non_module_dependencies!{Style.RESET_ALL}")


def run_copied_target_license_metadata_test():
    """Run the copied target license metadata rule test using print statements."""
    all_targets = setup_modules()  # Using setup_modules as targets

    print(f"{Fore.CYAN}Running copied target license metadata rule for 'vendor_config'...\n{Style.RESET_ALL}")
    copied_target_license_metadata_rule("vendor_config", all_targets)

    # Print the updated targets list
    print(f"{Fore.CYAN}Updated all_targets (Copied Target):{Style.RESET_ALL}")
    for target in all_targets:
        print(f"{Fore.CYAN}Target: {target['name']}{Style.RESET_ALL}")
        for key, value in target.items():
            print(f"  {key}: {value}")

    # Verify that 'vendor_config' now has 'meta_lic' set
    vendor_config_target = next((t for t in all_targets if t["name"] == "vendor_config"), None)
    has_meta_lic = vendor_config_target and "meta_lic" in vendor_config_target
    print_result(has_meta_lic, "'meta_lic' attribute is correctly set for 'vendor_config'", "'meta_lic' attribute is not set for 'vendor_config'")


# Run the tests without pytest
if __name__ == "__main__":
    run_license_metadata_test()
    run_non_module_license_metadata_test()
    run_record_missing_dependencies_test()
    run_copied_target_license_metadata_test()
