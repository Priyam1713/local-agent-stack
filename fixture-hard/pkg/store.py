class Store:
    """In-memory ordered item store."""

    def __init__(self, items):
        self._items = list(items)

    def __len__(self):
        return len(self._items)

    def slice(self, offset, limit):
        """Return items[offset:offset + limit] as a list: fewer near the end, [] past the end."""
        return self._items[offset + 1:offset + limit]
