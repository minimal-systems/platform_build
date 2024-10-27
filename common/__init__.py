# __init__.py for build.common
# Copyright (C) 2024 The Minimal Systems Project
# SPDX-License-Identifier: GPL-2.0-or-later

# Import all modules and their components
from .core_build import (
    pretty_message, SHELL, empty, space, comma, newline, 
    pound, backslash, TOP, TOPDIR
)
from .json_build import (
    json_start, json_end, add_json_str, add_json_bool, 
    add_json_list, add_json_csv, add_json_map, 
    add_json_array, end_json_map, end_json_array
)
from .math_build import (
    math_is_number_in_100, math_is_zero, int_range_list,
    math_max, math_min, math_gt_or_eq, math_gt,
    math_lt_or_eq, math_lt, numbers_less_than,
    numbers_greater_or_equal_to
)
from .strings_build import (
    to_lower, to_upper, streq, normalize_path_list,
    normalize_comma_list, word_colon, wordlist_colon,
    collapse_pairs, uniq_pairs_by_first_component
)