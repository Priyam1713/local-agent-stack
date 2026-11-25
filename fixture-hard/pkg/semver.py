"""Semantic versions and ranges (a subset of SemVer 2.0.0 and npm range syntax).

Versions
- Form: MAJOR.MINOR.PATCH, optionally followed by -PRERELEASE. No build metadata.
  MAJOR, MINOR and PATCH are non-negative integers without leading zeros ("01.0.0" is
  invalid). PRERELEASE is one or more dot-separated identifiers of [0-9A-Za-z-], none empty.
  Anything else ("1.0", "1.0.0.0", "1.0.0-", "1.0.0-alpha..1", "") raises ValueError.

compare(a, b) -> -1, 0 or 1, by SemVer precedence:
- Compare MAJOR, MINOR, PATCH numerically.
- If those are equal, a version WITH a prerelease is lower than the same version without.
- Two prereleases compare identifier by identifier, left to right: numeric identifiers
  compare numerically; alphanumeric ones compare lexically in ASCII order; a numeric
  identifier is lower than an alphanumeric one; if all shared identifiers are equal, the
  one with fewer identifiers is lower.
  e.g. 1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2
       < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0

satisfies(version, range) -> bool:
- A range is one or more comparator SETS separated by "||"; the version must satisfy at
  least one set. A set is one or more comparators separated by whitespace; the version must
  satisfy all of them.
- Comparators (no space between operator and version):
    1.2.3 or =1.2.3   exactly equal
    >1.2.3  >=1.2.3  <1.2.3  <=1.2.3
    ^1.2.3   := >=1.2.3 <2.0.0      (major > 0)
    ^0.2.3   := >=0.2.3 <0.3.0      (major 0, minor > 0)
    ^0.0.3   := >=0.0.3 <0.0.4      (major 0, minor 0)
    ~1.2.3   := >=1.2.3 <1.3.0
  The version inside a caret or tilde comparator may carry a prerelease (^1.2.3-beta.2).
- Prerelease rule: a version that HAS a prerelease satisfies a set only if, in addition, at
  least one comparator in that set has a prerelease on the same MAJOR.MINOR.PATCH.
  So 1.0.0-beta satisfies >=1.0.0-alpha, but 1.0.1-beta does not, and 2.0.0-alpha does not
  satisfy ^1.2.3 even though it sorts below 2.0.0.
- An invalid version or comparator anywhere raises ValueError.
"""


def parse(v):
    major, minor, patch = v.split("-")[0].split(".")
    pre = v.split("-", 1)[1] if "-" in v else ""
    return major, minor, patch, pre


def compare(a, b):
    pa, pb = parse(a), parse(b)
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def satisfies(version, range_):
    raise NotImplementedError("TASK: implement per the module docstring")
