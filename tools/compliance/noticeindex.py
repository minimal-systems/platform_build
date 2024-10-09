# noticeindex.py

import re
import hashlib
import os
from collections import defaultdict
from typing import Dict, Set, List

from graph import LicenseGraph, TargetNode, TargetEdgePath
from policy_walk import WalkTopDown, NoEdgeContext
from resolution import ResolutionSet, ResolveNotices
# Regular expression to match 'license' paths
licenses_path_regexp = re.compile(r'licen[cs]es?/')

# Placeholder for safe prefixes (you may need to adjust these according to your project)
safe_prebuilt_prefixes = []
safe_path_prefixes = []

# Implementing minimal versions of missing modules and functions

# Placeholder for WalkTopDown function (since 'walk' module is missing)
def WalkTopDown(context, lg: LicenseGraph, visit_fn):
    """
    Simulates a top-down traversal of the license graph.
    Since the actual implementation is not available, this is a simplified version.
    """
    # Assuming lg.Targets() returns the list of target nodes
    for tn in lg.Targets():
        path = TargetEdgePath()  # Empty path for simplicity
        if not visit_fn(lg, tn, path):
            continue

# Placeholder for NoEdgeContext class
class NoEdgeContext:
    pass

# Placeholder for ProjectMetadataIndex class (since 'projectmetadata' module is missing)
class ProjectMetadataIndex:
    def __init__(self, root_fs):
        pass

    def MetadataForProjects(self, *projects):
        # Return empty metadata for simplicity
        return []

    def AllMetadataFiles(self):
        return []

# Placeholder for ProjectMetadata class
class ProjectMetadata:
    def VersionedName(self):
        return ""

# Placeholder for resolution functions and classes
def ResolveNotices(lg: LicenseGraph):
    # Return an empty ResolutionSet for simplicity
    return ResolutionSet()

def ShippedNodes(lg: LicenseGraph):
    # Return a set of all targets in the graph as shipped nodes
    return set(lg.Targets())

class ResolutionSet:
    def Resolutions(self, tn: TargetNode):
        # Return an empty list for simplicity
        return []

class Hash:
    """
    Represents an opaque string derived from md5sum.
    """
    def __init__(self, key: str):
        self.key = key

    def __str__(self):
        return self.key

    def __eq__(self, other):
        if isinstance(other, Hash):
            return self.key == other.key
        return False

    def __hash__(self):
        return hash(self.key)

