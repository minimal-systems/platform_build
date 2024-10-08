# policy_policy.py

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

import re

# Recognized Annotations
RECOGNIZED_ANNOTATIONS = {
    "static": "static",
    "dynamic": "dynamic",
    "toolchain": "toolchain",
}

# Safe Path Prefixes
SAFE_PATH_PREFIXES = [
    {"prefix": "external/", "strip": True},
    {"prefix": "build/", "strip": False},
    {"prefix": "cts/", "strip": False},
    {"prefix": "developers/", "strip": False},
    {"prefix": "development/", "strip": False},
    {"prefix": "packages/", "strip": True},
    {"prefix": "prebuilts/", "strip": False},
    {"prefix": "system/", "strip": False},
    {"prefix": "test/", "strip": False},
    {"prefix": "toolchain/", "strip": False},
    {"prefix": "tools/", "strip": False},
]

# Safe Prebuilt Prefixes - This would typically include regex matching for safe paths
SAFE_PREBUILT_PREFIXES = [
    {"pattern": re.compile(r"external/"), "strip": True},
    {"pattern": re.compile(r"prebuilts/"), "strip": False},
]

# Conditions that imply Unencumbered
IMPLIES_UNENCUMBERED = {"UnencumberedCondition"}

# Conditions that imply Permissive
IMPLIES_PERMISSIVE = {"PermissiveCondition"}

# Define LicenseConditionSet class or use a set to manage these condition sets as required
class LicenseConditionSet:
    """Class to manage License Condition sets."""
    def __init__(self, *conditions):
        self.conditions = set(conditions)

    def add(self, condition):
        """Adds a new condition to the set."""
        self.conditions.add(condition)

    def __contains__(self, condition):
        """Checks if the condition is present in the set."""
        return condition in self.conditions

    def __str__(self):
        """String representation of the condition set."""
        return f"LicenseConditionSet({', '.join(self.conditions)})"

# Example Usage
if __name__ == "__main__":
    print("Recognized Annotations:", RECOGNIZED_ANNOTATIONS)
    print("Safe Path Prefixes:", SAFE_PATH_PREFIXES)
    print("Safe Prebuilt Prefixes:", [prefix["pattern"].pattern for prefix in SAFE_PREBUILT_PREFIXES])
    print("Conditions that imply Unencumbered:", IMPLIES_UNENCUMBERED)
    print("Conditions that imply Permissive:", IMPLIES_PERMISSIVE)
