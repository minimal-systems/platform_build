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
    """
    LicenseCondition identifies a recognized license condition by setting
    the corresponding bit value.
    """
    UNENCUMBERED = 0x0001
    PERMISSIVE = 0x0002
    NOTICE = 0x0004
    RECIPROCAL = 0x0008
    RESTRICTED = 0x0010
    WEAKLY_RESTRICTED = 0x0020
    PROPRIETARY = 0x0040
    BY_EXCEPTION_ONLY = 0x0080
    NOT_ALLOWED = 0x0100
    CONDITIONAL = 0x0200  # Make sure this constant is included.

    # LicenseConditionMask is a bitmask for the recognized license conditions.
    LICENSE_CONDITION_MASK = 0x1FF

    # Mapping of condition names to LicenseCondition values.
    RECOGNIZED_CONDITION_NAMES = {
        "unencumbered": UNENCUMBERED,
        "permissive": PERMISSIVE,
        "notice": NOTICE,
        "reciprocal": RECIPROCAL,
        "restricted": RESTRICTED,
        "restricted_if_statically_linked": WEAKLY_RESTRICTED,
        "proprietary": PROPRIETARY,
        "by_exception_only": BY_EXCEPTION_ONLY,
        "not_allowed": NOT_ALLOWED,
        "conditional": CONDITIONAL,  # Include the conditional condition here.
    }

    @classmethod
    def name(cls, condition):
        """
        Returns the condition string corresponding to the LicenseCondition.

        Args:
            condition (int): The LicenseCondition bit value.

        Returns:
            str: The name of the condition.
        """
        condition_map = {
            cls.UNENCUMBERED: "unencumbered",
            cls.PERMISSIVE: "permissive",
            cls.NOTICE: "notice",
            cls.RECIPROCAL: "reciprocal",
            cls.RESTRICTED: "restricted",
            cls.WEAKLY_RESTRICTED: "restricted_if_statically_linked",
            cls.PROPRIETARY: "proprietary",
            cls.BY_EXCEPTION_ONLY: "by_exception_only",
            cls.NOT_ALLOWED: "not_allowed",
            cls.CONDITIONAL: "conditional",  # Include the name for the conditional condition.
        }
        if condition in condition_map:
            return condition_map[condition]
        raise ValueError(f"Unrecognized license condition: {condition}")

    @classmethod
    def describe(cls, condition):
        """
        Returns a description of the LicenseCondition.

        Args:
            condition (int): The LicenseCondition bit value.

        Returns:
            str: The description of the condition.
        """
        descriptions = {
            cls.UNENCUMBERED: "Public domain or public domain-like license that disclaims copyright.",
            cls.PERMISSIVE: "License without notice or other significant requirements.",
            cls.NOTICE: "Typical open-source license with only notice or attribution requirements.",
            cls.RECIPROCAL: "License with requirement to share the module's source only.",
            cls.RESTRICTED: "License with requirement to share all source code linked to the module's source.",
            cls.WEAKLY_RESTRICTED: "Restricted license condition waived for dynamic linking.",
            cls.PROPRIETARY: "License with source privacy requirements.",
            cls.BY_EXCEPTION_ONLY: "License where policy requires product counsel review prior to use.",
            cls.NOT_ALLOWED: "License with onerous conditions where policy prohibits use.",
            cls.CONDITIONAL: "License with conditions that must be met for usage.",  # Add the description here.
        }
        if condition in descriptions:
            return descriptions[condition]
        raise ValueError(f"Unrecognized license condition: {condition}")
