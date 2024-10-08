import unittest
from condition import LicenseCondition


class TestConditionSet(unittest.TestCase):
    def setUp(self):
        # Setting up the implied shared conditions
        self.implies_share = {
            LicenseCondition.RESTRICTED,
            LicenseCondition.RECIPROCAL,
            LicenseCondition.WEAKLY_RESTRICTED,
            LicenseCondition.PROPRIETARY,
        }

    def test_condition_set_has(self):
        # Testing with `implies_share` set up in `setUp`
        print(f"testing with implies_share={self.implies_share}")

        # Check if NOTICE condition is not in `implies_share`
        self.assertFalse(
            LicenseCondition.NOTICE in self.implies_share,
            f"implies_share.HasAny(\"notice\"={LicenseCondition.NOTICE}) got true, want false"
        )

        # Check if RESTRICTED condition is in `implies_share`
        self.assertTrue(
            LicenseCondition.RESTRICTED in self.implies_share,
            f"implies_share.HasAny(\"restricted\"={LicenseCondition.RESTRICTED}) got false, want true"
        )

        # Check if RECIPROCAL condition is in `implies_share`
        self.assertTrue(
            LicenseCondition.RECIPROCAL in self.implies_share,
            f"implies_share.HasAny(\"reciprocal\"={LicenseCondition.RECIPROCAL}) got false, want true"
        )

        # Check if a zero-value or unrecognized condition is not in `implies_share`
        self.assertFalse(
            0x0000 in LicenseCondition.RECOGNIZED_CONDITION_NAMES.values(),
            f"implies_share.HasAny(\"unrecognized\"=0x0000) got true, want false"
        )

    def test_condition_name(self):
        # Test the name descriptions of recognized conditions
        recognized_conditions = {
            "Public domain or public domain-like license that disclaims copyright.": LicenseCondition.UNENCUMBERED,
            "License without notice or other significant requirements.": LicenseCondition.PERMISSIVE,
            "Typical open-source license with only notice or attribution requirements.": LicenseCondition.NOTICE,
            "License with requirement to share the module's source only.": LicenseCondition.RECIPROCAL,
            "License with requirement to share all source code linked to the module's source.": LicenseCondition.RESTRICTED,
            "Restricted license condition waived for dynamic linking.": LicenseCondition.WEAKLY_RESTRICTED,
            "License with source privacy requirements.": LicenseCondition.PROPRIETARY,
            "License where policy requires product counsel review prior to use.": LicenseCondition.BY_EXCEPTION_ONLY,
            "License with conditions that must be met for usage.": LicenseCondition.CONDITIONAL
        }

        for expected, condition in recognized_conditions.items():
            actual = LicenseCondition.describe(condition)
            self.assertEqual(expected, actual, f"unexpected name for condition {condition}: got {actual}, want {expected}")

    def test_condition_name_invalid_condition(self):
        # Test an invalid condition and expect a panic/exception
        with self.assertRaises(ValueError):
            invalid_condition = 0xFFFF  # Condition not in LicenseCondition
            LicenseCondition.describe(invalid_condition)


if __name__ == "__main__":
    unittest.main()
