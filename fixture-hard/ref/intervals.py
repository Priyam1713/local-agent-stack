def _check(intervals):
    for s, e in intervals:
        if s > e:
            raise ValueError(f"invalid interval {(s, e)}")


def merge(intervals):
    _check(intervals)
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def insert(intervals, new):
    return merge(list(intervals) + [tuple(new)])
