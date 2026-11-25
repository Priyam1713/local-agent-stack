import warnings


def normalize(s):
    """Collapse runs of whitespace to single spaces, strip both ends, and lowercase."""
    return " ".join(s.split()).lower()


def normalise(s):
    warnings.warn("normalise is deprecated; use normalize", DeprecationWarning, stacklevel=2)
    return normalize(s)
