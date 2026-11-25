import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be > 0")
        self.rate, self.capacity, self.clock = rate, capacity, clock
        self._tokens = float(capacity)
        self._last = clock()

    def _refill(self):
        now = self.clock()
        elapsed = now - self._last
        if elapsed > 0:
            self._tokens = min(float(self.capacity), self._tokens + elapsed * self.rate)
            self._last = now

    @property
    def tokens(self):
        self._refill()
        return self._tokens

    def allow(self, cost=1):
        if cost > self.capacity:
            raise ValueError("cost exceeds capacity")
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False
