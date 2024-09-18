from core import *

# Constants
MATH_POS_NUMBERS = list(range(1, 101))
MATH_NUMBERS = [0] + MATH_POS_NUMBERS
MATH_ONE_NUMBERS = list(range(10))

# Error handling
def math_error(message):
    pretty_error(message)

# Math functions
def math_is_number_in_100(num):
    if num is None:
        math_error("Argument missing")
    if not isinstance(num, int) or num not in MATH_NUMBERS:
        return False
    return True

def math_is_number(num):
    if num is None:
        math_error("Argument missing")
    if not isinstance(num, int):
        return False
    if math_is_number_in_100(num):
        return True
    return num >= 0

def math_is_zero(num):
    if num is None:
        math_error("Argument missing")
    if num == 0:
        return True
    return False

def int_range_list(start, end):
    if not math_is_number_in_100(start):
        math_error(f"Only non-negative integers <= 100 are supported (not {start})")
    if not math_is_number_in_100(end):
        math_error(f"Only non-negative integers <= 100 are supported (not {end})")
    if start > end:
        return []
    return list(range(start, end + 1))

def _math_number_to_list(num):
    if not math_is_number(num):
        math_error(f"Only non-negative integers are supported (not {num})")
    num_str = str(num)
    if len(num_str) >= 9:
        math_error(f"Only non-negative integers with less than 9 digits are supported (not {num})")
    if num_str.startswith("0") and len(num_str) > 1:
        math_error(f"Only non-negative integers without leading zeros are supported (not {num})")
    return [int(d) for d in num_str]

def _math_1digit_comp(d1, d2):
    if d1 == d2:
        return 0
    return 1 if d1 > d2 else -1

def _math_list_comp(list1, list2):
    for d1, d2 in zip(list1, list2):
        comp = _math_1digit_comp(d1, d2)
        if comp != 0:
            return comp
    return 0

def _math_ext_comp(num1, num2):
    list1 = _math_number_to_list(num1)
    list2 = _math_number_to_list(num2)
    len1, len2 = len(list1), len(list2)
    comp = _math_1digit_comp(len1, len2)
    if comp != 0:
        return comp
    return _math_list_comp(list1, list2)

def math_max(num1, num2):
    if not (math_is_number_in_100(num1) and math_is_number_in_100(num2)):
        math_error(f"Only non-negative integers <= 100 are supported (not {num1} or {num2})")
    return max(num1, num2)

def math_min(num1, num2):
    if not (math_is_number_in_100(num1) and math_is_number_in_100(num2)):
        math_error(f"Only non-negative integers <= 100 are supported (not {num1} or {num2})")
    return min(num1, num2)

def math_gt_or_eq(num1, num2):
    return num1 >= num2

def math_gt(num1, num2):
    return num1 > num2

def math_lt_or_eq(num1, num2):
    return num1 <= num2

def math_lt(num1, num2):
    return num1 < num2

def numbers_less_than(limit, numbers):
    return [n for n in numbers if math_is_number(n) and n < limit]

def numbers_greater_or_equal_to(limit, numbers):
    return [n for n in numbers if math_is_number(n) and n >= limit]

def int_plus(num1, num2):
    return num1 + num2

def int_subtract(num1, num2):
    result = num1 - num2
    if result < 0:
        math_error(f"subtract underflow {num1} - {num2}")
    return result

def int_multiply(num1, num2):
    return num1 * num2

def int_divide(num1, num2):
    if num2 == 0:
        math_error("division by zero is not allowed!")
    return num1 // num2

def inc_and_print(variable_name, namespace):
    namespace[variable_name] = namespace.get(variable_name, 0) + 1
    return namespace[variable_name]

def main():
    # Example usage
    assert math_is_number(0)
    assert math_is_number(2)
    assert math_is_number(202412)
    assert not math_is_number("foo")
    assert not math_is_number(-1)
    
    assert math_is_zero(0)
    assert not math_is_zero(1)
    assert not math_is_zero("foo")
    
    assert int_range_list(0, 1) == [0, 1]
    assert int_range_list(1, 1) == [1]
    assert int_range_list(1, 2) == [1, 2]
    assert int_range_list(2, 1) == []
    
    assert _math_number_to_list(123) == [1, 2, 3]
    
    assert _math_1digit_comp(1, 1) == 0
    assert _math_1digit_comp(0, 9) == -1
    assert _math_1digit_comp(3, 1) == 1
    
    assert _math_ext_comp(5, 10) == -1
    assert _math_ext_comp(12345, 12345) == 0
    assert _math_ext_comp(500, 5) == 1
    
    assert math_max(5, 42) == 42
    assert math_min(7, 32) == 7
    
    assert math_gt_or_eq(2, 1)
    assert not math_gt_or_eq(1, 2)
    
    assert numbers_less_than(3, [0, 2, 1, 3]) == [0, 2, 1]
    assert numbers_greater_or_equal_to(2, [0, 2, 1, 3]) == [2, 3]
    
    assert int_plus(1, 100) == 101
    assert int_subtract(100, 1) == 99
    assert int_multiply(4, 100) == 400
    assert int_divide(200, 3) == 66
    
    print("All tests passed.") # type: ignore