# noticeindex.py

import hashlib
import os
import re
from collections import defaultdict
from graph import LicenseGraph


# Placeholder for projectmetadata module and classes
class ProjectMetadataIndex:
    """Dummy implementation for indexing project metadata."""
    def __init__(self, root_fs):
        self.root_fs = root_fs

    def metadata_for_projects(self, *projects):
        return ["project1_metadata", "project2_metadata"]

    def all_metadata_files(self):
        return ["metadata_file1", "metadata_file2"]

class NoticeIndex:
    """
    NoticeIndex transforms license metadata into license text hashes, library
    names, and install paths, indexing them for fast lookup and iteration.

    Attributes:
        lg (LicenseGraph): License graph to which the index applies.
        pmix (ProjectMetadataIndex): Indexes project metadata.
        rs (ResolutionSet): Set of resolutions upon which the index is based.
        shipped (TargetNodeSet): Set of target nodes shipped directly or as derivative works.
        root_fs (FileSystem): Root file system to read the files.
        hash (dict): Maps license text filenames to content hashes.
        text (dict): Maps content hashes to content.
        hash_lib_install (dict): Maps hashes to libraries and their install paths.
        install_hash_lib (dict): Maps install paths to libraries and their hashes.
        lib_hash (dict): Maps libraries to hashes.
        target_hashes (dict): Maps target nodes to hashes.
        project_name (dict): Maps project directory names to project name text.
        files (list): List of all files accessed during indexing.
    """
    licenses_path_regexp = re.compile(r'licen[cs]es?/')

    def __init__(self, lg, root_fs, rs=None):
        self.lg = lg
        self.pmix = ProjectMetadataIndex(root_fs)
        self.rs = rs or self.resolve_notices(lg)
        self.shipped = self.shipped_nodes(lg)
        self.root_fs = root_fs
        self.hash = {}
        self.text = {}
        self.hash_lib_install = defaultdict(lambda: defaultdict(set))
        self.install_hash_lib = defaultdict(lambda: defaultdict(set))
        self.lib_hash = defaultdict(set)
        self.target_hashes = defaultdict(set)
        self.project_name = {}
        self.files = []

    def add_text(self, file):
        """Reads and indexes the content of a license text file."""
        with open(file, 'rb') as f:
            text = f.read()
            hash_value = hashlib.md5(text).hexdigest()
            self.hash[file] = hash_value
            self.text[hash_value] = text
            self.files.append(file)

    def index_license_texts(self, tn):
        """Adds all license texts for the given target node to the index."""
        if tn in self.target_hashes:
            return self.target_hashes[tn]

        hashes = set()
        for text in tn.license_texts():
            fname = text.split(":")[0]
            if fname not in self.hash:
                self.add_text(fname)

            hash_value = self.hash[fname]
            hashes.add(hash_value)

        self.target_hashes[tn] = hashes
        return hashes

    def link(self, tn, hashes, install_paths):
        """Links license hashes, libraries, and install paths."""
        for h in hashes:
            lib_name = self.get_lib_name(tn, h)
            self.lib_hash[lib_name].add(h)

            for install_path in install_paths:
                self.install_hash_lib[install_path][h].add(lib_name)
                self.hash_lib_install[h][lib_name].add(install_path)

    def get_lib_name(self, tn, h):
        """Returns the name of the library associated with a given license text hash."""
        for text in tn.license_texts():
            fname, pname = (text.split(":", 1) if ":" in text else (text, ""))
            if self.hash.get(fname) == h:
                return pname or self.project_name.get(tn)

        return self.project_name.get(tn, "unknown_lib")

    def resolve_notices(self, lg):
        """Dummy function to resolve notices (placeholder)."""
        return {}

    def shipped_nodes(self, lg):
        """Dummy function to get shipped nodes (placeholder)."""
        return set()


class ResolutionSet:
    """Dummy ResolutionSet for demonstration purposes."""
    def __init__(self):
        pass

class TargetNodeSet:
    """Dummy TargetNodeSet for demonstration purposes."""
    def __init__(self):
        pass

class TargetNode:
    """Dummy TargetNode representing nodes in a LicenseGraph."""
    def license_texts(self):
        return ["file1:LibraryA", "file2:LibraryB"]

# Example usage
if __name__ == '__main__':
    # Demonstrate the usage of NoticeIndex with dummy data
    lg = LicenseGraph()
    ni = NoticeIndex(lg, root_fs=None)
    tn = TargetNode()
    hashes = ni.index_license_texts(tn)
    ni.link(tn, hashes, ["install/path/libA", "install/path/libB"])
    print("Libraries:", ni.lib_hash)
