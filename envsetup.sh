#!/bin/sh

# Store the current working directory in a temporary file
echo $(pwd) > /tmp/build_top
export BUILD_TOP=$(cat /tmp/build_top)
export TOP=$BUILD_TOP
export OUT_DIR=$BUILD_TOP/out
export PYTHONPATH="" # Clear PYTHONPATH

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

