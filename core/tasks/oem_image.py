import os
import subprocess
from envsetup import target_product_out, out_dir, target_device
from definitions import declare_1p_container, intermediates_dir_for
from device_info import *

# Paths from environment or defaults
target_out_oem = os.path.join(str(target_product_out), "oem")
# Ensure the correct output path includes `out/target/product/generic/obj/PACKAGING/oem_image_intermediates`
oemimage_intermediates = intermediates_dir_for("PACKAGING", "oem_image", target_product_out=str(target_product_out))
installed_oemimage_target = os.path.join(str(target_product_out), "oem.img")
board_oemimage_partition_size = target_board_oem_size

# Error handling for missing OEM partition size
if not board_oemimage_partition_size:
    raise ValueError("BOARD_OEMIMAGE_PARTITION_SIZE is not set.")

# Gather the modules installed in the OEM directory
all_default_installed_modules = []  # Replace with actual logic to gather installed modules
internal_oemimage_files = [f for f in all_default_installed_modules if f.startswith(target_out_oem)]


def generate_image_prop_dictionary(output_file, image_type, **kwargs):
    """
    Generate the image property dictionary. Write properties to the given output file.

    Args:
        output_file (str): The file to write the properties.
        image_type (str): Type of the image (e.g., "oem").
        kwargs: Additional properties to add (e.g., skip_fsck).
    """
    with open(output_file, 'w') as f:
        f.write(f"image_type={image_type}\n")
        for key, value in kwargs.items():
            f.write(f"{key}={value}\n")
    print(f"Image property dictionary generated at {output_file}")


def assert_max_image_size(image_path, max_size):
    """
    Assert that the image does not exceed the maximum partition size.

    Args:
        image_path (str): Path to the image.
        max_size (str): Maximum allowed size (e.g., "500MB").

    Raises:
        ValueError: If the image exceeds the max size.
    """
    image_size = os.path.getsize(image_path)
    max_size_bytes = int(max_size.rstrip('MB')) * 1024 * 1024

    if image_size > max_size_bytes:
        raise ValueError(f"Image size {image_size} exceeds maximum size {max_size_bytes}.")
    print(f"Image size {image_size} is within the allowed limit of {max_size_bytes} bytes.")


def build_image(target_out_oem, oem_image_info_path, installed_oemimage_target, env):
    """
    Builds the OEM image using the generated image properties.
    """
    print(f"Building image with info from {oem_image_info_path}")

    # Convert the partition size to bytes, assuming it is in MB
    try:
        partition_size_mb = int(board_oemimage_partition_size.rstrip('MB'))
    except ValueError:
        raise ValueError(f"Invalid partition size format: {board_oemimage_partition_size}")

    # Enforce the 512 MB size limit
    max_partition_size_mb = 512
    if partition_size_mb > max_partition_size_mb:
        print(f"Warning: OEM partition size exceeds the 512 MB limit. Limiting to {max_partition_size_mb} MB.")
        partition_size_mb = max_partition_size_mb

    partition_size_bytes = partition_size_mb * 1024 * 1024

    # Print the calculated partition size
    print(f"OEM Partition size: {partition_size_mb} MB ({partition_size_bytes} bytes)")

    # Create the image file using dd
    print(f"Creating image file: {installed_oemimage_target} with size {partition_size_mb} MB")
    dd_command = [
        "dd", "if=/dev/zero", f"of={installed_oemimage_target}", "bs=1M", f"count={partition_size_mb}"
    ]

    dd_result = subprocess.run(dd_command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if dd_result.returncode != 0:
        stderr_message = dd_result.stderr.decode() if dd_result.stderr else "No error message"
        raise RuntimeError(f"Failed to create image file with dd: {stderr_message}")

    print(f"Image file created: {installed_oemimage_target}")

    # Command to create the ext4 filesystem on the image file
    command = [
        "mke2fs",
        "-t", "ext4",
        "-d", target_out_oem,
        "-L", "oem",  # Label for the image
        installed_oemimage_target
    ]

    result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if the process was successful
    if result.returncode != 0:
        stderr_message = result.stderr.decode() if result.stderr else "No error message"
        raise RuntimeError(f"Failed to build the image: {stderr_message}")

    print(f"OEM image built successfully: {installed_oemimage_target}")

    # Shrink the image using resize2fs to minimize size
    print(f"Shrinking the OEM image to the minimum size")
    resize_command = ["resize2fs", "-M", installed_oemimage_target]
    resize_result = subprocess.run(resize_command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if resize_result.returncode != 0:
        stderr_message = resize_result.stderr.decode() if resize_result.stderr else "No error message"
        raise RuntimeError(f"Failed to shrink the image: {stderr_message}")

    print(f"OEM image shrunk successfully.")


def dist_for_goals(goal, target):
    """
    Placeholder function for 'dist-for-goals' behavior.

    Args:
        goal (str): The build goal (e.g., "oem_image").
        target (str): The target to distribute.
    """
    print(f"Distributing {target} for goal {goal}")
    # Add actual distribution logic here if needed


def build_oem_image():
    """
    Function to create the OEM image.
    """
    print(f"Target OEM fs image: {installed_oemimage_target}")

    # Create necessary directories
    os.makedirs(target_out_oem, exist_ok=True)
    os.makedirs(oemimage_intermediates, exist_ok=True)

    # Clear previous image info
    oem_image_info_path = os.path.join(oemimage_intermediates, "oem_image_info.txt")
    if os.path.exists(oem_image_info_path):
        os.remove(oem_image_info_path)

    # Generate the image property dictionary
    generate_image_prop_dictionary(
        oem_image_info_path,
        "oem",
        skip_fsck="true",
        oem_partition_size=f"{board_oemimage_partition_size}"
    )

    # Add paths to internal binaries if required
    internal_userimages_binary_paths = os.getenv('INTERNAL_USERIMAGES_BINARY_PATHS', '')
    env = os.environ.copy()
    env["PATH"] = f"{internal_userimages_binary_paths}:{env['PATH']}"

    # Call the build_image function with the corrected argument order
    build_image(target_out_oem, oem_image_info_path, installed_oemimage_target, env)

    # Ensure image does not exceed partition size
    assert_max_image_size(installed_oemimage_target, board_oemimage_partition_size)

    # Declare license for the OEM image
    declare_1p_container(
        target=installed_oemimage_target,
        project_path=target_out_oem,  # Set actual project path
        all_non_modules={},  # Replace with the actual non-modules dictionary
        all_targets={},  # Replace with the actual targets dictionary
        out_dir=out_dir,
    )

    print(f"OEM image built and placed at: {installed_oemimage_target}")


def main():
    """
    Main function to build the OEM image if requested.
    """
    build_oem_image()

    # Distribute the OEM image
    dist_for_goals("oem_image", installed_oemimage_target)


if __name__ == "__main__":
    main()
