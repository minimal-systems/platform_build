#
# Copyright (C) 2024 The Minimal Systems Project
# SPDX-License-Identifier: GPL-2.0-or-later
# json_build.py - JSON building functions for the build system.

import json

# Initialize the JSON contents and indentation level
json_contents, json_indent, indent_level = {}, 4, 0

# Utility functions for managing indentation
increase_indent = lambda: globals().update(indent_level=indent_level+json_indent)
decrease_indent = lambda: globals().update(indent_level=indent_level-json_indent)
get_indent = lambda: ' ' * indent_level

# Convert a list to a JSON list (space-separated or comma-separated)
json_list = lambda lst, separator=' ': [item.strip() for item in lst.split(separator)] if lst else []
csv_to_json_list = lambda lst: json_list(lst, separator=',')

# Add key-value pairs to the JSON object
add_json_val = lambda key, value: json_contents.update({key.strip(): value})
add_json_str = lambda key, value: add_json_val(key, value.strip())  # No quotes around string values
add_json_list = lambda key, value: add_json_val(key, json_list(value))
add_json_csv = lambda key, value: add_json_val(key, csv_to_json_list(value))
add_json_bool = lambda key, value: add_json_val(key, True if value.strip() else False)

# Handle JSON objects and arrays
add_json_map = lambda key: [json_contents.update({key.strip(): {}}), increase_indent()]
add_json_map_anon = lambda: increase_indent()
end_json_map = lambda: decrease_indent()

add_json_array = lambda key: [json_contents.update({key.strip(): []}), increase_indent()]
end_json_array = lambda: decrease_indent()

# Start and end the JSON file structure
json_start = lambda: [globals().update(json_contents={}, indent_level=json_indent)]
json_end = lambda: json.dumps(json_contents, indent=json_indent)

# Example usage
#if __name__ == "__main__":
#    json_start()
#    add_json_str("name", "Example")
#    add_json_bool("is_active", "true")
#    add_json_list("items", "item1 item2 item3")
#    add_json_csv("numbers", "1,2,3,4")
#    add_json_map("address")
#    add_json_str("city", "San Francisco")
#    add_json_str("state", "CA")
#    end_json_map()
#    print(json_end())
# TODO: Add this to the build_tests.py script for testing the JSON output.