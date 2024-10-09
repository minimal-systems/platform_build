# policy_policy_test.py

import unittest
import logging

from policy_policy import (
    depConditionsPropagatingToTarget,
    targetConditionsPropagatingToDep,
    edgeIsDerivation,
    edgeIsDynamicLink,
    ImpliesRestricted,
    NewLicenseConditionSet,
    RecognizedConditionNames,
    LicenseConditionSet,
)

from graph import (
    LicenseGraph,
    TargetNode,
    TargetEdge,
    TargetEdgeAnnotations,
)

# Simulate the meta mapping from the Go code
meta = {
    'apacheBin.meta_lic': 'notice',
    'apacheLib.meta_lic': 'notice',
    'mitBin.meta_lic': 'notice',
    'mitLib.meta_lic': 'notice',
    'lgplLib.meta_lic': 'restricted_if_statically_linked',
    'gplLib.meta_lic': 'restricted',
    'gplBin.meta_lic': 'restricted',
    'gplContainer.meta_lic': 'restricted',
    'gplWithClasspathException.meta_lic': 'restricted',
    'dependentModule.meta_lic': 'notice',
    'proprietary.meta_lic': 'proprietary',
    'by_exception.meta_lic': 'by_exception_only',
    'mplLib.meta_lic': 'reciprocal',
    'mplBin.meta_lic': 'reciprocal',
    # Add more mappings as needed
}


class TestPolicyEdgeConditions(unittest.TestCase):
    def test_policy_edge_conditions(self):
        tests = [
            {
                'name': 'firstparty',
                'edge': {'target': 'apacheBin.meta_lic', 'dep': 'apacheLib.meta_lic', 'annotations': ['static']},
                'treatAsAggregate': False,
                'otherCondition': '',
                'expectedDepActions': [],
                'expectedTargetConditions': [],
            },
            {
                'name': 'notice',
                'edge': {'target': 'mitBin.meta_lic', 'dep': 'mitLib.meta_lic', 'annotations': ['static']},
                'treatAsAggregate': False,
                'otherCondition': '',
                'expectedDepActions': [],
                'expectedTargetConditions': [],
            },
            {
                'name': 'fponlgpl',
                'edge': {'target': 'apacheBin.meta_lic', 'dep': 'lgplLib.meta_lic', 'annotations': ['static']},
                'treatAsAggregate': False,
                'otherCondition': '',
                'expectedDepActions': [
                    'apacheBin.meta_lic:lgplLib.meta_lic:restricted_if_statically_linked',
                    'lgplLib.meta_lic:lgplLib.meta_lic:restricted_if_statically_linked',
                ],
                'expectedTargetConditions': [],
            },
            # Include all other test cases following the same structure...
        ]
        for tt in tests:
            with self.subTest(tt['name']):
                # Simulate reading the license graph
                lg = LicenseGraph()
                # Create TargetNodes for target and dependency
                target_node = TargetNode(tt['edge']['target'], proto={})
                dep_node = TargetNode(tt['edge']['dep'], proto={})
                # Assign license conditions based on the meta mapping
                target_condition_name = meta.get(tt['edge']['target'], 'notice')
                dep_condition_name = meta.get(tt['edge']['dep'], 'notice')
                target_condition = RecognizedConditionNames.get(target_condition_name)
                dep_condition = RecognizedConditionNames.get(dep_condition_name)
                target_node.licenseConditions = NewLicenseConditionSet(target_condition)
                dep_node.licenseConditions = NewLicenseConditionSet(dep_condition)
                # Create an edge between target and dependency
                annotations = tt['edge']['annotations']
                edge_annotations = TargetEdgeAnnotations(annotations)
                edge = TargetEdge(target_node, dep_node, edge_annotations)
                lg.add_edge(edge)
                # Simulate other conditions if any
                otherTarget = ''
                otn = None
                if tt['otherCondition']:
                    fields = tt['otherCondition'].split(':')
                    otherTarget = fields[0]
                    otherConditionName = fields[1]
                    otn = TargetNode(otherTarget, proto={})
                    other_condition = RecognizedConditionNames.get(otherConditionName)
                    otn.licenseConditions = NewLicenseConditionSet(other_condition)
                    lg.targets[otherTarget] = otn
                # Simulate depConditionsPropagatingToTarget
                if tt['expectedDepActions'] is not None:
                    depConditions = dep_node.LicenseConditions()
                    if otherTarget:
                        # Simulate a sub-dependency's condition having already propagated up to dep
                        depConditions |= otn.LicenseConditions()
                    logging.info(f"Calculating target actions for edge={edge}, dep conditions={depConditions}, treatAsAggregate={tt['treatAsAggregate']}")
                    csActual = depConditionsPropagatingToTarget(lg, edge, depConditions, tt['treatAsAggregate'])
                    logging.info(f"Calculated target conditions: {csActual}")
                    csExpected = NewLicenseConditionSet()
                    for triple in tt['expectedDepActions']:
                        fields = triple.split(':')
                        expectedConditions = NewLicenseConditionSet()
                        for cname in fields[2:]:
                            condition_name = RecognizedConditionNames.get(cname)
                            expectedConditions |= NewLicenseConditionSet(condition_name)
                        csExpected |= expectedConditions
                    logging.info(f"Expected target conditions: {csExpected}")
                    self.assertEqual(csActual, csExpected, f"Unexpected license conditions: got {csActual}, want {csExpected}")
                # Simulate targetConditionsPropagatingToDep
                if tt['expectedTargetConditions'] is not None:
                    targetConditions = target_node.LicenseConditions()
                    if otherTarget:
                        targetConditions |= otn.LicenseConditions()
                    logging.info(f"Calculating dep conditions for edge={edge}, target conditions={targetConditions.Names()}, treatAsAggregate={tt['treatAsAggregate']}")
                    cs = targetConditionsPropagatingToDep(lg, edge, targetConditions, tt['treatAsAggregate'], lambda tn: tn.LicenseConditions())
                    logging.info(f"Calculated dep conditions: {cs.Names()}")
                    actual = cs.Names()
                    expected = [cond.split(':')[1] for cond in tt['expectedTargetConditions']]
                    actual.sort()
                    expected.sort()
                    self.assertEqual(actual, expected, f"Unexpected target conditions: got {actual}, want {expected}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
