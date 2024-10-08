from definitions import (
    license_metadata_rule,
    non_module_license_metadata_rule,
    record_missing_non_module_dependencies,
    copied_target_license_metadata_rule,
    _copied_target_license_metadata_rule,
)
import os
from colorama import Fore, Style, init

# Initialize colorama for cross-platform support
init(autoreset=True)

# Control printing of detailed information and assertions
PRINT_CONDITIONS = True
PROGRESS_EMOJIS = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]

# Index for tracking progress
progress_index = 0


def update_progress():
    """Print the current progress using moon phase emojis."""
    global progress_index
    print(PROGRESS_EMOJIS[progress_index % len(PROGRESS_EMOJIS)],
          end=" ",
          flush=True)
    progress_index += 1


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
            "license_install_map": {
                "vendor_init": "/destination/path"
            },
            "path": ["out/target/product/generic/rootfs/etc/environment"],
        },
        "vendor_init": {
            "name": "vendor_init",
            "built": ["vendor_init.built"],
            "installed": ["vendor_init.installed"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
            "meta_lic": "vendor_init.meta_lic"    # This module has metadata
        },
        "vendor_config": {
            "name": "vendor_config",
            "built": ["vendor_config.built"],
            "installed": ["vendor_config.installed"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"]
        }
    }


def setup_non_modules():
    """Provide a consistent setup for all_non_modules."""
    return {
        "vendor_config": {
            "name": "vendor_config",
            "dependencies": ["vendor_init", "missing_target"
                            ],    # Includes a missing dependency
            "notices": ["build/soong/licenses/notice_vendor"],
            "path": ["out/target/product/generic/rootfs/vendor/etc/config"],
            "license_kinds": ["spdx-license-identifier-apache-2.0"],
            "license_conditions": ["notice"],
            "root_mappings": ["vendor_init:/vendor/path"],
            "is_container": True,
            "license_package_name": "package_name_vendor"
        }
    }


def setup_targets():
    """Initialize an empty dictionary to represent all_targets."""
    return {}


def setup_paths():
    """Provide build paths and command."""
    build_license_metadata_cmd = "build/soong/compliance/build_license_metadata"
    intermediates_dir = "out/target/product/generic"
    out_dir = "out/target/product/generic"
    return build_license_metadata_cmd, intermediates_dir, out_dir


def print_result(condition, success_msg, failure_msg):
    """Print result based on condition with emojis."""
    emoji = "✅" if condition else "❌"
    print(f"{emoji} {Fore.GREEN}{success_msg}{Style.RESET_ALL}"
          if condition else f"{emoji} {Fore.RED}{failure_msg}{Style.RESET_ALL}")


def print_target_details(all_targets):
    """Print details of all targets if printing conditions are enabled."""
    if PRINT_CONDITIONS:
        print(f"{Fore.CYAN}Updated all_targets:{Style.RESET_ALL}")
        for target_name, target_data in all_targets.items():
            print(f"{Fore.CYAN}Target: {target_name}{Style.RESET_ALL}")
            for key, value in target_data.items():
                print(f"  {key}: {value}")


def run_license_metadata_test():
    """Test the license metadata rule for a module target."""
    update_progress()
    all_modules = setup_modules()
    all_targets = setup_targets()
    build_license_metadata_cmd, intermediates_dir, out_dir = setup_paths()

    print(
        f"{Fore.CYAN}Running license metadata rule for 'environment'...\n{Style.RESET_ALL}"
    )
    license_metadata_rule("environment", all_modules, all_targets,
                          build_license_metadata_cmd, intermediates_dir,
                          out_dir)

    print_target_details(all_targets)

    # Perform assertions with print results
    print_result(
        len(all_targets) == 2,
        "Expected 2 targets to be added for 'environment'",
        f"Expected 2 targets, but got {len(all_targets)}")
    print_result("environment" in all_targets,
                 "'environment' is in the target names",
                 "'environment' is not in the target names")


def run_non_module_license_metadata_test():
    """Test the license metadata rule for a non-module target."""
    update_progress()
    all_non_modules = setup_non_modules()
    all_targets = setup_targets()
    build_license_metadata_cmd, out_dir = setup_paths()[:2]

    print(
        f"{Fore.CYAN}Running non-module license metadata rule for 'vendor_config'...\n{Style.RESET_ALL}"
    )
    non_module_license_metadata_rule("vendor_config", all_non_modules,
                                     all_targets, build_license_metadata_cmd,
                                     out_dir)

    print_target_details(all_targets)
    print_result(
        len(all_targets) == 1,
        "Expected 1 target to be added for 'vendor_config'",
        f"Expected 1 target, but got {len(all_targets)}")


def run_record_missing_dependencies_test():
    """Test recording missing dependencies for non-module targets."""
    update_progress()
    all_non_modules = setup_non_modules()
    all_targets = setup_modules()
    missing_dependencies = []

    print(
        f"{Fore.CYAN}Running record missing dependencies for 'vendor_config'...\n{Style.RESET_ALL}"
    )
    record_missing_non_module_dependencies("vendor_config", all_non_modules,
                                           all_targets, missing_dependencies)

    print(f"{Fore.CYAN}Missing dependencies:{Style.RESET_ALL}")
    for dep in missing_dependencies:
        print(f"  {Fore.RED}{dep}{Style.RESET_ALL}")

    print_result(
        len(missing_dependencies) == 1,
        "Expected 1 missing dependency for 'vendor_config'",
        f"Expected 1 missing dependency, but got {len(missing_dependencies)}")


def run_copied_target_license_metadata_test():
    """Test copied target license metadata rule."""
    update_progress()
    all_targets = setup_modules()
    all_copied_targets = {"vendor_config": {"sources": ["vendor_init"]}}
    copy_license_metadata_cmd = "build/soong/compliance/copy_license_metadata"
    out_dir = "out/target/product/generic"

    print(
        f"{Fore.CYAN}Running copied target license metadata rule for 'vendor_config'...\n{Style.RESET_ALL}"
    )
    _copied_target_license_metadata_rule("vendor_config", all_targets,
                                         all_copied_targets,
                                         copy_license_metadata_cmd, out_dir)

    print_target_details(all_targets)
    vendor_config_target = all_targets.get("vendor_config", None)
    has_meta_lic = vendor_config_target and "meta_lic" in vendor_config_target
    print_result(has_meta_lic,
                 "'meta_lic' attribute is correctly set for 'vendor_config'",
                 "'meta_lic' attribute is not set for 'vendor_config'")

    # No assertions, just print the output


# Run all tests
if __name__ == "__main__":
    run_copied_target_license_metadata_test()
    run_license_metadata_test()
    run_non_module_license_metadata_test()
    run_record_missing_dependencies_test()
    # Final progress print
    print(
        f"\n{Fore.CYAN}All test cases executed successfully! {PROGRESS_EMOJIS[-1]}{Style.RESET_ALL}"
    )
