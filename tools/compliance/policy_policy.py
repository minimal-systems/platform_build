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
from conditionset import LicenseConditionSet
from condition import LicenseCondition  # Import LicenseCondition for condition constants

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

# Safe Prebuilt Prefixes - This would typically include regex matching for safe paths.
SAFE_PREBUILT_PREFIXES = [
    {"pattern": re.compile(r"external/"), "strip": True},
    {"pattern": re.compile(r"prebuilts/"), "strip": False},
]

# Conditions that imply Unencumbered.
IMPLIES_UNENCUMBERED = {LicenseCondition.UNENCUMBERED}

# Conditions that imply Permissive.
IMPLIES_PERMISSIVE = {LicenseCondition.PERMISSIVE}


# Example Usage
if __name__ == "__main__":
    print("Recognized Annotations:", RECOGNIZED_ANNOTATIONS)
    print("Safe Path Prefixes:", SAFE_PATH_PREFIXES)
    print("Safe Prebuilt Prefixes:", [prefix["pattern"].pattern for prefix in SAFE_PREBUILT_PREFIXES])
    print("Conditions that imply Unencumbered:", IMPLIES_UNENCUMBERED)
    print("Conditions that imply Permissive:", IMPLIES_PERMISSIVE)

    # Demonstrate usage of LicenseConditionSet with correct LicenseCondition constants
    condition_set = LicenseConditionSet()
    condition_set.add(LicenseCondition.UNENCUMBERED)  # Use LicenseCondition.UNENCUMBERED (integer constant)
    condition_set.add(LicenseCondition.PERMISSIVE)    # Use LicenseCondition.PERMISSIVE (integer constant)
    print(f"LicenseConditionSet: {condition_set}")
