# policy_shareprivacyconflicts.py

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

from policy_resolve import resolve_top_down_conditions, walk_resolutions_for_condition
from conditionset import LicenseConditionSet

# Placeholder for conditions that imply shared or private conditions
IMPLIES_SHARED = LicenseConditionSet("SharedCondition")
IMPLIES_PRIVATE = LicenseConditionSet("PrivateCondition")


class SourceSharePrivacyConflict:
    """
    Represents a conflict between a source-sharing condition and a source-privacy condition.

    Attributes:
        source_node (TargetNode): The source node where the conflict is observed.
        share_condition (LicenseCondition): The condition that requires sharing.
        privacy_condition (LicenseCondition): The condition that requires privacy.
    """
    def __init__(self, source_node, share_condition, privacy_condition):
        self.source_node = source_node
        self.share_condition = share_condition
        self.privacy_condition = privacy_condition

    def __str__(self):
        """Returns a string describing the conflict."""
        return f"{self.source_node.name} {self.privacy_condition} and must share from {self.share_condition} condition."

    def is_equal_to(self, other):
        """Returns true if `self` and `other` describe the same conflict."""
        return (self.source_node.name == other.source_node.name and
                self.share_condition == other.share_condition and
                self.privacy_condition == other.privacy_condition)


def conflicting_shared_private_source(lg):
    """
    Lists all of the targets where conflicting conditions to share the source and to keep the source private apply.

    Args:
        lg (LicenseGraph): The LicenseGraph to analyze.

    Returns:
        List[SourceSharePrivacyConflict]: List of conflicts found in the license graph.
    """
    # Resolve top-down conditions in the graph
    resolve_top_down_conditions(lg)

    # Placeholder for combined conditions - this would be specific logic based on policy
    combined = walk_resolutions_for_condition(lg, IMPLIES_SHARED.union(IMPLIES_PRIVATE))

    # Placeholder: Collect conflicts (implement actual logic here)
    conflicts = []
    for target in lg.all_targets():
        if "SharedCondition" in lg.targets[target]["conditions"] and "PrivateCondition" in lg.targets[target]["conditions"]:
            conflict = SourceSharePrivacyConflict(target, "SharedCondition", "PrivateCondition")
            conflicts.append(conflict)

    return conflicts


# Dummy class implementations for LicenseGraph and TargetNode
class LicenseGraph:
    """A dummy LicenseGraph class for demonstration purposes."""
    def __init__(self):
        self.targets = {}

    def add_target(self, target, conditions=None):
        if conditions is None:
            conditions = LicenseConditionSet()
        self.targets[target] = {"conditions": conditions, "dependencies": set()}

    def add_dependency(self, target, dependency):
        if target in self.targets and dependency in self.targets:
            self.targets[target]["dependencies"].add(dependency)

    def all_targets(self):
        return self.targets.keys()

    def get_dependencies(self, target):
        return self.targets[target]["dependencies"]

    def __str__(self):
        """String representation for debugging purposes."""
        return "\n".join(f"{target}: {self.targets[target]}" for target in self.targets)


class TargetNode:
    """A dummy TargetNode class with a name attribute."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"TargetNode({self.name})"


# Example usage
if __name__ == "__main__":
    # Create a dummy LicenseGraph and add targets with conflicting conditions
    lg = LicenseGraph()
    node1 = TargetNode("file1")
    node2 = TargetNode("file2")
    node3 = TargetNode("file3")

    # Add targets to the graph with conditions
    lg.add_target(node1, LicenseConditionSet("SharedCondition"))
    lg.add_target(node2, LicenseConditionSet("PrivateCondition"))
    lg.add_target(node3, LicenseConditionSet("SharedCondition", "PrivateCondition"))

    # Define dependencies
    lg.add_dependency(node1, node2)
    lg.add_dependency(node2, node3)

    # Get conflicting shared-private sources
    conflicts = conflicting_shared_private_source(lg)
    for conflict in conflicts:
        print(conflict)
