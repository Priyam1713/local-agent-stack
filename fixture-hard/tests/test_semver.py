import pytest

from pkg.semver import compare, satisfies


@pytest.mark.parametrize(
    "a,b,want",
    [
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "2.0.0", -1),
        ("1.10.0", "1.9.0", 1),
        ("1.0.10", "1.0.9", 1),
        ("2.0.0", "1.99.99", 1),
        ("1.0.0-alpha", "1.0.0", -1),
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("1.0.0", "1.0.0-rc.1", 1),
        ("1.0.0-rc.1", "1.0.0-rc.1", 0),
    ],
)
def test_compare(a, b, want):
    assert compare(a, b) == want


@pytest.mark.parametrize("v", ["1.0", "1.0.0.0", "01.0.0", "1.0.0-", "a.b.c", "", "1.0.0-alpha..1"])
def test_invalid_version(v):
    with pytest.raises(ValueError):
        compare(v, "1.0.0")


@pytest.mark.parametrize(
    "v,r,want",
    [
        ("1.2.3", "1.2.3", True),
        ("1.2.3", "=1.2.3", True),
        ("1.2.4", "=1.2.3", False),
        ("1.2.3", ">1.2.2", True),
        ("1.2.2", ">1.2.2", False),
        ("1.2.2", "<=1.2.2", True),
        ("1.5.0", ">=1.2.0 <2.0.0", True),
        ("2.0.0", ">=1.2.0 <2.0.0", False),
        ("1.9.9", "^1.2.3", True),
        ("2.0.0", "^1.2.3", False),
        ("1.2.2", "^1.2.3", False),
        ("0.2.9", "^0.2.3", True),
        ("0.3.0", "^0.2.3", False),
        ("0.0.3", "^0.0.3", True),
        ("0.0.4", "^0.0.3", False),
        ("1.2.9", "~1.2.3", True),
        ("1.3.0", "~1.2.3", False),
        ("3.1.0", "^1.0.0 || ^3.0.0", True),
        ("2.1.0", "^1.0.0 || ^3.0.0", False),
        ("1.0.0-beta", ">=1.0.0-alpha", True),
        ("1.0.1-beta", ">=1.0.0-alpha", False),
        ("1.0.0-alpha", "<1.0.0", False),
        ("2.0.0-alpha", "^1.2.3", False),
        ("1.2.3-beta.3", "^1.2.3-beta.2", True),
        ("1.2.4-beta.3", "^1.2.3-beta.2", False),
        ("1.2.3", "^1.2.3-beta.2", True),
    ],
)
def test_satisfies(v, r, want):
    assert satisfies(v, r) is want


@pytest.mark.parametrize("r", ["^1.x", ">=1.2", "~", "1.2.3 || "])
def test_invalid_range(r):
    with pytest.raises(ValueError):
        satisfies("1.2.3", r)
