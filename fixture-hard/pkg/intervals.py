"""Closed-interval utilities.

An interval is a tuple (start, end) with start <= end, covering [start, end] inclusive.

Specification:
- merge(intervals): return a new list of merged intervals, sorted by start, as tuples.
  * Overlapping intervals merge, and so do TOUCHING ones: (1, 3) and (3, 5) -> (1, 5).
  * An interval contained inside another is absorbed: (1, 10), (2, 3) -> (1, 10).
  * Input may be in any order and may be empty (-> []).
  * The input list must not be modified.
  * Raise ValueError if any interval has start > end.
- insert(intervals, new): `intervals` is already merged and sorted. Return a new merged,
  sorted list that also covers `new`. Same rules as merge(); the input is not modified, and
  ValueError is raised if `new` has start > end.
"""


def merge(intervals):
    intervals.sort()
    out = []
    for s, e in intervals:
        if out and s < out[-1][1]:
            out[-1] = (out[-1][0], e)
        else:
            out.append((s, e))
    return out


def insert(intervals, new):
    raise NotImplementedError("TASK: implement per the module docstring")
