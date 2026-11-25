"""Token-bucket rate limiter.

Specification for TokenBucket(rate, capacity, clock=time.monotonic):
- `rate` is tokens added per second, `capacity` is the maximum number of tokens held.
  Both must be > 0, otherwise raise ValueError.
- `clock` is a zero-argument callable returning the current time in seconds (a float). The
  bucket starts FULL at the time it is created.
- Refill is continuous: elapsed seconds * rate are added, fractional tokens accumulate and
  are never lost, and the count never exceeds `capacity`.
- allow(cost=1): refill, then if at least `cost` tokens are available, remove `cost` tokens
  and return True. Otherwise return False and remove NOTHING. A `cost` greater than
  `capacity` can never succeed and raises ValueError.
- The `tokens` property returns the current (refilled) token count as a float.
"""
import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        self.rate = rate
        self.capacity = capacity
        self.clock = clock
        self._tokens = capacity
        self._last = clock()

    def _refill(self):
        now = self.clock()
        added = int((now - self._last) * self.rate)
        self._tokens += added
        self._last = now

    @property
    def tokens(self):
        self._refill()
        return self._tokens

    def allow(self, cost=1):
        self._refill()
        self._tokens -= cost
        return self._tokens >= 0
