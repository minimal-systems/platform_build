# condition_test.py

import unittest
from condition import LicenseCondition, RecognizedConditionNames, ImpliesShared

class TestConditionSetHas(unittest.TestCase):
    def test_has_any(self):
        implies_share = ImpliesShared

        print(f"testing with implies_share={implies_share}")

        if implies_share.HasAny(LicenseCondition.NoticeCondition):
            self.fail(f"implies_share.HasAny('notice'={LicenseCondition.NoticeCondition}) got True, want False")

        if not implies_share.HasAny(LicenseCondition.RestrictedCondition):
            self.fail(f"implies_share.HasAny('restricted'={LicenseCondition.RestrictedCondition}) got False, want True")

        if not implies_share.HasAny(LicenseCondition.ReciprocalCondition):
            self.fail(f"implies_share.HasAny('reciprocal'={LicenseCondition.ReciprocalCondition}) got False, want True")

        if implies_share.HasAny(LicenseCondition(0x0000)):
            self.fail(f"implies_share.HasAny(nil={LicenseCondition(0x0000)}) got True, want False")

class TestConditionName(unittest.TestCase):
    def test_condition_name(self):
        for expected, condition in RecognizedConditionNames.items():
            actual = condition.Name()
            if expected != actual:
                self.fail(f"unexpected name for condition {condition}: got {actual}, want {expected}")

class TestConditionNameInvalidCondition(unittest.TestCase):
    def test_invalid_condition_name(self):
        panicked = False
        lc = LicenseCondition(0x0)
        try:
            name = lc.Name()
            self.fail(f"invalid condition unexpected name: got {name}, wanted exception")
        except ValueError:
            panicked = True
        if not panicked:
            self.fail(f"no expected exception for {lc}.Name(): got no exception, wanted exception")

if __name__ == '__main__':
    unittest.main()
