import os
import subprocess

# Helper function to read the contents of a file
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Define paths
intermediates = os.path.join(target_product_out, 'intermediates', 'PACKAGING', 'owners')
owners_zip = os.path.join(intermediates, 'owners.zip')
owners_list = os.path.join(out_dir, '.module_paths', 'OWNERS.list')

# Create the intermediates directory if it doesn't exist
os.makedirs(intermediates, exist_ok=True)

# Read the owners list
owners = read_file(owners_list).strip().split('\n')

# Private owners with newlines handled
private_owners = "\n".join(owners)

# Function to create the owners zip
def create_owners_zip():
    print("Building artifact to include OWNERS files.")
    if os.path.exists(owners_zip):
        os.remove(owners_zip)
    
    list_file_path = f"{owners_zip}.list"
    with open(list_file_path, 'w') as list_file:
        list_file.write(private_owners)
    
    # Create the zip file using the regular zip command
    subprocess.run(['zip', '-r', owners_zip, '-@'], input=private_owners.encode(), check=True)
    
    os.remove(list_file_path)

# Main function to execute the tasks
def main():
    create_owners_zip()
    print(f"Created {owners_zip}")

if __name__ == "__main__":
    main()
