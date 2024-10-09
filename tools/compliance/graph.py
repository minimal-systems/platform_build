# graph.py

import threading
import functools
from condition import LicenseCondition, RecognizedConditionNames
from conditionset import LicenseConditionSet, AllLicenseConditions

# Alias for synchronization (sync.Once equivalent in Python)
def run_once(func):
    """Decorator to run a function only once."""
    lock = threading.Lock()
    has_run = False

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal has_run
        with lock:
            if not has_run:
                result = func(*args, **kwargs)
                has_run = True
                return result
    return wrapper

class LicenseGraph:
    """
    LicenseGraph describes the immutable license metadata for a set of root
    targets and the transitive closure of their dependencies.

    Alternatively, a graph is a set of edges. In this case directed, annotated
    edges from targets to dependencies.

    A LicenseGraph provides the frame of reference for all of the other types
    defined here. It is possible to have multiple graphs, and to have targets,
    edges, and resolutions from multiple graphs. But it is an error to try to
    mix items from different graphs in the same operation.
    May raise an exception if attempted.

    The compliance package assumes specific private implementations of each of
    these interfaces. May raise an exception if attempts are made to combine different
    implementations of some interfaces with expected implementations of other
    interfaces here.
    """

    def __init__(self, root_files=None):
        # root_files identifies the original set of files to read. (immutable)
        # Defines the starting "top" for top-down walks.
        # Alternatively, an instance of LicenseGraph conceptually defines a scope within
        # the universe of build graphs as a sub-graph rooted at root_files where all edges
        # and targets for the instance are defined relative to and within that scope. For
        # most analyses, the correct scope is to root the graph at all of the distributed
        # artifacts.
        self.root_files = root_files if root_files is not None else []

        # edges lists the directed edges in the graph from target to dependency.
        # (protected by threading.Lock())
        # Alternatively, the graph is the set of `edges`.
        self.edges = []

        # targets identifies, indexes, and describes the entire set of target node files.
        # (protected by threading.Lock())
        self.targets = {}

        # once_bottom_up makes sure the bottom-up resolve walk only happens one time.
        self.once_bottom_up_lock = threading.Lock()
        self.once_bottom_up_run = False

        # once_top_down makes sure the top-down resolve walk only happens one time.
        self.once_top_down_lock = threading.Lock()
        self.once_top_down_run = False

        # shipped_nodes caches the results of a full walk of nodes identifying targets
        # distributed either directly or as derivative works.
        # (creation protected by threading.Lock())
        self.shipped_nodes = None

        # lock guards against concurrent update.
        self.lock = threading.Lock()

    # Edges returns the list of edges in the graph. (unordered)
    def Edges(self):
        with self.lock:
            return list(self.edges)

    # Targets returns the list of target nodes in the graph. (unordered)
    def Targets(self):
        with self.lock:
            return list(self.targets.values())

    # TargetNames returns the list of target node names in the graph. (unordered)
    def TargetNames(self):
        with self.lock:
            return list(self.targets.keys())

    # compliance-only LicenseGraph methods

    # newLicenseGraph constructs a new, empty instance of LicenseGraph.
    @staticmethod
    def newLicenseGraph():
        return LicenseGraph()

class TargetEdge:
    """
    TargetEdge describes a directed, annotated edge from a target to a
    dependency. (immutable)

    A LicenseGraph, above, is a set of TargetEdges.

    i.e. `Target` depends on `Dependency` in the manner described by
    `Annotations`.
    """

    def __init__(self, target, dependency, annotations=None):
        self.target = target
        self.dependency = dependency
        self.annotations = annotations if annotations is not None else TargetEdgeAnnotations()

    # Target identifies the target that depends on the dependency.
    #
    # Target needs Dependency to build.
    def Target(self):
        return self.target

    # Dependency identifies the target depended on by the target.
    #
    # Dependency builds without Target, but Target needs Dependency to build.
    def Dependency(self):
        return self.dependency

    # Annotations describes the type of edge by the set of annotations attached to
    # it.
    #
    # Only annotations prescribed by policy have any meaning for licensing, and
    # the meaning for licensing is likewise prescribed by policy. Other annotations
    # are preserved and ignored by policy.
    def Annotations(self):
        return self.annotations

    # IsRuntimeDependency returns true for edges representing shared libraries
    # linked dynamically at runtime.
    def IsRuntimeDependency(self):
        return edgeIsDynamicLink(self)

    # IsDerivation returns true for edges where the target is a derivative
    # work of dependency.
    def IsDerivation(self):
        return edgeIsDerivation(self)

    # IsBuildTool returns true for edges where the target is built
    # by dependency.
    def IsBuildTool(self):
        return not edgeIsDerivation(self) and not edgeIsDynamicLink(self)

    # String returns a human-readable string representation of the edge.
    def __str__(self):
        return f"{self.target.name} -[{', '.join(self.annotations.AsList())}]> {self.dependency.name}"

