# ---------------------------------------------------------------
# Set path variables based on config values and input conditions.

# Variables we check:
#     HOST_BUILD_TYPE = { release debug }
#     TARGET_BUILD_TYPE = { release debug }
# and we output a bunch of variables, see the case statement at
# the bottom for the full list
#     OUT_DIR is also set to "out" if it's not already set.
#         this allows you to set it to somewhere else if you like
#     SCAN_EXCLUDE_DIRS is an optional, whitespace separated list of
#         directories that will also be excluded from full checkout tree
#         searches for source or make files, in addition to OUT_DIR.
#         This can be useful if you set OUT_DIR to be a different directory
#         than other outputs of your build system.

# Returns all words in $1 up to and including $2
# Python equivalent for find_and_earlier function from Makefile
def find_and_earlier(lst, target):
    result = []
    for item in lst:
        result.append(item)
        if item == target:
            break
    return " ".join(result)

#print(find_and_earlier(['A', 'B', 'C'], 'A'))  # Output: A
#print(find_and_earlier(['A', 'B', 'C'], 'B'))  # Output: A B
#print(find_and_earlier(['A', 'B', 'C'], 'C'))  # Output: A B C
#print(find_and_earlier(['A', 'B', 'C'], 'D'))  # Output: A B C