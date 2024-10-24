#
# Copyright (C) 2024 The Minimal Systems Project
# SPDX-License-Identifier: GPL-2.0-or-later
# math_build.py - Math building functions for the build system.

import sys

###########################################################
# Basic math functions for non-negative integers <= 100
###########################################################

# List of positive integers <= 100
MATH_POS_NUMBERS = list(range(1, 101))
MATH_NUMBERS = [0] + MATH_POS_NUMBERS
MATH_ONE_NUMBERS = list(range(10))

# Print error and exit
def math_error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)

# Run math tests if enabled
RUN_MATH_TESTS = False

if RUN_MATH_TESTS:
    MATH_TEST_FAILURE = False
    MATH_TEST_ERROR = None

    def math_expect(got, expected):
        if got != expected:
            print(f"Expected {expected}, but got {got}")
            MATH_TEST_FAILURE = True

    def math_expect_true(value):
        math_expect(value, True)

    def math_expect_false(value):
        math_expect(value, False)

    def math_expect_error(got, expected_error_msg):
        if got != expected_error_msg:
            print(f"Error: {got} != {expected_error_msg}")
            MATH_TEST_FAILURE = True

# Returns true if a number is a non-negative integer <= 100, otherwise returns nothing.
def math_is_number_in_100(n):
    if n is None:
        math_error("Argument missing")
    if isinstance(n, int) and 0 <= n <= 100:
        return True
    return False

# Same as math_is_number_in_100, but no limit.
def _math_ext_is_number(n):
    if n is None:
        math_error("Argument missing")
    try:
        int(n)
        return True
    except ValueError:
        math_error(f"Only non-negative integers are supported (not {n})")
    return False

# Returns true if a number is zero.
def math_is_zero(n):
    return n == 0

# Return a list of integers in the range [start, end].
def int_range_list(start, end):
    if not math_is_number_in_100(start) or not math_is_number_in_100(end):
        math_error(f"Only non-negative integers <= 100 are supported (not {start}, {end})")
    return list(range(start, end + 1))

# Split an integer into a list of digits.
def _math_number_to_list(n):
    if not _math_ext_is_number(n):
        math_error(f"Only non-negative integers are supported (not {n})")
    num_str = str(n)
    if len(num_str) > 9:
        math_error(f"Only non-negative integers with less than 9 digits are supported (not {n})")
    if num_str.startswith("0") and len(num_str) > 1:
        math_error(f"Only non-negative integers without leading zeros are supported (not {n})")
    return list(map(int, num_str))

# Compare 1-digit integers and return comparison result.
def _math_1digit_comp(a, b):
    return (a > b) - (a < b)

# Compare lists of digits of the same length.
def _math_list_comp(list1, list2, length):
    for i in range(length):
        comp = _math_1digit_comp(list1[i], list2[i])
        if comp != 0:
            return comp
    return 0

# Compare any two non-negative integers.
def _math_ext_comp(a, b):
    list1 = _math_number_to_list(a)
    list2 = _math_number_to_list(b)
    if len(list1) != len(list2):
        return _math_1digit_comp(len(list1), len(list2))
    return _math_list_comp(list1, list2, len(list1))

# Return the greater of two numbers.
def math_max(a, b):
    return a if _math_ext_comp(a, b) > 0 else b

# Return the lesser of two numbers.
def math_min(a, b):
    return a if _math_ext_comp(a, b) < 0 else b

# Compare if first number is greater or equal to second.
def math_gt_or_eq(a, b):
    return _math_ext_comp(a, b) >= 0

# Compare if first number is greater than second.
def math_gt(a, b):
    return _math_ext_comp(a, b) > 0

# Compare if first number is less or equal to second.
def math_lt_or_eq(a, b):
    return _math_ext_comp(a, b) <= 0

# Compare if first number is less than second.
def math_lt(a, b):
    return _math_ext_comp(a, b) < 0

# Increment a variable and return the result.
def inc_and_print(var):
    return var + 1

# Return the words in the list that are numbers and are less than a given value.
def numbers_less_than(n, lst):
    return [x for x in lst if _math_ext_is_number(x) and math_lt(x, n)]

# Return the words in the list that are numbers and are greater or equal to a given value.
def numbers_greater_or_equal_to(n, lst):
    return [x for x in lst if _math_ext_is_number(x) and math_gt_or_eq(x, n)]

# Run tests (if enabled).
if RUN_MATH_TESTS:
    math_expect_true(math_is_zero(0))
    math_expect_false(math_is_zero(1))
    math_expect_true(math_is_number_in_100(100))
    math_expect_false(math_is_number_in_100(101))
    math_expect(math_max(5, 10), 10)
    math_expect(math_min(5, 10), 5)
    math_expect(inc_and_print(0), 1)
    math_expect(inc_and_print(1), 2)
    print("Math tests passed!" if not MATH_TEST_FAILURE else "Math tests failed!")
