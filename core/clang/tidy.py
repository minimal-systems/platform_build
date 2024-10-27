import re

# Finds the second word of `first_pattern` if `second_string` starts with the first word of `first_pattern`
def find_default_local_tidy_check2(first_pattern, second_string):
    first_word, second_word = first_pattern.split()
    if second_string.startswith(first_word):
        return second_word
    return None

# Finds the second part of `first_pattern` (split by ':') if `second_string` starts with the first part of `first_pattern`
def find_default_local_tidy_check(first_pattern, second_string):
    first_part = first_pattern.split(':')[0]
    second_part = first_pattern.split(':')[1]
    return find_default_local_tidy_check2(f"{first_part} {second_part}", second_string)

# Returns the default tidy check list for the local project path `project_path`
# Match `project_path` with all patterns in `default_local_tidy_checks` and use the last most specific pattern.
def default_global_tidy_checks(project_path, default_global_tidy_checks, default_local_tidy_checks):
    last_check = None
    # Iterate through all local tidy checks and find the most specific pattern
    for pattern in default_local_tidy_checks:
        check = find_default_local_tidy_check(pattern, project_path)
        if check:
            last_check = check
    # Return the last found check, otherwise return the global tidy checks
    return last_check or default_global_tidy_checks[-1]

# Default filter contains current directory `current_directory` and optional `default_tidy_header_dirs`
def default_tidy_header_filter(current_directory, default_tidy_header_dirs=None):
    if default_tidy_header_dirs:
        return f"-header-filter=({re.escape(current_directory)}/|{re.escape(default_tidy_header_dirs)})"
    else:
        return f"-header-filter={re.escape(current_directory)}/"
