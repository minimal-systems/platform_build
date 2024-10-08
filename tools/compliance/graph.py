# graph.py

# Import necessary modules
import threading

class LicenseGraph:
    """
    LicenseGraph describes the immutable license metadata for a set of root
    targets and the transitive closure of their dependencies.

    It provides the frame of reference for all of the other types defined here.
    """
    def __init__(self, root_files=None):
        self.root_files = root_files or []  # Root files list (immutable)
        self.edges = []  # List of directed edges in the graph (target -> dependency)
        self.targets = {}  # Maps each target name to its corresponding TargetNode
        self.once_bottom_up = threading.Lock()  # Ensures bottom-up resolve only happens once
        self.once_top_down = threading.Lock()  # Ensures top-down resolve only happens once
        self.shipped_nodes = None  # Caches shipped nodes result
        self.mu = threading.Lock()  # Lock for guarding concurrent updates
        self.shipped = set()  # Initialize shipped attribute as an empty set

    def edges(self):
        """Returns the list of edges in the graph (unordered)."""
        return self.edges[:]

    def targets(self):
        """Returns the list of target nodes in the graph (unordered)."""
        return list(self.targets.values())

    def target_names(self):
        """Returns the list of target node names in the graph (unordered)."""
        return list(self.targets.keys())

    def add_target(self, target):
        """Adds a new target node to the graph."""
        if isinstance(target, TargetNode):
            self.targets[target.name] = target

    def add_edge(self, edge):
        """Adds a new edge to the graph."""
        if isinstance(edge, TargetEdge):
            self.edges.append(edge)

    def get_target(self, target_name):
        """Returns the TargetNode associated with the given target name."""
        return self.targets.get(target_name)

    def set_shipped_nodes(self, shipped_nodes):
        """Sets the shipped nodes for the graph."""
        self.shipped = shipped_nodes

    def __str__(self):
        """Provides a human-readable representation of the graph."""
        return f"LicenseGraph({len(self.targets)} targets, {len(self.edges)} edges)"


class TargetEdge:
    """
    TargetEdge describes a directed, annotated edge from a target to a dependency.

    A LicenseGraph is a set of such TargetEdges.
    """
    def __init__(self, target, dependency, annotations=None):
        self.target = target
        self.dependency = dependency
        self.annotations = annotations or TargetEdgeAnnotations()

    def is_runtime_dependency(self):
        """Returns True if the edge represents a runtime dependency (shared libraries)."""
        return self.annotations.has_annotation("dynamic")

    def is_derivation(self):
        """Returns True if the edge represents a derivation relationship."""
        return self.annotations.has_annotation("derivation")

    def is_build_tool(self):
        """Returns True if the edge represents a build tool dependency."""
        return not self.is_derivation() and not self.is_runtime_dependency()

    def __str__(self):
        """Returns a string representation of the edge."""
        return f"{self.target.name} -[{self.annotations}]> {self.dependency.name}"


class TargetEdgeAnnotations:
    """
    TargetEdgeAnnotations describes a set of annotations attached to an edge from a target to a dependency.

    These annotations distinguish between static linkage, dynamic linkage, and tools used at build time.
    """
    def __init__(self):
        self.annotations = {}

    def has_annotation(self, ann):
        """Returns True if the given annotation exists in the set."""
        return ann in self.annotations

    def add_annotation(self, ann):
        """Adds a new annotation to the set."""
        self.annotations[ann] = True

    def as_list(self):
        """Returns the list of annotation names attached to the edge."""
        return list(self.annotations.keys())

    def compare(self, other):
        """Compares two TargetEdgeAnnotations sets."""
        a1 = sorted(self.as_list())
        a2 = sorted(other.as_list())
        if a1 < a2:
            return -1
        elif a1 > a2:
            return 1
        else:
            return 0

    def __str__(self):
        """Returns a string representation of the annotations."""
        return ", ".join(self.as_list())


class TargetNode:
    """
    TargetNode describes a module or target identified by the name of a specific metadata file.

    Each metadata file corresponds to a Soong module or to a Make target.
    """
    def __init__(self, name, proto=None):
        self.name = name
        self.proto = proto or {}
        self.edges = []  # Edges connecting to dependencies

    def dependencies(self):
        """Returns the list of edges to dependencies of the target node."""
        return self.edges[:]

    def license_conditions(self):
        """Returns a copy of the set of license conditions originating at the target."""
        return self.proto.get("license_conditions", set())

    def license_texts(self):
        """Returns the paths to the files containing the license texts for the target."""
        return self.proto.get("license_texts", [])

    def is_container(self):
        """Returns True if the target represents a container that aggregates other targets."""
        return self.proto.get("is_container", False)

    def built(self):
        """Returns the list of files built by the module or target."""
        return self.proto.get("built", [])

    def installed(self):
        """Returns the list of files installed by the module or target."""
        return self.proto.get("installed", [])

    def target_files(self):
        """Returns the list of files built or installed by the module or target."""
        return self.built() + self.installed()

    def install_map(self):
        """Returns the list of path transformations to move files to their destination inside a container."""
        return self.proto.get("install_map", [])

    def sources(self):
        """Returns the list of file names depended on by the target."""
        return self.proto.get("sources", [])

    def __str__(self):
        """Returns a string representation of the target node."""
        return f"TargetNode({self.name})"


class TargetEdgePathSegment:
    """
    TargetEdgePathSegment describes a single arc in a TargetPath associating the edge with a context.
    """
    def __init__(self, edge, ctx=None):
        self.edge = edge
        self.ctx = ctx

    def target(self):
        """Returns the target of the edge."""
        return self.edge.target

    def dependency(self):
        """Returns the dependency of the edge."""
        return self.edge.dependency

    def __str__(self):
        """Returns a string representation of the path segment."""
        return f"{self.edge}"


class TargetEdgePath:
    """
    TargetEdgePath describes a sequence of edges starting at a root and ending at some final dependency.
    """
    def __init__(self, capacity=0):
        self.path = []

    def push(self, edge, ctx=None):
        """Appends a new edge to the list, verifying that the target of the new edge matches the prior dependency."""
        if len(self.path) == 0 or self.path[-1].edge.dependency == edge.target:
            self.path.append(TargetEdgePathSegment(edge, ctx))
        else:
            raise ValueError(f"Disjoint path: {edge.target.name} does not match {self.path[-1].edge.dependency.name}")

    def pop(self):
        """Shortens the path by one edge."""
        if len(self.path) > 0:
            self.path.pop()
        else:
            raise ValueError("Attempt to remove edge from an empty path")

    def clear(self):
        """Clears the path."""
        self.path = []

    def copy(self):
        """Returns a copy of the path."""
        copied_path = TargetEdgePath()
        copied_path.path = self.path[:]
        return copied_path

    def __str__(self):
        """Returns a string representation of the path."""
        if len(self.path) == 0:
            return "[]"
        segments = " -> ".join(str(segment) for segment in self.path)
        return f"[{segments}]"

