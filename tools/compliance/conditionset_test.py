# conditionset_test.py

import unittest
from condition import LicenseCondition, RecognizedConditionNames
from conditionset import LicenseConditionSet, AllLicenseConditions, NewLicenseConditionSet

class TestConditionSet(unittest.TestCase):
    def test_condition_set(self):
        tests = [
            {
                'name': 'empty',
                'conditions': [],
                'plus': [],
                'minus': None,
                'matchingAny': {
                    'notice': [],
                    'restricted': [],
                    'restricted|reciprocal': [],
                },
                'expected': [],
            },
            {
                'name': 'emptyminusnothing',
                'conditions': [],
                'plus': None,
                'minus': [],
                'matchingAny': {
                    'notice': [],
                    'restricted': [],
                    'restricted|reciprocal': [],
                },
                'expected': [],
            },
            {
                'name': 'emptyminusnotice',
                'conditions': [],
                'plus': None,
                'minus': ['notice'],
                'matchingAny': {
                    'notice': [],
                    'restricted': [],
                    'restricted|reciprocal': [],
                },
                'expected': [],
            },
            {
                'name': 'noticeonly',
                'conditions': ['notice'],
                'plus': None,
                'minus': None,
                'matchingAny': {
                    'notice': ['notice'],
                    'notice|proprietary': ['notice'],
                    'restricted': [],
                },
                'expected': ['notice'],
            },
            {
                'name': 'allnoticeonly',
                'conditions': ['notice'],
                'plus': ['notice'],
                'minus': None,
                'matchingAny': {
                    'notice': ['notice'],
                    'notice|proprietary': ['notice'],
                    'restricted': [],
                },
                'expected': ['notice'],
            },
            {
                'name': 'emptyplusnotice',
                'conditions': [],
                'plus': ['notice'],
                'minus': None,
                'matchingAny': {
                    'notice': ['notice'],
                    'notice|proprietary': ['notice'],
                    'restricted': [],
                },
                'expected': ['notice'],
            },
            {
                'name': 'everything',
                'conditions': ['unencumbered', 'permissive', 'notice', 'reciprocal', 'restricted', 'proprietary'],
                'plus': ['restricted_if_statically_linked', 'by_exception_only', 'not_allowed'],
                'minus': None,
                'matchingAny': {
                    'unencumbered': ['unencumbered'],
                    'permissive': ['permissive'],
                    'notice': ['notice'],
                    'reciprocal': ['reciprocal'],
                    'restricted': ['restricted'],
                    'restricted_if_statically_linked': ['restricted_if_statically_linked'],
                    'proprietary': ['proprietary'],
                    'by_exception_only': ['by_exception_only'],
                    'not_allowed': ['not_allowed'],
                    'notice|proprietary': ['notice', 'proprietary'],
                },
                'expected': [
                    'unencumbered',
                    'permissive',
                    'notice',
                    'reciprocal',
                    'restricted',
                    'restricted_if_statically_linked',
                    'proprietary',
                    'by_exception_only',
                    'not_allowed',
                ],
            },
            # Additional test cases can be added here following the same structure.
        ]

        for tt in tests:
            def toConditions(names):
                return [RecognizedConditionNames[name] for name in names]

            def populate():
                testSet = NewLicenseConditionSet(*toConditions(tt['conditions']))
                if tt.get('plus') is not None:
                    testSet = testSet.Plus(*toConditions(tt['plus']))
                if tt.get('minus') is not None:
                    testSet = testSet.Minus(*toConditions(tt['minus']))
                return testSet

            def populateSet():
                testSet = NewLicenseConditionSet(*toConditions(tt['conditions']))
                if tt.get('plus') is not None:
                    testSet = testSet.Union(NewLicenseConditionSet(*toConditions(tt['plus'])))
                if tt.get('minus') is not None:
                    testSet = testSet.Difference(NewLicenseConditionSet(*toConditions(tt['minus'])))
                return testSet

            def populatePlusSet():
                testSet = NewLicenseConditionSet(*toConditions(tt['conditions']))
                if tt.get('plus') is not None:
                    testSet = testSet.Union(NewLicenseConditionSet(*toConditions(tt['plus'])))
                if tt.get('minus') is not None:
                    testSet = testSet.Minus(*toConditions(tt['minus']))
                return testSet

            def populateMinusSet():
                testSet = NewLicenseConditionSet(*toConditions(tt['conditions']))
                if tt.get('plus') is not None:
                    testSet = testSet.Plus(*toConditions(tt['plus']))
                if tt.get('minus') is not None:
                    testSet = testSet.Difference(NewLicenseConditionSet(*toConditions(tt['minus'])))
                return testSet

            def checkMatching(cs):
                for data, expectedNames in tt['matchingAny'].items():
                    expectedConditions = toConditions(expectedNames)
                    expected = NewLicenseConditionSet(*expectedConditions)
                    data_conditions = toConditions(data.split('|'))
                    actual = cs.MatchingAny(*data_conditions)
                    actualNames = actual.Names()

                    self.assertEqual(actual, expected, f"MatchingAny({data}): got {actual}, want {expected}")
                    self.assertEqual(len(actualNames), len(expectedNames),
                                     f"len(MatchingAny({data}).Names()): got {len(actualNames)}, want {len(expectedNames)}")
                    for i in range(len(actualNames)):
                        self.assertEqual(actualNames[i], expectedNames[i],
                                         f"MatchingAny({data}).Names()[{i}]: got {actualNames[i]}, want {expectedNames[i]}")

                    actualConditions = actual.AsList()
                    self.assertEqual(len(actualConditions), len(expectedConditions),
                                     f"len(MatchingAny({data}).AsList()): got {len(actualConditions)}, want {len(expectedConditions)}")
                    for i in range(len(actualConditions)):
                        self.assertEqual(actualConditions[i], expectedConditions[i],
                                         f"MatchingAny({data}).AsList()[{i}]: got {actualConditions[i]}, want {expectedConditions[i]}")

            def checkExpected(actual):
                expectedConditions = toConditions(tt['expected'])
                expected = NewLicenseConditionSet(*expectedConditions)
                actualNames = actual.Names()

                self.assertEqual(actual, expected, f"checkExpected: got {actual}, want {expected}")
                self.assertEqual(len(actualNames), len(tt['expected']),
                                 f"len(actual.Names()): got {len(actualNames)}, want {len(tt['expected'])}")

                for i in range(len(actualNames)):
                    self.assertEqual(actualNames[i], tt['expected'][i],
                                     f"actual.Names()[{i}]: got {actualNames[i]}, want {tt['expected'][i]}")

                actualConditions = actual.AsList()
                self.assertEqual(len(actualConditions), len(expectedConditions),
                                 f"len(actual.AsList()): got {len(actualConditions)}, want {len(expectedConditions)}")

                for i in range(len(actualConditions)):
                    self.assertEqual(actualConditions[i], expectedConditions[i],
                                     f"actual.AsList()[{i}]: got {actualConditions[i]}, want {expectedConditions[i]}")

                if len(tt['expected']) == 0:
                    self.assertTrue(actual.IsEmpty(), "actual.IsEmpty(): got False, want True")
                    self.assertFalse(actual.HasAny(*expectedConditions), "actual.HasAny(): got True, want False")
                else:
                    self.assertFalse(actual.IsEmpty(), "actual.IsEmpty(): got True, want False")
                    self.assertTrue(actual.HasAny(*expectedConditions), "actual.HasAny(all expected): got False, want True")
                self.assertTrue(actual.HasAll(*expectedConditions), "actual.HasAll(all expected): want True, got False")

                for expectedCondition in expectedConditions:
                    self.assertTrue(actual.HasAny(expectedCondition),
                                    f"actual.HasAny({expectedCondition.Name()}): got False, want True")
                    self.assertTrue(actual.HasAll(expectedCondition),
                                    f"actual.HasAll({expectedCondition.Name()}): got False, want True")

                notExpected = AllLicenseConditions - expected
                notExpectedList = notExpected.AsList()

                if len(tt['expected']) == 0:
                    self.assertFalse(actual.HasAny(*(expectedConditions + notExpectedList)),
                                     "actual.HasAny(all conditions): want False, got True")
                else:
                    self.assertTrue(actual.HasAny(*(expectedConditions + notExpectedList)),
                                    "actual.HasAny(all conditions): want True, got False")

                if len(notExpectedList) == 0:
                    self.assertTrue(actual.HasAll(*(expectedConditions + notExpectedList)),
                                    "actual.HasAll(all conditions): want True, got False")
                else:
                    self.assertFalse(actual.HasAll(*(expectedConditions + notExpectedList)),
                                     "actual.HasAll(all conditions): want False, got True")

                for unexpectedCondition in notExpectedList:
                    self.assertFalse(actual.HasAny(unexpectedCondition),
                                     f"actual.HasAny({unexpectedCondition.Name()}): got True, want False")
                    self.assertFalse(actual.HasAll(unexpectedCondition),
                                     f"actual.HasAll({unexpectedCondition.Name()}): got True, want False")

            # Run the tests
            cs = populate()
            checkExpected(cs)
            checkMatching(cs)

            # Similarly test with populateSet, populatePlusSet, and populateMinusSet
            cs_set = populateSet()
            checkExpected(cs_set)

            cs_plusset = populatePlusSet()
            checkExpected(cs_plusset)

            cs_minusset = populateMinusSet()
            checkExpected(cs_minusset)

if __name__ == '__main__':
    unittest.main()
