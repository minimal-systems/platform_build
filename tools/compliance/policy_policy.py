# policy_policy.py

import re
from typing import Dict, Set

from condition import (
    LicenseCondition,
    UnencumberedCondition,
    PermissiveCondition,
    NoticeCondition,
    ReciprocalCondition,
    RestrictedCondition,
    WeaklyRestrictedCondition,
    ProprietaryCondition,
    ByExceptionOnlyCondition,
    RecognizedConditionNames,
)
from conditionset import LicenseConditionSet, NewLicenseConditionSet
from graph import TargetEdge, LicenseGraph

# RecognizedAnnotations identifies the set of annotations that have meaning for compliance policy.
RecognizedAnnotations: Dict[str, str] = {
    "static": "static",
    "dynamic": "dynamic",
    "toolchain": "toolchain",
}

# safePathPrefixes maps the path prefixes presumed not to contain any
# proprietary or confidential pathnames to whether to strip the prefix
# from the path when used as the library name for notices.
class SafePathPrefix:
    def __init__(self, prefix: str, strip: bool):
        self.prefix = prefix
        self.strip = strip

safePathPrefixes = [
    SafePathPrefix("external/", True),
    SafePathPrefix("art/", False),
    SafePathPrefix("build/", False),
    SafePathPrefix("cts/", False),
    SafePathPrefix("dalvik/", False),
    SafePathPrefix("developers/", False),
    SafePathPrefix("development/", False),
    SafePathPrefix("frameworks/", False),
    SafePathPrefix("packages/", True),
    SafePathPrefix("prebuilts/module_sdk/", True),
    SafePathPrefix("prebuilts/", False),
    SafePathPrefix("sdk/", False),
    SafePathPrefix("system/", False),
    SafePathPrefix("test/", False),
    SafePathPrefix("toolchain/", False),
    SafePathPrefix("tools/", False),
]

# safePrebuiltPrefixes maps the regular expression to match a prebuilt
# containing the path of a safe prefix to the safe prefix.
class SafePrebuiltPrefix:
    def __init__(self, safe_path_prefix: SafePathPrefix, regex: re.Pattern):
        self.prefix = safe_path_prefix.prefix
        self.strip = safe_path_prefix.strip
        self.regex = regex

safePrebuiltPrefixes = []

# Initialize safePrebuiltPrefixes
def init_safe_prebuilt_prefixes():
    for safe_path_prefix in safePathPrefixes:
        if not safe_path_prefix.prefix.startswith("prebuilts/"):
            regex_str = r"^prebuilts/(?:runtime/mainline/)?" + re.escape(safe_path_prefix.prefix)
            regex = re.compile(regex_str)
            safePrebuiltPrefixes.append(SafePrebuiltPrefix(safe_path_prefix, regex))

init_safe_prebuilt_prefixes()

# Regular expressions
any_lgpl = re.compile(r'^SPDX-license-identifier-LGPL.*')
versioned_gpl = re.compile(r'^SPDX-license-identifier-GPL-\d.*')
generic_gpl = re.compile(r'^SPDX-license-identifier-GPL$')
cc_by_sa = re.compile(r'^SPDX-license-identifier-CC-BY.*-SA.*')

# License condition sets
ImpliesUnencumbered = LicenseConditionSet(UnencumberedCondition)

ImpliesPermissive = LicenseConditionSet(PermissiveCondition)

ImpliesNotice = LicenseConditionSet(
    UnencumberedCondition
    | PermissiveCondition
    | NoticeCondition
    | ReciprocalCondition
    | RestrictedCondition
    | WeaklyRestrictedCondition
    | ProprietaryCondition
    | ByExceptionOnlyCondition
)

ImpliesReciprocal = LicenseConditionSet(ReciprocalCondition)

ImpliesRestricted = LicenseConditionSet(RestrictedCondition | WeaklyRestrictedCondition)

ImpliesProprietary = LicenseConditionSet(ProprietaryCondition)

ImpliesByExceptionOnly = LicenseConditionSet(ProprietaryCondition | ByExceptionOnlyCondition)

ImpliesPrivate = LicenseConditionSet(ProprietaryCondition)

ImpliesShared = LicenseConditionSet(ReciprocalCondition | RestrictedCondition | WeaklyRestrictedCondition)

def LicenseConditionSetFromNames(*names: str) -> LicenseConditionSet:
    """
    Returns a set containing the recognized `names` and
    silently ignoring or discarding the unrecognized `names`.
    """
    cs = NewLicenseConditionSet()
    for name in names:
        lc = RecognizedConditionNames.get(name)
        if lc is not None:
            cs |= LicenseConditionSet(lc)
    return cs

# The following functions set the policy for license condition propagation.

def depConditionsPropagatingToTarget(
    lg: LicenseGraph,
    e: TargetEdge,
    dep_conditions: LicenseConditionSet,
    treat_as_aggregate: bool
) -> LicenseConditionSet:
    """
    Returns the conditions which propagate up an edge from dependency to target.
    """
    result = NewLicenseConditionSet()
    if edgeIsDerivation(e):
        result |= dep_conditions & ImpliesRestricted
        return result
    if not edgeIsDynamicLink(e):
        return result

    result |= dep_conditions & LicenseConditionSet(RestrictedCondition)
    return result

def targetConditionsPropagatingToDep(
    lg: LicenseGraph,
    e: TargetEdge,
    target_conditions: LicenseConditionSet,
    treat_as_aggregate: bool,
    conditions_fn
) -> LicenseConditionSet:
    """
    Returns the conditions which propagate down an edge from target to dependency.
    """
    result = target_conditions.copy()

    # Reverse direction -- none of these apply to things depended-on, only to targets depending-on.
    result = result.Minus(
        UnencumberedCondition,
        PermissiveCondition,
        NoticeCondition,
        ReciprocalCondition,
        ProprietaryCondition,
        ByExceptionOnlyCondition
    )

    if not edgeIsDerivation(e) and not edgeIsDynamicLink(e):
        # Target is not a derivative work of dependency and is not linked to dependency
        result = result.Difference(ImpliesRestricted)
        return result
    if treat_as_aggregate:
        # If the author of a pure aggregate licenses it restricted, apply restricted to immediate dependencies.
        # Otherwise, restricted does not propagate back down to dependencies.
        if not conditions_fn(e.target).MatchesAnySet(ImpliesRestricted):
            result = result.Difference(ImpliesRestricted)
        return result
    if edgeIsDerivation(e):
        return result
    result = result.Minus(WeaklyRestrictedCondition)
    return result

def conditionsAttachingAcrossEdge(
    lg: LicenseGraph,
    e: TargetEdge,
    universe: LicenseConditionSet
) -> LicenseConditionSet:
    """
    Returns the subset of conditions in `universe` that apply across edge `e`.
    """
    result = universe.copy()
    if edgeIsDerivation(e):
        return result
    if not edgeIsDynamicLink(e):
        return NewLicenseConditionSet()

    result &= LicenseConditionSet(RestrictedCondition)
    return result

def edgeIsDynamicLink(e: TargetEdge) -> bool:
    """
    Returns true for edges representing shared libraries linked dynamically at runtime.
    """
    return e.annotations.HasAnnotation("dynamic")

def edgeIsDerivation(e: TargetEdge) -> bool:
    """
    Returns true for edges where the target is a derivative work of dependency.
    """
    is_dynamic = e.annotations.HasAnnotation("dynamic")
    is_toolchain = e.annotations.HasAnnotation("toolchain")
    return not is_dynamic and not is_toolchain