class TargetEdgeList(list):
    """
    TargetEdgeList orders lists of edges by target then dependency then annotations.
    """

    # Len returns the count of the elements in the list.
    def Len(self):
        return len(self)

    # Swap rearranges 2 elements so that each occupies the other's former position.
    def Swap(self, i, j):
        self[i], self[j] = self[j], self[i]

    # Less returns true when the `i`th element is lexicographically less than the `j`th.
    def Less(self, i, j):
        name_i = self[i].target.name
        name_j = self[j].target.name
        if name_i == name_j:
            name_i = self[i].dependency.name
            name_j = self[j].dependency.name
        if name_i == name_j:
            return self[i].annotations.Compare(self[j].annotations) < 0
        return name_i < name_j

    # Sort the list
    def Sort(self):
        self.sort(key=lambda edge: (edge.target.name, edge.dependency.name, edge.annotations))

class TargetEdgePathSegment:
    """
    TargetEdgePathSegment describes a single arc in a TargetEdgePath associating the
    edge with a context `ctx` defined by whatever process is creating the path.
    """

    def __init__(self, edge, ctx=None):
        self.edge = edge
        self.ctx = ctx

    # Target identifies the target that depends on the dependency.
    #
    # Target needs Dependency to build.
    def Target(self):
        return self.edge.target

    # Dependency identifies the target depended on by the target.
    #
    # Dependency builds without Target, but Target needs Dependency to build.
    def Dependency(self):
        return self.edge.dependency

    # Edge describes the target edge.
    def Edge(self):
        return self.edge

    # Annotations describes the type of edge by the set of annotations attached to
    # it.
    #
    # Only annotations prescribed by policy have any meaning for licensing, and
    # the meaning for licensing is likewise prescribed by policy. Other annotations
    # are preserved and ignored by policy.
    def Annotations(self):
        return self.edge.annotations

    # Context returns the context associated with the path segment. The type and
    # value of the context defined by the process creating the path.
    def Context(self):
        return self.ctx

    # String returns a human-readable string representation of the edge.
    def __str__(self):
        return f"{self.edge.target.name} -[{', '.join(self.edge.annotations.AsList())}]> {self.edge.dependency.name}"

class TargetEdgePath:
    """
    TargetEdgePath describes a sequence of edges starting at a root and ending
    at some final dependency.
    """

    def __init__(self, capacity=0):
        self.path = []
        self.path.reserve(capacity)

    # NewTargetEdgePath creates a new, empty path with capacity `cap`.
    @staticmethod
    def NewTargetEdgePath(capacity=0):
        return TargetEdgePath(capacity)

    # Push appends a new edge to the list verifying that the target of the new
    # edge is the dependency of the prior.
    def Push(self, edge, ctx=None):
        if not self.path:
            self.path.append(TargetEdgePathSegment(edge, ctx))
            return
        if self.path[-1].edge.dependency != edge.target:
            raise ValueError(f"disjoint path {self} does not end at {edge.target.name}")
        self.path.append(TargetEdgePathSegment(edge, ctx))

    # Pop shortens the path by 1 edge.
    def Pop(self):
        if not self.path:
            raise ValueError("attempt to remove edge from empty path")
        self.path.pop()

    # Clear makes the path length 0.
    def Clear(self):
        self.path.clear()

    # Copy makes a new path with the same value.
    def Copy(self):
        new_path = TargetEdgePath()
        new_path.path = self.path.copy()
        return new_path

    # String returns a string representation of the path: [n1 -> n2 -> ... -> nn].
    def __str__(self):
        if not self.path:
            return "[]"
        nodes = [segment.edge.target.name for segment in self.path]
        nodes.append(self.path[-1].edge.dependency.name)
        return f"[{' -> '.join(nodes)}]"

