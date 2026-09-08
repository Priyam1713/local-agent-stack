"""Apply a sequence of operations to a list, all-or-nothing."""


def apply_all(items, ops):
    # BUG: does not roll back on failure. If op 3 of 5 raises, ops 1-2 remain
    # applied instead of the list being restored to its original state.
    for op in ops:
        op(items)
    return items
