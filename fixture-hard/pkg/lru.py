"""LRU cache with a fixed capacity.

Specification:
- LRUCache(capacity): capacity must be an integer >= 1, otherwise raise ValueError.
- get(key): return the stored value, or None if the key is absent. A successful get marks
  the key as the most recently used.
- put(key, value): insert a new key, or update an existing one. Updating an existing key
  replaces its value, marks it most recently used, and never evicts anything.
- When inserting a NEW key while the cache already holds `capacity` keys, first evict the
  single least recently used key.
- len(cache) is the number of stored keys.
- `key in cache` reports membership and must NOT change recency.
"""


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self._data = {}
        self._order = []  # oldest first

    def get(self, key):
        if key not in self._data:
            return None
        return self._data[key]

    def put(self, key, value):
        if key in self._data:
            self._data[key] = value
            return
        if len(self._data) >= self.capacity:
            newest = self._order.pop()
            del self._data[newest]
        self._data[key] = value
        self._order.append(key)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data
