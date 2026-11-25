import pytest

from pkg.toposort import CycleError, order


def test_simple():
    assert order({"app": ["lib", "log"], "lib": ["log"]}) == ["log", "lib", "app"]


def test_leaf_only_nodes_included():
    assert order({"a": ["b"]}) == ["b", "a"]


def test_lexicographic_ties():
    assert order({"c": [], "a": [], "b": []}) == ["a", "b", "c"]


def test_ties_after_resolution():
    # base first; then y and z are ready (y < z); placing y readies m, and m < z.
    assert order({"z": ["base"], "y": ["base"], "m": ["y"], "base": []}) == ["base", "y", "m", "z"]


def test_ready_set_is_global():
    # After "a" is placed both "b" and "x" are ready; "b" < "x".
    assert order({"x": [], "b": ["a"], "a": []}) == ["a", "b", "x"]


def test_empty():
    assert order({}) == []


def test_accepts_sets():
    assert order({"b": {"a"}}) == ["a", "b"]


def test_not_mutated():
    deps = {"a": ["b"]}
    order(deps)
    assert deps == {"a": ["b"]}


def _assert_cycle(deps, cyc):
    assert len(cyc) >= 2 and cyc[0] == cyc[-1]
    for x, y in zip(cyc, cyc[1:]):
        assert y in deps.get(x, ())


def test_cycle():
    deps = {"a": ["b"], "b": ["c"], "c": ["a"], "d": []}
    with pytest.raises(CycleError) as ei:
        order(deps)
    _assert_cycle(deps, ei.value.cycle)
    assert set(ei.value.cycle) == {"a", "b", "c"}


def test_self_cycle():
    with pytest.raises(CycleError) as ei:
        order({"a": ["a"]})
    assert ei.value.cycle == ["a", "a"]


def test_cycle_is_value_error():
    with pytest.raises(ValueError):
        order({"x": ["y"], "y": ["x"]})


def test_cycle_behind_valid_nodes():
    deps = {"app": ["core"], "core": ["util"], "util": ["core"], "x": []}
    with pytest.raises(CycleError) as ei:
        order(deps)
    _assert_cycle(deps, ei.value.cycle)
    assert set(ei.value.cycle) == {"core", "util"}
