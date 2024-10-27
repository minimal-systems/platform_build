#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
core_tests.py - Unified unit tests for core.py, strings_build.py, json_build.py, and math_build.py
"""

import unittest
import sys
import os
import inspect
import json
import io
from contextlib import redirect_stderr

# Adjust the import path if necessary
sys.path.append('/home/kjones/Documents/rebase/platform_build/common')

# Import modules to be tested
import core_build as *
import strings_build
import json_build
import math_build

# Patch pretty_message in core.py and strings_build.py
def patched_pretty_message(msg, level="error"):
    """
    Patched version of pretty_message to prevent sys.exit() during testing.
    """
    # Get the caller's frame, filename, and line number
    caller_frame = inspect.stack()[1]
    filename = os.path.basename(caller_frame.filename)
    lineno = caller_frame.lineno

    # Print the message in the format: filename:lineno: level: msg
    print(f"{filename}:{lineno}: {level}: {msg}", file=sys.stderr)

    # Instead of exiting, raise an exception for errors
    if level == "error":
        raise Exception(f"Error: {msg}")

# Patch pretty_message in the modules
core_build.pretty_message = patched_pretty_message
strings_build.pretty_message = patched_pretty_message

# Patch math_error in math_build.py
def patched_math_error(msg):
    """
    Patched version of math_error to prevent sys.exit() during testing.
    """
    print(f"Error: {msg}", file=sys.stderr)
    raise Exception(f"MathError: {msg}")

math_build.math_error = patched_math_error

###########################################################
## Test Classes for Each Module
###########################################################

class TestCoreFunctions(unittest.TestCase):
    """Test cases for core.py"""

    def test_constants(self):
        """Test the constants defined in core.py"""
        self.assertEqual(core_build.SHELL, os.environ.get('LINUX_BUILD_SHELL', '/bin/bash'))
        self.assertEqual(core_build.empty, '')
        self.assertEqual(core_build.space, ' ')
        self.assertEqual(core_build.comma, ',')
        self.assertEqual(core_build.newline, '\n')
        self.assertEqual(core_build.pound, '#')
        self.assertEqual(core_build.backslash, '\\')
        self.assertEqual(core_build.TOP, '.')
        self.assertEqual(core_build.top, '.')
        self.assertEqual(core_build.TOPDIR, '')
        self.assertEqual(core_build.topdir, '')

    def test_pretty_message_info(self):
        """Test that pretty_message outputs the correct info message"""
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            core_build.pretty_message("This is an info message", level="info")
        output = stderr.getvalue().strip()
        self.assertIn("core.py:", output)
        self.assertIn(": info: This is an info message", output)

    def test_pretty_message_warning(self):
        """Test that pretty_message outputs the correct warning message"""
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            core_build.pretty_message("This is a warning", level="warning")
        output = stderr.getvalue().strip()
        self.assertIn("core.py:", output)
        self.assertIn(": warning: This is a warning", output)

    def test_pretty_message_error(self):
        """Test that pretty_message raises an exception for error level"""
        with self.assertRaises(Exception) as context:
            core_build.pretty_message("This is an error", level="error")
        self.assertIn("Error: This is an error", str(context.exception))

class TestStringFunctions(unittest.TestCase):
    """Test cases for strings_build.py"""

    def test_to_lower(self):
        self.assertEqual(strings_build.to_lower("ABCDEF"), "abcdef")
        self.assertEqual(strings_build.to_lower("AbCdEf"), "abcdef")
        self.assertEqual(strings_build.to_lower(""), "")

    def test_to_upper(self):
        self.assertEqual(strings_build.to_upper("abcdef"), "ABCDEF")
        self.assertEqual(strings_build.to_upper("AbCdEf"), "ABCDEF")
        self.assertEqual(strings_build.to_upper(""), "")

    def test_streq(self):
        self.assertEqual(strings_build.streq("test", "test"), "true")
        self.assertEqual(strings_build.streq("test", "Test"), "")
        self.assertEqual(strings_build.streq(None, "test"), "")
        self.assertEqual(strings_build.streq("test", None), "")
        self.assertEqual(strings_build.streq(None, None), "")

    def test_normalize_path_list(self):
        self.assertEqual(strings_build.normalize_path_list("a b c"), "a:b:c")
        self.assertEqual(strings_build.normalize_path_list("  a   b   c  "), "a:b:c")
        self.assertEqual(strings_build.normalize_path_list(""), "")

    def test_normalize_comma_list(self):
        self.assertEqual(strings_build.normalize_comma_list("a b c"), "a,b,c")
        self.assertEqual(strings_build.normalize_comma_list("  a   b   c  "), "a,b,c")
        self.assertEqual(strings_build.normalize_comma_list(""), "")

    def test_word_colon(self):
        self.assertEqual(strings_build.word_colon(1, "a:b:c"), "a")
        self.assertEqual(strings_build.word_colon(2, "a:b:c"), "b")
        self.assertEqual(strings_build.word_colon(3, "a:b:c"), "c")
        self.assertEqual(strings_build.word_colon(4, "a:b:c"), "")

    def test_wordlist_colon(self):
        self.assertEqual(strings_build.wordlist_colon(1, 2, "a:b:c:d"), "a:b")
        self.assertEqual(strings_build.wordlist_colon(2, 3, "a:b:c:d"), "b:c")
        self.assertEqual(strings_build.wordlist_colon(3, 0, "a:b:c:d"), "c:d")
        self.assertEqual(strings_build.wordlist_colon(5, 0, "a:b:c:d"), "")

    def test_collapse_pairs(self):
        input_str = "a=b c= d e = f = g h="
        expected_output = "a=b c=d e=f=g h="
        self.assertEqual(strings_build.collapse_pairs(input_str), expected_output)

        input_str = "a:=b c:= d e :=f g := h"
        expected_output = "a:=b c:=d e:=f g:=h"
        self.assertEqual(strings_build.collapse_pairs(input_str, ":="), expected_output)

        input_str = "key1=value1 key2= value2 key3 =value3 key4 = value4"
        expected_output = "key1=value1 key2=value2 key3=value3 key4=value4"
        self.assertEqual(strings_build.collapse_pairs(input_str), expected_output)

    def test_uniq_pairs_by_first_component(self):
        input_str = "a:b a:c b:d c:e a:f"
        expected_output = "a:b b:d c:e"
        self.assertEqual(strings_build.uniq_pairs_by_first_component(input_str, ":"), expected_output)

        input_str = "key=value key=data key=info"
        expected_output = "key=value"
        self.assertEqual(strings_build.uniq_pairs_by_first_component(input_str), expected_output)

class TestJSONBuildFunctions(unittest.TestCase):
    """Test cases for json_build.py"""

    def test_json_building(self):
        """Test the JSON building functions in json_build.py"""
        # Start building the JSON structure
        json_build.json_start()
        json_build.add_json_str("name", "Example")
        json_build.add_json_bool("is_active", "true")
        json_build.add_json_list("items", "item1 item2 item3")
        json_build.add_json_csv("numbers", "1,2,3,4")

        # Add a nested JSON object
        json_build.add_json_map("address")
        json_build.add_json_str("city", "San Francisco")
        json_build.add_json_str("state", "CA")
        json_build.end_json_map()

        # Finalize the JSON content
        json_str = json_build.json_end()

        expected_json = {
            "name": "Example",
            "is_active": True,
            "items": ["item1", "item2", "item3"],
            "numbers": ["1", "2", "3", "4"],
            "address": {
                "city": "San Francisco",
                "state": "CA"
            }
        }
        self.assertEqual(json.loads(json_str), expected_json)

class TestMathBuildFunctions(unittest.TestCase):
    """Test cases for math_build.py"""

    def test_math_is_number_in_100(self):
        self.assertTrue(math_build.math_is_number_in_100(0))
        self.assertTrue(math_build.math_is_number_in_100(50))
        self.assertTrue(math_build.math_is_number_in_100(100))
        with self.assertRaises(Exception):
            math_build.math_is_number_in_100(-1)
        with self.assertRaises(Exception):
            math_build.math_is_number_in_100(101)

    def test_math_is_zero(self):
        self.assertTrue(math_build.math_is_zero(0))
        self.assertFalse(math_build.math_is_zero(1))

    def test_int_range_list(self):
        self.assertEqual(math_build.int_range_list(1, 5), [1, 2, 3, 4, 5])
        self.assertEqual(math_build.int_range_list(0, 0), [0])
        with self.assertRaises(Exception):
            math_build.int_range_list(-1, 5)
        with self.assertRaises(Exception):
            math_build.int_range_list(1, 101)

    def test_math_max(self):
        self.assertEqual(math_build.math_max(5, 10), 10)
        self.assertEqual(math_build.math_max(20, 15), 20)
        self.assertEqual(math_build.math_max(0, 0), 0)

    def test_math_min(self):
        self.assertEqual(math_build.math_min(5, 10), 5)
        self.assertEqual(math_build.math_min(20, 15), 15)
        self.assertEqual(math_build.math_min(0, 0), 0)

    def test_math_gt_or_eq(self):
        self.assertTrue(math_build.math_gt_or_eq(10, 5))
        self.assertTrue(math_build.math_gt_or_eq(5, 5))
        self.assertFalse(math_build.math_gt_or_eq(5, 10))

    def test_math_gt(self):
        self.assertTrue(math_build.math_gt(10, 5))
        self.assertFalse(math_build.math_gt(5, 5))
        self.assertFalse(math_build.math_gt(5, 10))

    def test_math_lt_or_eq(self):
        self.assertTrue(math_build.math_lt_or_eq(5, 10))
        self.assertTrue(math_build.math_lt_or_eq(5, 5))
        self.assertFalse(math_build.math_lt_or_eq(10, 5))

    def test_math_lt(self):
        self.assertTrue(math_build.math_lt(5, 10))
        self.assertFalse(math_build.math_lt(5, 5))
        self.assertFalse(math_build.math_lt(10, 5))

    def test_inc_and_print(self):
        self.assertEqual(math_build.inc_and_print(0), 1)
        self.assertEqual(math_build.inc_and_print(5), 6)

    def test_numbers_less_than(self):
        lst = ['1', '2', '3', '4', '5']
        self.assertEqual(math_build.numbers_less_than(3, lst), ['1', '2'])
        self.assertEqual(math_build.numbers_less_than(6, lst), ['1', '2', '3', '4', '5'])

    def test_numbers_greater_or_equal_to(self):
        lst = ['1', '2', '3', '4', '5']
        self.assertEqual(math_build.numbers_greater_or_equal_to(3, lst), ['3', '4', '5'])
        self.assertEqual(math_build.numbers_greater_or_equal_to(6, lst), [])

###########################################################
## Main Execution
###########################################################

if __name__ == "__main__":
    unittest.main()
