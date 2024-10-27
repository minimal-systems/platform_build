# Copyright (C) 2024 The Minimal Systems Project
# SPDX-License-Identifier: GPL-2.0-or-later
# strings_build.py - String Functions for the build system.

import string
import re
import os
import sys
import inspect
from common.core_build import pretty_message

###########################################################
## Convert to lower case without requiring a shell.
##
## string: string to be converted
###########################################################
def to_lower(s):
    return s.lower()

###########################################################
## Convert to upper case without requiring a shell.
##
## string: string to be converted
###########################################################
def to_upper(s):
    return s.upper()

# Test to_lower and to_upper
lower = "abcdefghijklmnopqrstuvwxyz-_"
upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
if lower != to_lower(upper):
    pretty_message("to-lower sanity check failure", level="error")
if upper != to_upper(lower):
    pretty_message("to-upper sanity check failure", level="error")

lower = ""
upper = ""

###########################################################
## Returns true if two strings are equal. Returns
## an empty string if they are not equal.
###########################################################
def streq(str1, str2):
    if str1 is None or str2 is None:
        return ""
    return "true" if str1 == str2 else ""

###########################################################
## Convert "a b c" into "a:b:c"
###########################################################
def normalize_path_list(s):
    return ":".join(s.strip().split())

###########################################################
## Convert "a b c" into "a,b,c"
###########################################################
def normalize_comma_list(s):
    return ",".join(s.strip().split())

###########################################################
## Read the word out of a colon-separated list of words.
## This has the same behavior as the built-in function
## word(n, str).
##
## The individual words may not contain spaces.
##
## n: 1-based index
## s: value of the form a:b:c...
###########################################################
def word_colon(n, s):
    words = s.split(":")
    return words[n - 1] if 0 < n <= len(words) else ""

###########################################################
## Read a colon-separated sublist out of a colon-separated
## list of words.
## Similar to the built-in function wordlist(s, e, str),
## but with colon-separated lists.
##
## n_start: 1-based index start
## n_end: 1-based index end (can be 0)
## s: value of the form a:b:c...
###########################################################
def wordlist_colon(n_start, n_end, s):
    words = s.split(":")
    return ":".join(words[n_start - 1:n_end]) if n_end else ":".join(words[n_start - 1:])

###########################################################
## Convert "a=b c= d e = f = g h=" into "a=b c=d e=f g=h="
##
## lst: list to collapse
## sep: separator word (defaults to "=" if not set)
###########################################################
def collapse_pairs(lst, sep="="):
    items = lst.split()
    result = []
    current_pair = ""

    for item in items:
        item = item.strip()

        if sep in item:
            if item.endswith(sep):  # If the item ends with '=', start a new pair
                current_pair = item
            else:  # If it's a complete pair, add it directly
                if current_pair:
                    result.append(current_pair + item)  # Complete the previous pair
                    current_pair = ""
                else:
                    result.append(item)
        else:
            if current_pair:  # Complete the current incomplete pair
                current_pair += item
                result.append(current_pair)
                current_pair = ""
            else:
                result.append(item)

    if current_pair:  # Append any remaining incomplete pair
        result.append(current_pair)

    return " ".join(result)

###########################################################
## Given a list of pairs, if multiple pairs have the same
## first components, keep only the first pair.
##
## lst: list of pairs
## sep: separator word, such as ":", "=", etc.
###########################################################
def uniq_pairs_by_first_component(lst, sep=":"):
    first_seen = set()
    result = []
    for w in lst.split():
        first_part = w.split(sep)[0]
        if first_part not in first_seen:
            first_seen.add(first_part)
            result.append(w)
    return " ".join(result)