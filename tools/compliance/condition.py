# condition.py

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

class LicenseCondition:
    """Represents various license conditions as constants."""
    UNENCUMBERED = 0x0001
    PERMISSIVE = 0x0002
    NOTICE = 0x0004
    RECIPROCAL = 0x0008
    RESTRICTED = 0x0010
    WEAKLY_RESTRICTED = 0x0020
    PROPRIETARY = 0x0040
    BY_EXCEPTION_ONLY = 0x0080
    CONDITIONAL = 0x0100

    LICENSE_CONDITION_MASK = 0x1FF

    # Set of all valid conditions
    VALID_CONDITIONS = {
        UNENCUMBERED,
        PERMISSIVE,
        NOTICE,
        RECIPROCAL,
        RESTRICTED,
        WEAKLY_RESTRICTED,
        PROPRIETARY,
        BY_EXCEPTION_ONLY,
        CONDITIONAL,
    }

    def __init__(self, value=None):
        """Initialize the LicenseCondition with a value, if provided."""
        if value is not None:
            if self.validate_condition(value):
                self.value = value
            else:
                raise ValueError(f"Invalid LicenseCondition value: {value}")
        else:
            self.value = None

    @classmethod
    def describe(cls, condition):
        """Returns a description for the given license condition."""
        if not cls.validate_condition(condition):
            raise KeyError(f"Unrecognized license condition: {condition}")
        descriptions = {
            cls.UNENCUMBERED: "Unencumbered: Public domain or public domain-like license that disclaims copyright.",
            cls.PERMISSIVE: "Permissive: License without notice or other significant requirements.",
            cls.NOTICE: "Notice: Open-source license with only notice or attribution requirements.",
            cls.RECIPROCAL: "Reciprocal: License with requirement to share the module's source only.",
            cls.RESTRICTED: "Restricted: License with requirement to share all source code linked to the module's source.",
            cls.WEAKLY_RESTRICTED: "Weakly Restricted: RestrictedCondition waived for dynamic linking.",
            cls.PROPRIETARY: "Proprietary: License with source privacy requirements.",
            cls.BY_EXCEPTION_ONLY: "By Exception Only: License that applies under specific exceptions.",
            cls.CONDITIONAL: "Conditional: License with conditions that must be met for usage."
        }
        return descriptions[condition]

    @classmethod
    def validate_condition(cls, condition):
        """Validates if the given condition is a recognized LicenseCondition."""
        return condition in cls.VALID_CONDITIONS


# Example usage:
if __name__ == '__main__':
    condition = LicenseCondition.NOTICE
    print(f"Condition: {condition}, Description: {LicenseCondition.describe(condition)}")
