import re

_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def parse(v):
    m = _RE.match(v) if isinstance(v, str) else None
    if not m:
        raise ValueError(f"invalid version {v!r}")
    pre = tuple(m.group(4).split(".")) if m.group(4) else ()
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), pre


def _cmp_pre(a, b):
    if a == b:
        return 0
    if not a:
        return 1
    if not b:
        return -1
    for x, y in zip(a, b):
        if x == y:
            continue
        xd, yd = x.isdigit(), y.isdigit()
        if xd and yd:
            return -1 if int(x) < int(y) else 1
        if xd:
            return -1
        if yd:
            return 1
        return -1 if x < y else 1
    return -1 if len(a) < len(b) else 1


def compare(a, b):
    pa, pb = parse(a), parse(b)
    if pa[:3] != pb[:3]:
        return -1 if pa[:3] < pb[:3] else 1
    return _cmp_pre(pa[3], pb[3])


def _expand(comp):
    if comp.startswith("^"):
        v = comp[1:]
        M, m, p, _ = parse(v)
        upper = f"{M + 1}.0.0" if M else (f"0.{m + 1}.0" if m else f"0.0.{p + 1}")
        return [(">=", v), ("<", upper)]
    if comp.startswith("~"):
        v = comp[1:]
        M, m, _, _ = parse(v)
        return [(">=", v), ("<", f"{M}.{m + 1}.0")]
    for op in (">=", "<=", ">", "<", "="):
        if comp.startswith(op):
            parse(comp[len(op):])
            return [(op, comp[len(op):])]
    parse(comp)
    return [("=", comp)]


_OPS = {
    "=": lambda c: c == 0,
    ">": lambda c: c > 0,
    ">=": lambda c: c >= 0,
    "<": lambda c: c < 0,
    "<=": lambda c: c <= 0,
}


def satisfies(version, range_):
    pv = parse(version)
    sets = []
    for alt in range_.split("||"):
        comps = alt.split()
        if not comps:
            raise ValueError("empty comparator set")
        sets.append([x for c in comps for x in _expand(c)])
    for expanded in sets:
        if not all(_OPS[op](compare(version, v)) for op, v in expanded):
            continue
        if pv[3] and not any(parse(v)[3] and parse(v)[:3] == pv[:3] for _, v in expanded):
            continue
        return True
    return False
