import os
import zipfile

# Import necessary functions from definitions.py
from definitions import declare_0p_target, intermediates_dir_for

from envsetup import target_product_out, out_dir


def create_directory(path):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory created: {path}")
    else:
        print(f"Directory already exists: {path}")


def zip_files(zip_file_path, files):
    """Zips the provided list of files into the specified zip file."""
    with zipfile.ZipFile(zip_file_path, 'w') as z:
        for file in files:
            if os.path.exists(file):
                z.write(file, arcname=os.path.basename(file))
            else:
                print(f"File {file} not found, skipping.")
    print(f"Created zip file: {zip_file_path}")


def read_file(file_path):
    """Reads a file and returns the list of lines."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read().splitlines()
    else:
        print(f"File {file_path} not found.")
        return []


def merge_owner_files(owners_list):
    """Merges the content of all OWNERS files into a single list."""
    merged_content = []
    for owners_file in owners_list:
        content = read_file(owners_file)
        merged_content.extend(content)  # Append all content from each OWNERS file
    return merged_content


class OwnersArtifactCreator:
    def __init__(self, target_class, target_name, target_type, soong_zip_cmd, owners_list_file):
        # Fetch the TARGET_DEVICE from the environment
        target_device = os.getenv("TARGET_DEVICE", "generic")
        self.target_class = target_class
        self.target_name = target_name
        self.target_type = target_type
        self.soong_zip_cmd = soong_zip_cmd  # Placeholder, assuming a function to invoke zip
        self.owners_list_file = owners_list_file

        # Correct path with TARGET_DEVICE
        self.intermediates_dir = intermediates_dir_for(self.target_class, self.target_name, self.target_type,
                                                       target_product_out=os.path.join(out_dir, "target", "product",
                                                                                       target_device))
        self.owners_zip = os.path.join(self.intermediates_dir, "owners.zip")
        self.all_0p_targets = {}  # Dictionary to store non-copyrightable targets

    def read_owners_list(self):
        """Read the list of OWNER files from the provided file."""
        return read_file(self.owners_list_file)

    def create_owners_zip(self, owners):
        """Create a zip file containing the merged owners."""
        merged_owners_file = os.path.join(self.intermediates_dir, "OWNERS.merged")

        # Merge content of all OWNERS files into one file
        merged_content = merge_owner_files(owners)
        with open(merged_owners_file, 'w') as f:
            for owner in merged_content:
                f.write(f"{owner}\n")

        # Create the zip archive using the merged OWNERS file
        zip_files(self.owners_zip, [merged_owners_file])

        # Clean up the temporary merged file
        os.remove(merged_owners_file)

    def declare_target(self):
        """Declare the owners.zip as a non-copyrightable target."""
        declare_0p_target(self.owners_zip, self.all_0p_targets)

    def run(self):
        """Main function to create the owners artifact and declare the target."""
        owners = self.read_owners_list()
        if owners:
            create_directory(self.intermediates_dir)  # Create the intermediates directory if it doesn't exist
            self.create_owners_zip(owners)
            self.declare_target()
        else:
            print("No OWNERS files found.")


# Example usage
if __name__ == "__main__":
    # Define paths
    target_class = "PACKAGING"
    target_name = "owners"
    target_type = "TARGET"  # Example target type
    soong_zip_cmd = "soong_zip"  # Replace with the actual SOONG_ZIP command or function
    owners_list_file = os.path.join(out_dir, ".module_paths/OWNERS.list")  # Path to the OWNERS.list file

    # Instantiate and run the artifact creator
    creator = OwnersArtifactCreator(target_class, target_name, target_type, soong_zip_cmd, owners_list_file)
    creator.run()
