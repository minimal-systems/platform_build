# policy_shipped.py

# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from threading import Lock


class TargetNodeSet(set):
    """Represents a set of target nodes in the LicenseGraph."""
    pass


def shipped_nodes(lg):
    """
    Returns the set of nodes in a license graph where the target or a derivative work gets distributed.
    The result is cached for subsequent calls.

    Args:
        lg (LicenseGraph): The LicenseGraph to analyze.

    Returns:
        TargetNodeSet: A set of nodes that are shipped as part of the distribution.
    """
    # Use a lock to ensure thread safety while accessing the shipped nodes
    lg.lock.acquire()
    shipped = lg.shipped_nodes
    lg.lock.release()

    # Return cached shipped nodes if available
    if shipped is not None:
        return shipped

    # Create a new TargetNodeSet to store shipped nodes
    shipped_set = TargetNodeSet()

    # Perform a top-down walk of the graph to identify shipped nodes
    def walk_top_down(node, path=[]):
        """Recursively traverses the graph to find shipped nodes."""
        if node in shipped_set:
            return False
        if len(path) > 0 and not edge_is_derivation(path[-1]):
            return False
        shipped_set.add(node)
        for dep in lg.get_dependencies(node):
            walk_top_down(dep, path + [node])
        return True

    for root in lg.get_roots():
        walk_top_down(root)

    # Cache the result for future use
    lg.lock.acquire()
    if lg.shipped_nodes is None:
        lg.shipped_nodes = shipped_set
    else:
        # If another thread has already set the shipped nodes, use that instead
        shipped_set = lg.shipped_nodes
    lg.lock.release()

    return shipped_set


def edge_is_derivation(edge):
    """Determines whether a given edge represents a derivation relationship."""
    # Placeholder logic - replace with actual condition check
    return True


# Dummy class implementation for LicenseGraph and TargetNode
class LicenseGraph:
    """A dummy LicenseGraph class for demonstration purposes."""
    def __init__(self):
        self.targets = {}
        self.roots = set()
        self.shipped_nodes = None
        self.lock = Lock()

    def add_target(self, target):
        self.targets[target] = {"conditions": set(), "dependencies": set()}

    def add_dependency(self, target, dependency):
        if target in self.targets and dependency in self.targets:
            self.targets[target]["dependencies"].add(dependency)

    def get_roots(self):
        return self.roots

    def get_dependencies(self, target):
        return self.targets[target]["dependencies"]

    def add_root(self, target):
        self.roots.add(target)


class TargetNode:
    """A dummy TargetNode class with a name attribute."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"TargetNode({self.name})"


# Example usage
if __name__ == "__main__":
    lg = LicenseGraph()
    node1 = TargetNode("file1")
    node2 = TargetNode("file2")
    node3 = TargetNode("file3")

    # Add targets to the graph
    lg.add_target(node1)
    lg.add_target(node2)
    lg.add_target(node3)

    # Define dependencies
    lg.add_dependency(node1, node2)
    lg.add_dependency(node2, node3)

    # Add root nodes
    lg.add_root(node1)

    # Get shipped nodes
    shipped = shipped_nodes(lg)
    print("Shipped Nodes:", shipped)
