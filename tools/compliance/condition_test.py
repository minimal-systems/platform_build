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

        # Check if a nil or unrecognized condition is not in `implies_share`
        self.assertFalse(
            LicenseCondition.validate_condition(0x0000),
            f"implies_share.HasAny(nil=0x0000) got true, want false"
        )

    def test_condition_name(self):
        # Test the name descriptions of recognized conditions
        recognized_conditions = {
            "Unencumbered: Public domain or public domain-like license that disclaims copyright.": LicenseCondition.UNENCUMBERED,
            "Permissive: License without notice or other significant requirements.": LicenseCondition.PERMISSIVE,
            "Notice: Open-source license with only notice or attribution requirements.": LicenseCondition.NOTICE,
            "Reciprocal: License with requirement to share the module's source only.": LicenseCondition.RECIPROCAL,
            "Restricted: License with requirement to share all source code linked to the module's source.": LicenseCondition.RESTRICTED,
            "Weakly Restricted: RestrictedCondition waived for dynamic linking.": LicenseCondition.WEAKLY_RESTRICTED,
            "Proprietary: License with source privacy requirements.": LicenseCondition.PROPRIETARY,
            "By Exception Only: License that applies under specific exceptions.": LicenseCondition.BY_EXCEPTION_ONLY,
            "Conditional: License with conditions that must be met for usage.": LicenseCondition.CONDITIONAL
        }

        for expected, condition in recognized_conditions.items():
            actual = LicenseCondition.describe(condition)
            self.assertEqual(expected, actual, f"unexpected name for condition {condition}: got {actual}, want {expected}")

    def test_condition_name_invalid_condition(self):
        # Test an invalid condition and expect a panic/exception
        with self.assertRaises(KeyError):
            invalid_condition = 0xFFFF  # Condition not in LicenseCondition
            LicenseCondition.describe(invalid_condition)


if __name__ == "__main__":
    unittest.main()
