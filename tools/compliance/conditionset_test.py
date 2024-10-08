# conditionset_test.py

import unittest
from conditionset import LicenseCondition, LicenseConditionSet

# Mapping of condition names to LicenseCondition constants.
RecognizedConditionNames = {
    "unencumbered": LicenseCondition.UNENCUMBERED,
    "permissive": LicenseCondition.PERMISSIVE,
    "notice": LicenseCondition.NOTICE,
    "reciprocal": LicenseCondition.RECIPROCAL,
    "restricted": LicenseCondition.RESTRICTED,
    "weakly_restricted": LicenseCondition.WEAKLY_RESTRICTED,
    "proprietary": LicenseCondition.PROPRIETARY,
    "by_exception_only": LicenseCondition.BY_EXCEPTION_ONLY,
    "conditional": LicenseCondition.CONDITIONAL,
}


class TestConditionSet(unittest.TestCase):
    """Unit tests for LicenseConditionSet."""

    def to_conditions(self, names):
        """Convert a list of condition names to a list of LicenseCondition values."""
        return [RecognizedConditionNames[name] for name in names]

    def populate_set(self, conditions, plus=None, minus=None):
        """Populate a LicenseConditionSet based on initial conditions, plus, and minus sets."""
        test_set = LicenseConditionSet(*self.to_conditions(conditions))
        if plus:
            test_set = test_set.plus(*self.to_conditions(plus))
        if minus:
            test_set = test_set.minus(*self.to_conditions(minus))
        return test_set

    def test_condition_set(self):
        """Run test cases based on converted Go test cases."""
        tests = [
            {
                "name": "empty",
                "conditions": [],
                "plus": [],
                "minus": [],
                "matchingAny": {
                    "notice": [],
                    "restricted": [],
                    "restricted|reciprocal": [],
                },
                "expected": [],
            },
            # Additional test cases can be added here...
        ]

        for tt in tests:
            with self.subTest(tt["name"]):
                cs = self.populate_set(tt["conditions"], tt.get("plus"), tt.get("minus"))
                expected_conditions = LicenseConditionSet(*self.to_conditions(tt["expected"]))
                self.assertEqual(cs, expected_conditions, f"Test {tt['name']} failed")

                # Check MatchingAny
                for key, expected_names in tt["matchingAny"].items():
                    expected = LicenseConditionSet(*self.to_conditions(expected_names))
                    actual = cs.matching_any(*self.to_conditions(key.split("|")))
                    self.assertEqual(actual, expected, f"MatchingAny failed for {tt['name']} and key {key}")


if __name__ == "__main__":
    unittest.main()
