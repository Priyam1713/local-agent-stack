"""Median of a list of numbers."""


def median(nums):
    # BUG: does not handle even-length lists (no averaging), and mutates the
    # caller's list via sort().
    nums.sort()
    n = len(nums)
    return nums[n // 2]
