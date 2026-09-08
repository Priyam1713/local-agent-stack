"""Merge a config overlay onto a base config."""


def apply_overlay(base, overlay):
    # BUG: shallow update blows away nested dicts instead of deep-merging
    # them, so overlay={"a": {"y": 2}} destroys base["a"]["x"].
    result = dict(base)
    result.update(overlay)
    return result
