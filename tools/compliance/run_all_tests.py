#!/usr/bin/env python3
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
import time

# Set the path to the compliance directory for imports.
COMPLIANCE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, COMPLIANCE_DIR)

# Colors for ninja-style output.
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_test_start(file_name):
    """Print a ninja-style message indicating that a test file is starting."""
    print(f"{Colors.OKCYAN}Starting test: {file_name}...{Colors.ENDC}")

def print_test_result(file_name, success, time_taken):
    """Print a ninja-style message for test results."""
    if success:
        print(f"{Colors.OKGREEN}PASS: {file_name} ({time_taken:.3f}s){Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}FAIL: {file_name} ({time_taken:.3f}s){Colors.ENDC}")

def print_final_results(success, total_tests, total_time):
    """Print a final summary of the test results."""
    if success:
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}All {total_tests} tests passed! ({total_time:.3f}s total){Colors.ENDC}")
    else:
        print(f"\n{Colors.BOLD}{Colors.FAIL}Some tests failed. ({total_time:.3f}s total){Colors.ENDC}")

def run_all_tests():
    """Run all test files in the current directory and subdirectories."""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=COMPLIANCE_DIR, pattern="*_test.py")

    # Print all the test files being run
    print(f"{Colors.HEADER}Running the following test files:\n{Colors.ENDC}")
    test_files = []
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            for sub_test in test:
                if isinstance(sub_test, unittest.TestSuite):
                    for case in sub_test:
                        file_name = f"{case.__module__.replace('.', '/')}.py"
                        if file_name not in test_files:
                            test_files.append(file_name)
                            print(f"  - {file_name}")

    print(f"\n{Colors.HEADER}============================== Test Results =============================={Colors.ENDC}")

    # Run the test suite and measure total time
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=0, resultclass=unittest.TextTestResult)
    total_tests = 0
    all_successful = True

    for test_file in test_files:
        # Run tests for each file separately and measure time for each
        file_start_time = time.time()
        print_test_start(test_file)
        result = runner.run(loader.loadTestsFromName(test_file.replace('/', '.').replace('.py', '')))
        file_end_time = time.time()
        time_taken = file_end_time - file_start_time

        # Count total number of tests and update success status
        total_tests += result.testsRun
        all_successful = all_successful and result.wasSuccessful()

        # Print test result in ninja-style format
        print_test_result(test_file, result.wasSuccessful(), time_taken)

    end_time = time.time()
    total_time = end_time - start_time

    # Print the final results in ninja-style
    print_final_results(all_successful, total_tests, total_time)

    # Exit with appropriate code
    exit_code = 0 if all_successful else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    run_all_tests()
