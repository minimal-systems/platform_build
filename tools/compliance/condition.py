# condition.py

import enum

class LicenseCondition(enum.IntFlag):
    """
    LicenseCondition identifies a recognized license condition by setting the
    corresponding bit.
    """
    # LicenseConditionMask is a bitmask for the recognized license conditions.
    LicenseConditionMask = 0x1FF

    # UnencumberedCondition identifies public domain or public domain-
    # like license that disclaims copyright.
    UnencumberedCondition = 0x0001
    # PermissiveCondition identifies a license without notice or other
    # significant requirements.
    PermissiveCondition = 0x0002
    # NoticeCondition identifies a typical open-source license with only
    # notice or attribution requirements.
    NoticeCondition = 0x0004
    # ReciprocalCondition identifies a license with requirement to share
    # the module's source only.
    ReciprocalCondition = 0x0008
    # RestrictedCondition identifies a license with requirement to share
    # all source code linked to the module's source.
    RestrictedCondition = 0x0010
    # WeaklyRestrictedCondition identifies a RestrictedCondition waived
    # for dynamic linking.
    WeaklyRestrictedCondition = 0x0020
    # ProprietaryCondition identifies a license with source privacy
    # requirements.
    ProprietaryCondition = 0x0040
    # ByExceptionOnlyCondition identifies a license where policy requires product
    # counsel review prior to use.
    ByExceptionOnlyCondition = 0x0080
    # NotAllowedCondition identifies a license with onerous conditions
    # where policy prohibits use.
    NotAllowedCondition = 0x0100

    def Name(self):
        """Returns the condition string corresponding to the LicenseCondition."""
        if self == LicenseCondition.UnencumberedCondition:
            return "unencumbered"
        elif self == LicenseCondition.PermissiveCondition:
            return "permissive"
        elif self == LicenseCondition.NoticeCondition:
            return "notice"
        elif self == LicenseCondition.ReciprocalCondition:
            return "reciprocal"
        elif self == LicenseCondition.RestrictedCondition:
            return "restricted"
        elif self == LicenseCondition.WeaklyRestrictedCondition:
            return "restricted_if_statically_linked"
        elif self == LicenseCondition.ProprietaryCondition:
            return "proprietary"
        elif self == LicenseCondition.ByExceptionOnlyCondition:
            return "by_exception_only"
        elif self == LicenseCondition.NotAllowedCondition:
            return "not_allowed"
        else:
            raise ValueError(f"Unrecognized license condition: {self}")

    def HasAny(self, other):
        """Checks if any bits in 'other' are set in self."""
        return bool(self & other)

# Expose the LicenseCondition enum members at the module level
UnencumberedCondition = LicenseCondition.UnencumberedCondition
PermissiveCondition = LicenseCondition.PermissiveCondition
NoticeCondition = LicenseCondition.NoticeCondition
ReciprocalCondition = LicenseCondition.ReciprocalCondition
RestrictedCondition = LicenseCondition.RestrictedCondition
WeaklyRestrictedCondition = LicenseCondition.WeaklyRestrictedCondition
ProprietaryCondition = LicenseCondition.ProprietaryCondition
ByExceptionOnlyCondition = LicenseCondition.ByExceptionOnlyCondition
NotAllowedCondition = LicenseCondition.NotAllowedCondition

# RecognizedConditionNames maps condition strings to LicenseCondition.
RecognizedConditionNames = {
    "unencumbered":                    UnencumberedCondition,
    "permissive":                      PermissiveCondition,
    "notice":                          NoticeCondition,
    "reciprocal":                      ReciprocalCondition,
    "restricted":                      RestrictedCondition,
    "restricted_if_statically_linked": WeaklyRestrictedCondition,
    "proprietary":                     ProprietaryCondition,
    "by_exception_only":               ByExceptionOnlyCondition,
    "not_allowed":                     NotAllowedCondition,
}

# Define ImpliesShared as a combination of conditions.
ImpliesShared = (
    ReciprocalCondition |
    RestrictedCondition |
    WeaklyRestrictedCondition
)
