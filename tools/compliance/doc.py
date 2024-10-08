# doc.py

"""
Package compliance provides an approved means for reading, consuming, and
analyzing license metadata graphs.

Assuming the license metadata and dependencies are fully and accurately
recorded in the build system, any discrepancy between the official policy for
open source license compliance and this code is considered a bug in the code.

### Principal Types

There are a few principal types to understand:

1. **LicenseGraph**
2. **LicenseCondition**
3. **ResolutionSet**

#### LicenseGraph
A `LicenseGraph` is an immutable graph of the targets and dependencies reachable
from a specific set of root targets. In general, the root targets will be the
artifacts in a release or distribution. While conceptually immutable, parts of
the graph may be loaded or evaluated lazily.

Conceptually, the graph itself will always be a directed acyclic graph (DAG).
One representation is a set of directed edges. Another is a set of nodes with
directed edges to their dependencies.

The edges have annotations, which can distinguish between build tools, runtime
dependencies, and dependencies like 'contains' that make a derivative work.

#### LicenseCondition
A `LicenseCondition` is an immutable tuple pairing a condition name with an
originating target. For example, per current policy, a static library licensed
under an MIT license might have a `LicenseCondition` indicating that the module
as a whole is considered under the MIT license, even if it links to other licenses.

### Summary
This module acts as documentation for the `compliance` package and provides
high-level information about the classes and their relationships. Refer to the
README.md for more information on using the `compliance` package.
"""

# No functional code is provided, as this module serves only as documentation.
