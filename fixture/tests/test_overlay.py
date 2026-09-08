from pkg.overlay import apply_overlay

def test_deep_merges_nested_dicts():
    base = {"a": {"x": 1, "y": 2}, "b": 5}
    overlay = {"a": {"y": 99}}
    result = apply_overlay(base, overlay)
    assert result == {"a": {"x": 1, "y": 99}, "b": 5}
