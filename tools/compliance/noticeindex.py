# noticeindex.py

from graph import LicenseGraph, TargetNode
import os
import hashlib
import re
from collections import defaultdict

class NoticeIndex:
    """Transforms license metadata into an indexed structure."""

    licenses_path_regexp = re.compile(r"licen[cs]es?/")

    def __init__(self, root_dir, lg, rs):
        self.lg = lg
        self.rs = rs if rs else self.resolve_notices(lg)
        self.root_dir = root_dir

        # Initialize all mappings and variables
        self.hash = {}  # Maps license text filenames to content hashes
        self.text = {}  # Maps content hashes to content
        self.hash_lib_install = defaultdict(lambda: defaultdict(set))  # Maps hashes to libraries to install paths
        self.install_hash_lib = defaultdict(lambda: defaultdict(set))  # Maps install paths to libraries to hashes
        self.lib_hash = defaultdict(set)  # Maps libraries to hashes
        self.target_hashes = defaultdict(set)  # Maps target nodes to hashes
        self.project_name = {}  # Maps project directory names to project name text
        self.files = []  # List of all files accessed during indexing

        # Ensure shipped nodes are set in the LicenseGraph
        if not self.lg.shipped:
            self.lg.set_shipped_nodes(self.get_shipped_nodes())

        # Begin indexing license texts
        self.index_license_texts()

    def index_license_texts(self):
        """Index all license texts for the LicenseGraph."""
        def index_node(tn):
            """Add all license texts for the target node to the index."""
            if tn in self.target_hashes:
                return self.target_hashes[tn]
            hashes = set()
            for text in tn.license_texts():
                filename = text.split(":", 1)[0]
                if filename not in self.hash:
                    self.add_text(filename)
                h = self.hash[filename]
                hashes.add(h)
            self.target_hashes[tn] = hashes
            return hashes

        for tn in self.lg.shipped:
            hashes = index_node(tn)
            install_paths = self.get_install_paths(tn)
            self.link_node(tn, hashes, install_paths)

    def add_text(self, filename):
        """Reads and indexes the content of a license text file."""
        filepath = os.path.join(self.root_dir, filename)
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
                h = hashlib.md5(content).hexdigest()
                self.hash[filename] = h
                self.text[h] = content
                self.files.append(filename)
        except FileNotFoundError:
            print(f"File not found: {filepath}")

    def link_node(self, tn, hashes, install_paths):
        """Link the target node to the indexed hashes and install paths."""
        for h in hashes:
            lib_name = self.get_lib_name(tn, h)
            self.lib_hash[lib_name].add(h)
            for install_path in install_paths:
                self.install_hash_lib[install_path][h].add(lib_name)
                self.hash_lib_install[h][lib_name].add(install_path)

    def get_lib_name(self, tn, h):
        """Derives a library name for the given target node and hash."""
        return f"lib_{h}"

    def get_install_paths(self, tn):
        """Get the install paths for the given target node."""
        return tn.installed() or tn.built()

    def get_shipped_nodes(self):
        """Mock method to get shipped nodes (can be replaced with actual implementation)."""
        return set(self.lg.targets.values())

    def hashes(self):
        """Returns a sorted list of all hashes."""
        return sorted(self.text.keys())

    def hash_libs(self, h):
        """Returns the libraries using the license text hashed as `h`."""
        return sorted(self.hash_lib_install[h].keys())

    def hash_lib_installs(self, h, lib_name):
        """Returns the install paths for a given hash and library."""
        return sorted(self.hash_lib_install[h][lib_name])

    def install_hashes(self, install_path):
        """Returns the hashes associated with an install path."""
        return sorted(self.install_hash_lib[install_path].keys())

    def install_hash_libs(self, install_path, h):
        """Returns the libraries associated with an install path and hash."""
        return sorted(self.install_hash_lib[install_path][h])

    def libraries(self):
        """Returns a sorted list of library names."""
        return sorted(self.lib_hash.keys())

    def install_paths(self):
        """Returns a sorted list of install paths."""
        return sorted(self.install_hash_lib.keys())

    def input_files(self):
        """Returns a sorted list of all files read during indexing."""
        return sorted(self.files)

    def resolve_notices(self, lg):
        """Mock function for resolving notices (can be replaced with actual implementation)."""
        return None

# Example usage with graph.py integration
if __name__ == "__main__":
    # Create some mock TargetNodes with license texts and paths
    node1 = TargetNode("node1", {"license_texts": ["LICENSE:libA"], "installed": ["install/path/libA"]})
    node2 = TargetNode("node2", {"license_texts": ["LICENSE:libB"], "installed": ["install/path/libB"]})

    # Create a LicenseGraph and add nodes to it
    lg = LicenseGraph()
    lg.add_target(node1)
    lg.add_target(node2)
    lg.set_shipped_nodes([node1, node2])

    rs = None  # Assuming ResolutionSet is not used for this example

    # Create a NoticeIndex with the graph and print results
    ni = NoticeIndex(root_dir="", lg=lg, rs=rs)
    print(f"Hashes: {list(ni.hashes())}")
    for h in ni.hashes():
        print(f"Hash: {h}, Libraries: {ni.hash_libs(h)}, Install Paths: {ni.hash_lib_installs(h, f'lib_{h}')}")
