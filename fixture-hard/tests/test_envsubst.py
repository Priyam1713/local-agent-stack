import pytest

from pkg.envsubst import expand

ENV = {"HOME": "/home/u", "USER": "ann", "EMPTY": "", "DOLLAR": "$HOME"}


@pytest.mark.parametrize(
    "t,want",
    [
        ("$HOME/x", "/home/u/x"),
        ("${HOME}x", "/home/ux"),
        ("${USER}_x", "ann_x"),
        ("cost $$5", "cost $5"),
        ("$$HOME", "$HOME"),
        ("cost $5", "cost $5"),
        ("end $", "end $"),
        ("a $ b", "a $ b"),
        ("${MISSING:-dflt}", "dflt"),
        ("${EMPTY:-dflt}", "dflt"),
        ("${EMPTY-dflt}", ""),
        ("${MISSING-dflt}", "dflt"),
        ("${USER:-dflt}", "ann"),
        ("${MISSING:-}", ""),
        ("${MISSING:-$USER}", "ann"),
        ("${MISSING:-${ALSO:-deep}}", "deep"),
        ("${MISSING:-a-b}", "a-b"),
        ("${USER:-$MISSING}", "ann"),
        ("$DOLLAR", "$HOME"),
        ("no vars", "no vars"),
        ("", ""),
        ("$USER$HOME", "ann/home/u"),
    ],
)
def test_expand(t, want):
    assert expand(t, ENV) == want


@pytest.mark.parametrize("t,name", [("$MISSING", "MISSING"), ("${MISSING}", "MISSING"), ("$USER_x", "USER_x")])
def test_missing_raises_keyerror(t, name):
    with pytest.raises(KeyError) as ei:
        expand(t, ENV)
    assert ei.value.args[0] == name


@pytest.mark.parametrize("t", ["${HOME", "${}", "${1BAD}", "${HOME:?x}", "${HOME+x}", "x ${MISSING:-y"])
def test_malformed(t):
    with pytest.raises(ValueError):
        expand(t, ENV)
