# conditionset.py

from condition import (
    LicenseCondition,
    RecognizedConditionNames,
    UnencumberedCondition,
    PermissiveCondition,
    NoticeCondition,
    ReciprocalCondition,
    RestrictedCondition,
    WeaklyRestrictedCondition,
    ProprietaryCondition,
    ByExceptionOnlyCondition,
    NotAllowedCondition,
)
import itertools

class LicenseConditionSet:
    """Identifies sets of license conditions."""

    def __init__(self, *conditions):
        self.value = 0
        for condition in conditions:
            if isinstance(condition, LicenseConditionSet):
                self.value |= condition.value
            elif isinstance(condition, LicenseCondition):
                self.value |= int(condition)
            elif isinstance(condition, int):
                self.value |= condition
            else:
                raise ValueError(f"Invalid condition type: {type(condition)}")

        # Ensure only valid bits are set
        self.value &= int(LicenseCondition.LicenseConditionMask)

    def Plus(self, *conditions):
        """Returns a new set containing all of the elements of `self` and `conditions`."""
        new_value = self.value
        for condition in conditions:
            if isinstance(condition, LicenseConditionSet):
                new_value |= condition.value
            elif isinstance(condition, LicenseCondition):
                new_value |= int(condition)
            elif isinstance(condition, int):
                new_value |= condition
            else:
                raise ValueError(f"Invalid condition type: {type(condition)}")
        return LicenseConditionSet(new_value)

    def Union(self, *others):
        """Returns a new set containing all of the elements of `self` and all of the elements of the `other` sets."""
        new_value = self.value
        for other in others:
            if isinstance(other, LicenseConditionSet):
                new_value |= other.value
            else:
                raise ValueError(f"Invalid condition type: {type(other)}")
        return LicenseConditionSet(new_value)

    def MatchingAny(self, *conditions):
        """Returns the subset of `self` equal to any of the `conditions`."""
        result_value = 0
        for condition in conditions:
            if isinstance(condition, LicenseCondition):
                result_value |= self.value & int(condition)
            elif isinstance(condition, int):
                result_value |= self.value & condition
            else:
                raise ValueError(f"Invalid condition type: {type(condition)}")
        return LicenseConditionSet(result_value)

    def MatchingAnySet(self, *others):
        """Returns the subset of `self` that are members of any of the `other` sets."""
        result_value = 0
        for other in others:
            if isinstance(other, LicenseConditionSet):
                result_value |= self.value & other.value
            else:
                raise ValueError(f"Invalid condition type: {type(other)}")
        return LicenseConditionSet(result_value)

    def HasAny(self, *conditions):
        """Returns True when `self` contains at least one of the `conditions`."""
        for condition in conditions:
            if isinstance(condition, LicenseCondition):
                if self.value & int(condition):
                    return True
            elif isinstance(condition, int):
                if self.value & condition:
                    return True
            else:
                raise ValueError(f"Invalid condition type: {type(condition)}")
        return False

    def MatchesAnySet(self, *others):
        """Returns True when `self` has a non-empty intersection with at least one of the `other` condition sets."""
        for other in others:
            if isinstance(other, LicenseConditionSet):
                if self.value & other.value:
                    return True
            else:
                raise ValueError(f"Invalid condition type: {type(other)}")
        return False

    def HasAll(self, *conditions):
        """Returns True when `self` contains every one of the `conditions`."""
        for condition in conditions:
            if isinstance(condition, LicenseCondition):
                if not (self.value & int(condition)):
                    return False
            elif isinstance(condition, int):
                if not (self.value & condition):
                    return False
            else:
                raise ValueError(f"Invalid condition type: {type(condition)}")
        return True

    def MatchesEverySet(self, *others):
        """Returns True when `self` has a non-empty intersection with each of the `other` condition sets."""
        for other in others:
            if isinstance(other, LicenseConditionSet):
                if not (self.value & other.value):
                    return False
            else:
                raise ValueError(f"Invalid condition type: {type(other)}")
        return True

    def Intersection(self, *others):
        """Returns the subset of `self` that are members of every `other` set."""
        result_value = self.value
        for other in others:
            if isinstance(other, LicenseConditionSet):
                result_value &= other.value
            else:
                raise ValueError(f"Invalid condition type: {type(other)}")
        return LicenseConditionSet(result_value)

    def Minus(self, *conditions):
        """Returns the subset of `self` that are not equal to any `conditions`."""
        result_value = self.value
        for condition in conditions:
            if isinstance(condition, LicenseCondition):
                result_value &= ~int(condition)
            elif isinstance(condition, int):
                result_value &= ~condition
            else:
                raise ValueError(f"Invalid condition type: {type(condition)}")
        return LicenseConditionSet(result_value)

    def Difference(self, *others):
        """Returns the subset of `self` that are not members of any `other` set."""
        result_value = self.value
        for other in others:
            if isinstance(other, LicenseConditionSet):
                result_value &= ~other.value
            else:
                raise ValueError(f"Invalid condition type: {type(other)}")
        return LicenseConditionSet(result_value)

    def Len(self):
        """Returns the number of license conditions in the set."""
        return bin(self.value).count('1')

    def AsList(self):
        """Returns a list of the license conditions in the set."""
        return [condition for condition in LicenseCondition if self.value & int(condition)]

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
            return LicenseConditionSet(self.value | int(other))
        elif isinstance(other, int):
            return LicenseConditionSet(self.value | other)
        else:
            return NotImplemented

    def __and__(self, other):
        if isinstance(other, LicenseConditionSet):
            return LicenseConditionSet(self.value & other.value)
        elif isinstance(other, LicenseCondition):
            return LicenseConditionSet(self.value & int(other))
        elif isinstance(other, int):
            return LicenseConditionSet(self.value & other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, LicenseConditionSet):
            return LicenseConditionSet(self.value & ~other.value)
        elif isinstance(other, LicenseCondition):
            return LicenseConditionSet(self.value & ~int(other))
        elif isinstance(other, int):
            return LicenseConditionSet(self.value & ~other)
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, LicenseConditionSet):
            return self.value == other.value
        return False

    def copy(self):
        """
        Creates a copy of the LicenseConditionSet instance.
        """
        return LicenseConditionSet(self.value)

    def __contains__(self, item):
        if isinstance(item, LicenseCondition):
            return bool(self.value & int(item))
        elif isinstance(item, int):
            return bool(self.value & item)
        else:
            return False

# Module-level function to create a new LicenseConditionSet
def NewLicenseConditionSet(*conditions):
    """Returns a set containing exactly the elements of `conditions`."""
    return LicenseConditionSet(*conditions)

# AllLicenseConditions is the set of all recognized license conditions.
AllLicenseConditions = LicenseConditionSet(
    UnencumberedCondition,
    PermissiveCondition,
    NoticeCondition,
    ReciprocalCondition,
    RestrictedCondition,
    WeaklyRestrictedCondition,
    ProprietaryCondition,
    ByExceptionOnlyCondition,
    NotAllowedCondition,
)

# Example usage of ImpliesShared from condition.py
ImpliesShared = LicenseConditionSet(
    ReciprocalCondition,
    RestrictedCondition,
    WeaklyRestrictedCondition,
)
