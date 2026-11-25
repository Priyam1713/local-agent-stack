"""Text helpers.

TASK: rename `normalise` to `normalize` (US spelling) across the codebase.
- `normalize` becomes the real function, defined here, with `normalize.__name__ == "normalize"`.
- Keep `normalise` as a deprecated alias: calling it emits a DeprecationWarning and then
  returns exactly what `normalize` returns.
- `pkg.textutil` must export BOTH names, and list both in its `__all__`.
- Every caller inside `pkg` must switch to `normalize`, so that normal use of the package
  emits no DeprecationWarning, and no module in `pkg` other than this one still refers to
  `normalise`.
"""


def normalise(s):
    """Collapse runs of whitespace to single spaces, strip both ends, and lowercase."""
    return " ".join(s.split()).lower()
