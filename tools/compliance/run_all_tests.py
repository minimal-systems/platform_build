# tools/compliance/run_all_tests.py

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

import unittest
import os
import sys

# Set the path to the compliance directory for imports
COMPLIANCE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, COMPLIANCE_DIR)

def run_all_tests():
    """Run all test files in the current directory and subdirectories."""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=COMPLIANCE_DIR, pattern="*_test.py")

    # Print all the test files being run
    print("Running the following test files:\n")
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            for sub_test in test:
                if isinstance(sub_test, unittest.TestSuite):
                    for case in sub_test:
                        print(f"Running test file: {case.__module__.replace('.', '/')}.py")

    print("\n============================== Test Results ==============================")

    # Run the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print the results
    if result.wasSuccessful():
        print("\nAll tests passed!")
        exit_code = 0
    else:
        print("\nSome tests failed.")
        exit_code = 1

    sys.exit(exit_code)

if __name__ == "__main__":
    run_all_tests()