class NoticeIndex:
    """
    Transforms license metadata into license text hashes, library names,
    and install paths, indexing them for fast lookup/iteration.
    """

    def __init__(self, root_fs, lg: LicenseGraph, rs: ResolutionSet):
        self.lg = lg
        self.pmix = ProjectMetadataIndex(root_fs)
        self.rs = rs
        self.shipped = ShippedNodes(lg)
        self.root_fs = root_fs

        self.hash: Dict[str, Hash] = {}  # Maps license text filenames to content hashes
        self.text: Dict[Hash, bytes] = {}  # Maps content hashes to content

        # Maps hashes to libraries to install paths
        self.hash_lib_install: Dict[Hash, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        # Maps install paths to libraries to hashes
        self.install_hash_lib: Dict[str, Dict[Hash, Set[str]]] = defaultdict(lambda: defaultdict(set))
        # Maps libraries to hashes
        self.lib_hash: Dict[str, Set[Hash]] = defaultdict(set)
        # Maps target nodes to hashes
        self.target_hashes: Dict[TargetNode, Set[Hash]] = {}
        # Maps project directory names to project name text
        self.project_name: Dict[str, str] = {}
        # Lists all the files accessed during indexing
        self.files: List[str] = []

    @staticmethod
    def IndexLicenseTexts(root_fs, lg: LicenseGraph, rs: ResolutionSet = None):
        """
        Creates a hashed index of license texts for `lg` and `rs`
        using the files rooted at `root_fs`.
        """
        if rs is None:
            rs = ResolveNotices(lg)
        ni = NoticeIndex(root_fs, lg, rs)

        # Function to index all license texts for a target node
        def index(tn: TargetNode):
            if tn in ni.target_hashes:
                return ni.target_hashes[tn]
            hashes = set()
            for text in tn.LicenseTexts():
                fname = text.split(":", 1)[0]
                if fname not in ni.hash:
                    err = ni.addText(fname)
                    if err:
                        raise err
                hash_value = ni.hash[fname]
                hashes.add(hash_value)
            ni.target_hashes[tn] = hashes
            return hashes

        # Function to link hashes to libraries and install paths
        def link(tn: TargetNode, hashes: Set[Hash], install_paths: List[str]):
            for h in hashes:
                lib_name = ni.getLibName(tn, h)
                ni.lib_hash[lib_name].add(h)
                for install_path in install_paths:
                    ni.install_hash_lib[install_path][h].add(lib_name)
                    ni.hash_lib_install[h][lib_name].add(install_path)

        # Start indexing
        try:
            def walk_fn(lg, tn, path):
                if tn not in ni.shipped:
                    return False
                install_paths = getInstallPaths(tn, path)
                hashes = index(tn)
                link(tn, hashes, install_paths)
                if tn.IsContainer():
                    return True
                for r in ni.rs.Resolutions(tn):
                    hashes = index(r.actsOn)
                    link(r.actsOn, hashes, install_paths)
                return False

            WalkTopDown(NoEdgeContext(), lg, walk_fn)
        except Exception as e:
            raise e

        return ni

    def Hashes(self):
        """
        Returns an ordered list of the hashed license texts.
        """
        libs = sorted(self.lib_hash.keys())
        hashes = set()
        result = []
        for lib_name in libs:
            hl = []
            for h in self.lib_hash[lib_name]:
                if h in hashes:
                    continue
                hashes.add(h)
                hl.append(h)
            if hl:
                hl.sort(key=lambda x: (len(self.text[x]), x.key))
                result.extend(hl)
        return result

    def InputFiles(self):
        """
        Returns the complete list of files read during indexing.
        """
        project_meta = self.pmix.AllMetadataFiles()
        files = self.files.copy()
        files.extend(self.lg.TargetNames())
        files.extend(project_meta)
        return files

    def HashLibs(self, h: Hash):
        """
        Returns the ordered list of library names using the license text hashed as `h`.
        """
        libs = list(self.hash_lib_install[h].keys())
        libs.sort()
        return libs

    def HashLibInstalls(self, h: Hash, lib_name: str):
        """
        Returns the ordered list of install paths referencing library `lib_name`
        using the license text hashed as `h`.
        """
        installs = list(self.hash_lib_install[h][lib_name])
        installs.sort()
        return installs

    def InstallPaths(self):
        """
        Returns an ordered list of indexed install paths.
        """
        paths = sorted(self.install_hash_lib.keys())
        return paths

    def InstallHashes(self, install_path: str):
        """
        Returns the ordered list of hashes attached to `install_path`.
        """
        hashes = list(self.install_hash_lib[install_path].keys())
        hashes.sort(key=lambda h: (len(self.text[h]), h.key))
        return hashes

    def InstallHashLibs(self, install_path: str, h: Hash):
        """
        Returns the ordered list of library names attached to `install_path` as hash `h`.
        """
        libs = list(self.install_hash_lib[install_path][h])
        libs.sort()
        return libs

    def Libraries(self):
        """
        Returns an ordered list of indexed library names.
        """
        libs = sorted(self.lib_hash.keys())
        return libs

    def HashText(self, h: Hash):
        """
        Returns the file content of the license text hashed as `h`.
        """
        return self.text.get(h, b'')

    def getLibName(self, notice_for: TargetNode, h: Hash) -> str:
        """
        Returns the name of the library associated with `notice_for`.
        """
        # Attempt to find the library name from the license texts
        for text in notice_for.LicenseTexts():
            if ':' not in text:
                if self.hash.get(text) != h:
                    continue
                ln = self.checkMetadataForLicenseText(notice_for, text)
                if ln:
                    return ln
                continue
            fname, pname = text.split(':', 1)
            if self.hash.get(fname) != h:
                continue
            try:
                ln = url_parse_unquote(pname)
                return ln
            except:
                continue

        # Use name from METADATA if available
        ln = self.checkMetadata(notice_for)
        if ln:
            return ln

        # Use package_name from license module if available
        pn = notice_for.PackageName()
        if pn:
            return pn

        # Use module name as fallback
        return notice_for.ModuleName()

    def checkMetadata(self, notice_for: TargetNode) -> str:
        """
        Tries to look up a library name from a METADATA file associated with `notice_for`.
        """
        pms = self.pmix.MetadataForProjects(*notice_for.Projects())
        for pm in pms:
            name = pm.VersionedName()
            if name:
                return name
        return ""

    def checkMetadataForLicenseText(self, notice_for: TargetNode, license_text: str) -> str:
        """
        Tries to find a library name associated with the license text from METADATA.
        """
        p = ""
        for proj in notice_for.Projects():
            if license_text.startswith(proj):
                p = proj
                break
        if not p:
            p = os.path.dirname(license_text)
            while True:
                if os.path.exists(os.path.join(p, '.git')):
                    break
                if '/' in p and p != '/':
                    p = os.path.dirname(p)
                    continue
                return ""
        pms = self.pmix.MetadataForProjects(p)
        if pms:
            return pms[0].VersionedName()
        return ""

    def addText(self, file: str):
        """
        Reads and indexes the content of a license text file.
        """
        try:
            # Assuming root_fs is a dictionary-like object for simplicity
            if file in self.root_fs:
                text = self.root_fs[file]
                if isinstance(text, str):
                    text = text.encode('utf-8')
            else:
                raise FileNotFoundError(f"File {file} not found in root_fs")
            hash_value = Hash(hashlib.md5(text).hexdigest())
            self.hash[file] = hash_value
            if hash_value not in self.text:
                self.text[hash_value] = text
            self.files.append(file)
        except Exception as e:
            print(f"Error opening license text file {file}: {e}")
            raise e

# Helper functions

def getInstallPaths(attaches_to: TargetNode, path: TargetEdgePath) -> List[str]:
    """
    Returns the names of the used dependencies mapped to their installed locations.
    For simplicity, returns the installed files of the target node.
    """
    installs = attaches_to.Installed()
    if not installs:
        installs = attaches_to.Built()
    return installs

def url_parse_unquote(s: str) -> str:
    """
    Unquotes URL-encoded strings.
    """
    from urllib.parse import unquote
    return unquote(s)

# Note: Since the actual implementations of some classes and functions are missing,
# the placeholders above provide minimal functionality to allow the code to run.
# You may need to adjust or implement these according to your actual codebase.

