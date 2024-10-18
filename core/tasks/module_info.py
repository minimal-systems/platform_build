import os
import json
from blueprint_parser import parse_module_info_file
from envsetup import target_product_out, soong_out_dir, host_out_executables

# Paths from environment setup (envsetup)
PRODUCT_OUT = str(target_product_out)  # `target_product_out` from `envsetup`
SOONG_OUT_DIR = str(soong_out_dir)  # `soong_out_dir` from `envsetup`
HOST_OUT_EXECUTABLES = str(host_out_executables)  # `host_out_executables` from `envsetup`

# File paths
MODULE_INFO_JSON = os.path.join(PRODUCT_OUT, "module-info.json")
SOONG_MODULE_INFO = os.path.join(SOONG_OUT_DIR, f"module-info-{os.getenv('TARGET_PRODUCT', 'generic')}{os.getenv('COVERAGE_SUFFIX', '')}.json")

# Define helper functions to create the JSON structure
def write_optional_json_list(key, value_list):
    """Writes a JSON list field if the list is not empty."""
    if value_list:
        return {key: value_list}
    return {}

def write_optional_json_bool(key, value):
    """Writes a JSON boolean field if the value is set."""
    if value:
        return {key: str(value).lower()}
    return {}

def generate_module_info_json(module_info_path, soong_module_info_path, verbose=False):
    """Generate the module-info.json using parsed data from blueprint files."""
    # Parse module files from the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO.list"
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Create the JSON object
    module_info = {}
    for config in all_configs:
        module_name = config.get('name', 'unknown')
        module_info[module_name] = {
            "module_name": module_name,
            **write_optional_json_list("class", config.get('class', [])),
            **write_optional_json_list("path", config.get('path', [])),
            **write_optional_json_list("tags", config.get('tags', [])),
            **write_optional_json_list("installed", config.get('installed', [])),
            **write_optional_json_list("compatibility_suites", config.get('compatibility_suites', [])),
            **write_optional_json_list("auto_test_config", config.get('auto_test_config', [])),
            **write_optional_json_list("test_config", config.get('test_config', [])),
            **write_optional_json_list("dependencies", config.get('dependencies', [])),
            **write_optional_json_list("required", config.get('required', [])),
            **write_optional_json_list("shared_libs", config.get('shared_libs', [])),
            **write_optional_json_list("static_libs", config.get('static_libs', [])),
            **write_optional_json_list("system_shared_libs", config.get('system_shared_libs', [])),
            **write_optional_json_list("srcs", config.get('srcs', [])),
            **write_optional_json_list("srcjars", config.get('srcjars', [])),
            **write_optional_json_list("classes_jar", config.get('classes_jar', [])),
            **write_optional_json_list("test_mainline_modules", config.get('test_mainline_modules', [])),
            **write_optional_json_bool("is_unit_test", config.get('is_unit_test', False)),
            **write_optional_json_list("test_options_tags", config.get('test_options_tags', [])),
            **write_optional_json_list("data", config.get('data', [])),
            **write_optional_json_list("runtime_dependencies", config.get('runtime_dependencies', [])),
            **write_optional_json_list("static_dependencies", config.get('static_dependencies', [])),
            **write_optional_json_list("data_dependencies", config.get('data_dependencies', [])),
            **write_optional_json_list("supported_variants", config.get('supported_variants', [])),
            **write_optional_json_list("host_dependencies", config.get('host_dependencies', [])),
            **write_optional_json_list("target_dependencies", config.get('target_dependencies', [])),
            **write_optional_json_bool("test_module_config_base", config.get('test_module_config_base', False)),
            **write_optional_json_list("src" or "srcs", config.get('src', False)),
        }

    # Merge the parsed JSON with the SOONG module info
    try:
        with open(soong_module_info_path, 'r') as soong_file:
            soong_data = json.load(soong_file)
            module_info.update(soong_data)
    except FileNotFoundError:
        print(f"Warning: SOONG module info file {soong_module_info_path} not found.")

    # Write the resulting JSON to the target path
    with open(MODULE_INFO_JSON, 'w') as module_info_file:
        json.dump(module_info, module_info_file, indent=2)
        print(f"Generated module info JSON at {MODULE_INFO_JSON}")

# Generate module-info.json and all_modules.txt
def generate_all_modules_txt(module_info):
    """Generate all_modules.txt containing all module names."""
    all_modules_txt_path = os.path.join(PRODUCT_OUT, "all_modules.txt")
    with open(all_modules_txt_path, 'w') as f:
        for module_name in module_info.keys():
            f.write(module_name + "\n")
    print(f"Generated all_modules.txt at {all_modules_txt_path}")

def main(verbose=False):
    """Main function to generate module-info.json."""
    generate_module_info_json(MODULE_INFO_JSON, SOONG_MODULE_INFO, verbose)

    # Generate all_modules.txt based on module_info.json
    with open(MODULE_INFO_JSON, 'r') as f:
        module_info = json.load(f)
    generate_all_modules_txt(module_info)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Module Info JSON Generator")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
