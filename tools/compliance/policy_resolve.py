# policy_resolve.py

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

from conditionset import LicenseConditionSet
from graph import LicenseGraph, TargetNode


# TraceConditions is a function that returns the conditions to trace for each target node `tn`.
def trace_conditions(tn):
    """Returns the license conditions to trace for a given target node."""
    return tn.license_conditions


# AllResolutions resolves all unfiltered license conditions for a given target node.
ALL_RESOLUTIONS = trace_conditions


def resolve_bottom_up_conditions(lg):
    """
    Performs a bottom-up walk of the LicenseGraph, propagating conditions up the graph as necessary.

    Propagates conditions according to the properties of each edge and according to each license
    condition in question.
    """
    trace_bottom_up_conditions(lg, ALL_RESOLUTIONS)


def trace_bottom_up_conditions(lg, conditions_fn):
    """
    Performs a bottom-up walk of the LicenseGraph, propagating trace conditions from `conditions_fn`
    up the graph as necessary according to the properties of each edge and the license condition in question.
    """
    # Placeholder logic to simulate bottom-up graph traversal
    for target in lg.all_targets():
        conditions = conditions_fn(target)
        print(f"Tracing conditions for target: {target}")
        for dependency in lg.get_dependencies(target):
            print(f"Propagating conditions from {dependency} to {target}")


class TargetNode:
    """A dummy TargetNode class with a set of license conditions."""

    def __init__(self, name, license_conditions=None):
        self.name = name
        self.license_conditions = license_conditions or LicenseConditionSet()

    def __repr__(self):
        return f"TargetNode({self.name})"


# Example usage
if __name__ == "__main__":
    # Create a dummy LicenseGraph and add targets and dependencies
    lg = LicenseGraph()
    node1 = TargetNode("file1", LicenseConditionSet("PermissiveCondition"))
    node2 = TargetNode("file2", LicenseConditionSet("RestrictedCondition"))
    node3 = TargetNode("file3", LicenseConditionSet("NoticeCondition"))

    # Add targets to the graph
    lg.add_target(node1)
    lg.add_target(node2)
    lg.add_target(node3)

    # Define dependencies
    lg.add_dependency(node1, node2)
    lg.add_dependency(node2, node3)

    # Resolve conditions bottom-up
    resolve_bottom_up_conditions(lg)