class TargetNode:
    """
    TargetNode describes a module or target identified by the name of a specific
    metadata file. (immutable)

    Each metadata file corresponds to a Soong module or to a Make target.

    A target node can appear as the target or as the dependency in edges.
    Most target nodes appear as both target in one edge and as dependency in
    other edges.
    """

    def __init__(self, name, proto):
        self.name = name
        self.proto = proto  # Assuming proto is an object with required attributes
        self.edges = []
        self.licenseConditions = LicenseConditionSet(*[RecognizedConditionNames[cond] for cond in proto.get('LicenseConditions', [])])

    # Name returns the string that identifies the target node.
    # i.e. path to license metadata file
    def Name(self):
        return self.name

    # Dependencies returns the list of edges to dependencies of `tn`.
    def Dependencies(self):
        return list(self.edges)

    # PackageName returns the string that identifies the package for the target.
    def PackageName(self):
        return self.proto.get('PackageName', '')

    # ModuleName returns the module name of the target.
    def ModuleName(self):
        return self.proto.get('ModuleName', '')

    # Projects returns the projects defining the target node. (unordered)
    #
    # In an ideal world, only 1 project defines a target, but the interaction
    # between Soong and Make for a variety of architectures and for host versus
    # product means a module is sometimes defined more than once.
    def Projects(self):
        return self.proto.get('Projects', [])

    # LicenseConditions returns a copy of the set of license conditions
    # originating at the target. The values that appear and how each is resolved
    # is a matter of policy. (unordered)
    #
    # e.g. notice or proprietary
    def LicenseConditions(self):
        return self.licenseConditions

    # LicenseTexts returns the paths to the files containing the license texts for
    # the target. (unordered)
    def LicenseTexts(self):
        return self.proto.get('LicenseTexts', [])

    # IsContainer returns true if the target represents a container that merely
    # aggregates other targets.
    def IsContainer(self):
        return self.proto.get('IsContainer', False)

    # Built returns the list of files built by the module or target. (unordered)
    def Built(self):
        return self.proto.get('Built', [])

    # Installed returns the list of files installed by the module or target.
    # (unordered)
    def Installed(self):
        return self.proto.get('Installed', [])

    # TargetFiles returns the list of files built or installed by the module or
    # target. (unordered)
    def TargetFiles(self):
        return self.Built() + self.Installed()

    # InstallMap returns the list of path name transformations to make to move
    # files from their original location in the file system to their destination
    # inside a container. (unordered)
    def InstallMap(self):
        return [InstallMap(im.get('FromPath'), im.get('ContainerPath')) for im in self.proto.get('InstallMap', [])]

    # Sources returns the list of file names depended on by the target, which may
    # be a proper subset of those made available by dependency modules.
    # (unordered)
    def Sources(self):
        return self.proto.get('Sources', [])

class InstallMap:
    """
    InstallMap describes the mapping from an input filesystem file to file in a
    container.
    """

    def __init__(self, from_path, container_path):
        self.FromPath = from_path
        self.ContainerPath = container_path

class TargetEdgeAnnotations:
    """
    TargetEdgeAnnotations describes an immutable set of annotations attached to
    an edge from a target to a dependency.

    Annotations typically distinguish between static linkage versus dynamic
    versus tools that are used at build time but are not linked in any way.
    """

    def __init__(self, annotations=None):
        self.annotations = set(annotations) if annotations else set()

    # newEdgeAnnotations creates a new instance of TargetEdgeAnnotations.
    @staticmethod
    def newEdgeAnnotations():
        return TargetEdgeAnnotations()

    # HasAnnotation returns true if an annotation `ann` is in the set.
    def HasAnnotation(self, ann):
        return ann in self.annotations

    # Compare orders TargetAnnotations returning:
    # -1 when self < other,
    # +1 when self > other, and
    # 0 when self == other.
    def Compare(self, other):
        a1 = sorted(self.AsList())
        a2 = sorted(other.AsList())
        for s1, s2 in zip(a1, a2):
            if s1 < s2:
                return -1
            if s1 > s2:
                return 1
        if len(a1) < len(a2):
            return -1
        if len(a1) > len(a2):
            return 1
        return 0

    # AsList returns the list of annotation names attached to the edge.
    # (unordered)
    def AsList(self):
        return list(self.annotations)

    # Support for sorting annotations
    def __lt__(self, other):
        return self.Compare(other) == -1

    def __eq__(self, other):
        return self.Compare(other) == 0

class TargetNodeSet:
    """
    TargetNodeSet describes a set of distinct nodes in a license graph.
    """

    def __init__(self):
        self.nodes = set()

    # Contains returns true when `target` is an element of the set.
    def Contains(self, target):
        return target in self.nodes

    # Add a target node to the set
    def Add(self, target):
        self.nodes.add(target)

    # Names returns the array of target node names in the set. (unordered)
    def Names(self):
        return [tn.name for tn in self.nodes]

    # String returns a human-readable string representation of the set.
    def __str__(self):
        return f"{{{', '.join(self.Names())}}}"

class TargetNodeList(list):
    """
    TargetNodeList orders a list of targets by name.
    """

    # Len returns the count of elements in the list.
    def Len(self):
        return len(self)

    # Swap rearranges 2 elements so that each occupies the other's former position.
    def Swap(self, i, j):
        self[i], self[j] = self[j], self[i]

    # Less returns true when the `i`th element is lexicographically less than the `j`th.
    def Less(self, i, j):
        return self[i].name < self[j].name

    # Sort the list
    def Sort(self):
        self.sort(key=lambda tn: tn.name)

    # String returns a string representation of the list.
    def __str__(self):
        names = [tn.name for tn in self]
        return f"[{' '.join(names)}]"

    # Names returns an array of the names of the nodes in the same order as the nodes in the list.
    def Names(self):
        return [tn.name for tn in self]

# Helper functions (not part of the class definitions)

def edgeIsDynamicLink(edge):
    # Placeholder function to determine if an edge represents a dynamic link
    # This needs to be implemented according to the specific annotations
    return edge.annotations.HasAnnotation('dynamic')

def edgeIsDerivation(edge):
    # Placeholder function to determine if an edge represents a derivation
    # This needs to be implemented according to the specific annotations
    return edge.annotations.HasAnnotation('static')

# You can add more helper functions or classes as needed to complete the conversion

