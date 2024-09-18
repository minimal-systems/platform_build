from core import space, comma, pretty_warning, pretty_error

def to_lower(s):
    return s.lower()

def to_upper(s):
    return s.upper()

def streq(s1, s2):
    return s1.strip() == s2.strip()

def normalize_path_list(s):
    return s.strip().replace(space, ":")

def normalize_comma_list(s):
    return s.strip().replace(space, comma)

def word_colon(index, s):
    words = s.split(':')
    return words[index - 1] if index - 1 < len(words) else ""

def wordlist_colon(start, end, s):
    words = s.split(':')
    end = end if end != 0 else len(words)
    return ':'.join(words[start - 1:end])

def collapse_pairs(s, sep='='):
    pairs = s.split()
    result = []
    lhs = ""
    for pair in pairs:
        if sep in pair:
            if lhs:
                result.append(lhs)
            lhs = pair
        else:
            lhs += pair
    if lhs:
        result.append(lhs)
    return space.join(result)

def uniq_pairs_by_first_component(s, sep):
    pairs = s.split()
    seen = set()
    result = []
    for pair in pairs:
        key = pair.split(sep)[0]
        if key not in seen:
            seen.add(key)
            result.append(pair)
    return space.join(result)

def strings_tests():
    # Test to_lower and to_upper
    lower = "abcdefghijklmnopqrstuvwxyz-_"
    upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ-_"

    if to_lower(upper) != lower:
        pretty_error("to-lower sanity check failure")

    if to_upper(lower) != upper:
        pretty_error("to-upper sanity check failure")

    # Test collapse_pairs
    if collapse_pairs("a=b c= d e = f = g h=") != "a=b c=d e= f=g h=":
        pretty_error("collapse-pairs sanity check failure")
    
    if collapse_pairs("a:=b c:= d e :=f g := h", ":=") != "a:=b c:=d e:=f g:=h":
        pretty_error("collapse-pairs sanity check failure")

    # Additional tests
    assert streq("abc", "abc") == True
    assert streq("abc", "def") == False
    assert normalize_path_list("a b c") == "a:b:c"
    assert normalize_comma_list("a b c") == "a,b,c"
    assert word_colon(2, "a:b:c") == "b"
    assert wordlist_colon(2, 3, "a:b:c:d") == "b:c"
    assert uniq_pairs_by_first_component("a=b a=c d=e", "=") == "a=b d=e"
    
    print("All tests passed.")