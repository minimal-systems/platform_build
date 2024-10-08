# conditionset.py

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

from condition import LicenseCondition


class LicenseConditionSet:
    """Represents a set of license conditions."""

    ALL_LICENSE_CONDITIONS = LicenseCondition.LICENSE_CONDITION_MASK

    def __init__(self, *conditions):
        self.conditions = 0
        for condition in conditions:
            self.add(condition)

    def add(self, condition):
        """Adds a license condition to the set."""
        self.conditions |= condition

    def plus(self, *conditions):
        """Returns a new set containing all of the elements of this set and all of the given conditions."""
        result = LicenseConditionSet()
        result.conditions = self.conditions
        for condition in conditions:
            result.add(condition)
        return result

    def minus(self, *conditions):
        """Returns a new set containing all of the elements of this set without the given conditions."""
        result = LicenseConditionSet()
        result.conditions = self.conditions
        for condition in conditions:
            result.conditions &= ~condition
        return result

    def union(self, *other_sets):
        """Returns a new set containing all elements of this set and all elements of other sets."""
        result = LicenseConditionSet()
        result.conditions = self.conditions
        for other in other_sets:
            result.conditions |= other.conditions
        return result

    def matching_any(self, *conditions):
        """Returns the subset of the set equal to any of the given conditions."""
        result = LicenseConditionSet()
        for condition in conditions:
            if self.conditions & condition:
                result.add(condition)
        return result

    def contains(self, condition):
        """Checks if the set contains a specific condition."""
        return self.conditions & condition == condition

    def __eq__(self, other):
        """Check equality based on the internal conditions value."""
        if isinstance(other, LicenseConditionSet):
            return self.conditions == other.conditions
        return False

    def __hash__(self):
        """Generate a hash based on the internal conditions value."""
        return hash(self.conditions)

    def __str__(self):
        """Returns a human-readable representation of the set."""
        elements = []
        for condition in vars(LicenseCondition).values():
            if isinstance(condition, int) and self.contains(condition):
                elements.append(LicenseCondition.describe(condition))
        return f"LicenseConditionSet({', '.join(elements)})"
