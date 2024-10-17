#!/bin/sh

# Store the current working directory in a temporary file
echo $(pwd) > /tmp/build_top
export BUILD_TOP=$(cat /tmp/build_top)
export TOP=$BUILD_TOP
export OUT_DIR=$BUILD_TOP/out
export PYTHONPATH="" # Clear PYTHONPATH
# Disable pycache
export PYTHONDONTWRITEBYTECODE=1

# Check if required Python packages are installed on Arch Linux
check_dependencies() {
    # Check if we are running on Arch Linux
    if [ -f /etc/arch-release ]; then
        REQUIRED_PACKAGES=("python-prettytable" "python-cryptography" "python-termcolor")
        for pkg in "${REQUIRED_PACKAGES[@]}"; do
            if ! pacman -Qs $pkg > /dev/null; then
                echo "Error: $pkg is not installed. Please install it using 'sudo pacman -S $pkg'."
                # Install the package
                sudo pacman -S $pkg

                return 1
            fi
        done
    fi
}

# Run the dependency check
check_dependencies

# Cleanup PYTHONPATH and activate the Python virtual environment
chmod +x ./prebuilts/python/venv/bin/activate
source prebuilts/python/venv/bin/activate

# Parse board_config.py for architecture details
parse_board_config() {
    # Extract the relevant architecture variables from board_config.py using Python
    ARCH_VARS=$(python3 <<END
import os

board_config_path = os.path.join('$BUILD_TOP', "device", "$TARGET_DEVICE", 'board_config.py')

# Define the variables we're interested in
target_vars = {
    'target_cpu_abi': None,
    'target_arch': None,
    'target_arch_variant': None,
    'target_cpu_variant': None,
    'target_2nd_cpu_abi': None,
    'target_2nd_arch': None,
    'target_2nd_arch_variant': None,
    'target_board_platform': None,
    'target_product': None,
    'target_kernel_arch': None,
    'target_kernel': None,
    'target_defconfig': None,
}

# Execute board_config.py in a restricted namespace to extract the variables
namespace = {}
with open(board_config_path, 'r') as f:
    exec(f.read(), namespace)

# Extract the relevant values from the namespace
for key in target_vars.keys():
    target_vars[key] = namespace.get(key, "N/A")

# Print the results as environment variables
for key, value in target_vars.items():
    print(f'export {key.upper()}={value}')

END
)

    # Source the architecture variables into the current environment
    eval "$ARCH_VARS"
}



# Function: croot
# Usage: croot
# Changes directory to the top of the build tree.
function croot() {
    cd "$BUILD_TOP"
}

# Function: lunch
# Usage: lunch <product_name>-<build_variant>
# Selects <product_name> as the product to build and <build_variant> as the variant.
# Example: lunch aosp_arm-eng
function lunch() {
    if [ $# -ne 1 ]; then
        echo "Usage: lunch <product_name>-<build_variant>"
        echo "Selects <product_name> as the product to build, and <build_variant> as the variant."
        return 1
    fi

    # Ensure BUILD_TOP is set
    if [ -z "$BUILD_TOP" ]; then
        echo "Error: BUILD_TOP environment variable must be set."
        return 1
    fi

    # Set LUNCH_MODE to true
    export LUNCH_MODE="true"

    # Extract TARGET_DEVICE and TARGET_BUILD_VARIANT
    TARGET=$1
    TARGET_DEVICE=$(echo "$TARGET" | sed 's/-.*//')
    TARGET_BUILD_VARIANT=$(echo "$TARGET" | sed 's/.*-//')

    # Export target device, product, and build variant
    export TARGET_DEVICE
    export TARGET_PRODUCT=$TARGET_DEVICE
    export TARGET_BUILD_VARIANT

    # Set up PYTHONPATH for the build system
    export PYTHONPATH=$PYTHONPATH:$BUILD_TOP/build/make/core
    export PYTHONPATH=$PYTHONPATH:$BUILD_TOP/build/make/tools
    export PYTHONPATH=$PYTHONPATH:$BUILD_TOP/build/make/common
    export PYTHONPATH=$PYTHONPATH:$BUILD_TOP/build/make/core/combo
    export PYTHONPATH=$PYTHONPATH:$BUILD_TOP/build/make/core/tasks
    export PYTHONPATH=$PYTHONPATH:$BUILD_TOP/build/soong
    export PYTHONPATH=$PYTHONPATH:$BUILD_TOP/device/$TARGET_DEVICE

    # Source build environment and invoke lunch target script
    source "$BUILD_TOP/build/soong/scripts/build-environment.sh"
    python3 "$BUILD_TOP/build/make/core/lunch_target.py" "$TARGET_DEVICE-$TARGET_BUILD_VARIANT"
    # Run the architecture parser
  parse_board_config
}

# Function: build
# Usage: build [options]
# Starts the build using the Soong build system.
function build() {
    python build/core/main.py "$@"
}

# Function: mmm
# Usage: mmm <module>
# Builds the specified module using the Soong build system.
function mmm() {
    python build/soong/main_build.py --module "$@"
}

