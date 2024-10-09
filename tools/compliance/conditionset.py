# conditionset.py

from condition import LicenseCondition, RecognizedConditionNames
import itertools

class LicenseConditionSet:
    """Identifies sets of license conditions."""

    def __init__(self, *conditions):
        self.value = 0
        for condition in conditions:
            self.value |= condition.value if isinstance(condition, LicenseCondition) else condition

        # Ensure only valid bits are set
        self.value &= LicenseCondition.LicenseConditionMask

    @staticmethod
    def NewLicenseConditionSet(*conditions):
        """Returns a set containing exactly the elements of `conditions`."""
        return LicenseConditionSet(*conditions)

    def Plus(self, *conditions):
        """Returns a new set containing all of the elements of `self` and `conditions`."""
        new_value = self.value
        for condition in conditions:
            new_value |= condition.value if isinstance(condition, LicenseCondition) else condition
        return LicenseConditionSet(new_value)

    def Union(self, *others):
        """Returns a new set containing all of the elements of `self` and all of the elements of the `other` sets."""
        new_value = self.value
        for other in others:
            new_value |= other.value
        return LicenseConditionSet(new_value)

    def MatchingAny(self, *conditions):
        """Returns the subset of `self` equal to any of the `conditions`."""
        result_value = 0
        for condition in conditions:
            result_value |= self.value & condition.value
        return LicenseConditionSet(result_value)

    def MatchingAnySet(self, *others):
        """Returns the subset of `self` that are members of any of the `other` sets."""
        result_value = 0
        for other in others:
            result_value |= self.value & other.value
        return LicenseConditionSet(result_value)

    def HasAny(self, *conditions):
        """Returns True when `self` contains at least one of the `conditions`."""
        for condition in conditions:
            if self.value & condition.value:
                return True
        return False

    def MatchesAnySet(self, *others):
        """Returns True when `self` has a non-empty intersection with at least one of the `other` condition sets."""
        for other in others:
            if self.value & other.value:
                return True
        return False

    def HasAll(self, *conditions):
        """Returns True when `self` contains every one of the `conditions`."""
        for condition in conditions:
            if not (self.value & condition.value):
                return False
        return True

    def MatchesEverySet(self, *others):
        """Returns True when `self` has a non-empty intersection with each of the `other` condition sets."""
        for other in others:
            if not (self.value & other.value):
                return False
        return True

    def Intersection(self, *others):
        """Returns the subset of `self` that are members of every `other` set."""
        result_value = self.value
        for other in others:
            result_value &= other.value
        return LicenseConditionSet(result_value)

    def Minus(self, *conditions):
        """Returns the subset of `self` that are not equal to any `conditions`."""
        result_value = self.value
        for condition in conditions:
            result_value &= ~condition.value
        return LicenseConditionSet(result_value)

    def Difference(self, *others):
        """Returns the subset of `self` that are not members of any `other` set."""
        result_value = self.value
        for other in others:
            result_value &= ~other.value
        return LicenseConditionSet(result_value)

    def Len(self):
        """Returns the number of license conditions in the set."""
        return bin(self.value).count('1')

    def AsList(self):
        """Returns a list of the license conditions in the set."""
        return [condition for condition in LicenseCondition if self.value & condition.value]

    def Names(self):
        """Returns a list of the names of the license conditions in the set."""
        return [condition.Name() for condition in self.AsList()]

    def IsEmpty(self):
        """Returns True when the set contains no license conditions."""
        return self.value == 0

    def __str__(self):
        """Returns a human-readable string representation of the set."""
        return f"{{{'|'.join(self.Names())}}}"

    def __repr__(self):
        return f"LicenseConditionSet({hex(self.value)})"

    # Additional operator overloads for convenience
    def __or__(self, other):
        if isinstance(other, LicenseConditionSet):
            return LicenseConditionSet(self.value | other.value)
        elif isinstance(other, LicenseCondition):
            return LicenseConditionSet(self.value | other.value)
        else:
            return NotImplemented

    def __and__(self, other):
        if isinstance(other, LicenseConditionSet):
            return LicenseConditionSet(self.value & other.value)
        elif isinstance(other, LicenseCondition):
            return LicenseConditionSet(self.value & other.value)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, LicenseConditionSet):
            return LicenseConditionSet(self.value & ~other.value)
        elif isinstance(other, LicenseCondition):
            return LicenseConditionSet(self.value & ~other.value)
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, LicenseConditionSet):
            return self.value == other.value
        return False

    def __contains__(self, item):
        if isinstance(item, LicenseCondition):
            return bool(self.value & item.value)
        return False

# AllLicenseConditions is the set of all recognized license conditions.
AllLicenseConditions = LicenseConditionSet(
    LicenseCondition.UnencumberedCondition,
    LicenseCondition.PermissiveCondition,
    LicenseCondition.NoticeCondition,
    LicenseCondition.ReciprocalCondition,
    LicenseCondition.RestrictedCondition,
    LicenseCondition.WeaklyRestrictedCondition,
    LicenseCondition.ProprietaryCondition,
    LicenseCondition.ByExceptionOnlyCondition,
    LicenseCondition.NotAllowedCondition,
)

# Example usage of ImpliesShared from condition.py
ImpliesShared = LicenseConditionSet(
    LicenseCondition.ReciprocalCondition,
    LicenseCondition.RestrictedCondition,
    LicenseCondition.WeaklyRestrictedCondition,
)
