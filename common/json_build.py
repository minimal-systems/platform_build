import json

from core import *
four_space = space * 4

# Converts a list to a JSON list
def json_list(separator, items):
    if items:
        return json.dumps(items.split(separator))
    return "[]"

# Converts a space-separated list to a JSON list
def space_separated_to_json_list(items):
    return json_list(space, items)

# Converts a comma-separated list to a JSON list
def csv_to_json_list(items):
    return json_list(comma, items)

# JSON building utilities
json_indent = four_space
json_contents = []

def increase_indent():
    global json_indent
    json_indent += four_space

def decrease_indent():
    global json_indent
    if len(json_indent) >= len(four_space):
        json_indent = json_indent[:-len(four_space)]

def add_json_val(key, value):
    global json_contents
    json_contents.append(f'{json_indent}"{key.strip()}": {value.strip()}{comma}\n')

def add_json_str(key, value):
    add_json_val(key, json.dumps(value.strip()))

def add_json_list(key, value):
    add_json_val(key, space_separated_to_json_list(value.strip()))

def add_json_csv(key, value):
    add_json_val(key, csv_to_json_list(value.strip()))

def add_json_bool(key, value):
    add_json_val(key, "true" if value.strip() else "false")

def add_json_map(key):
    global json_contents
    json_contents.append(f'{json_indent}"{key.strip()}": {{\n')
    increase_indent()

def add_json_map_anon():
    global json_contents
    json_contents.append(f'{json_indent}{{\n')
    increase_indent()

def end_json_map():
    decrease_indent()
    global json_contents
    if json_contents and json_contents[-1].strip().endswith(comma):
        json_contents[-1] = json_contents[-1].strip()[:-1] + '\n'
    json_contents.append(f'{json_indent}}},\n')

def add_json_array(key):
    global json_contents
    json_contents.append(f'{json_indent}"{key.strip()}": [\n')
    increase_indent()

def end_json_array():
    decrease_indent()
    global json_contents
    if json_contents and json_contents[-1].strip().endswith(comma):
        json_contents[-1] = json_contents[-1].strip()[:-1] + '\n'
    json_contents.append(f'{json_indent}],\n')

def json_start():
    global json_contents, json_indent
    json_contents = ["{\n"]
    json_indent = four_space

def json_end():
    global json_contents
    if json_contents and json_contents[-1].strip().endswith(comma):
        json_contents[-1] = json_contents[-1].strip()[:-1] + '\n'
    json_contents.append("}\n")

def get_json_contents():
    return "".join(json_contents)

def build_test():
    # Example usage
    json_start()
    add_json_str("name", "example")
    add_json_bool("active", "true")
    add_json_list("items", "item1 item2 item3")
    add_json_csv("csv_items", "item1,item2,item3")
    add_json_map("nested")
    add_json_str("key", "value")
    end_json_map()
    json_end()
    print(get_json_contents())

if __name__ == "__main__":
    build_test()