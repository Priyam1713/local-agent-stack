"""Simple memoization for expensive pure functions.

Convention used elsewhere in this codebase: a decorator named `memoize` wraps
a function and caches results by its positional arguments, so repeated calls
with the same arguments skip recomputation. Apply that same convention here.
"""

_call_count = {"n": 0}


def expensive_square(x):
    """Squares x. Deliberately tracks how many times it actually runs so
    tests can verify caching worked, rather than just checking the return
    value (which would be correct even without any caching at all)."""
    _call_count["n"] += 1
    return x * x


def reset_call_count():
    _call_count["n"] = 0


def get_call_count():
    return _call_count["n"]


# TASK: expensive_square is not memoized. Add a `memoize` decorator (following
# the docstring's convention: cache by positional args) and apply it to
# expensive_square, so calling it twice with the same argument only computes
# once.
