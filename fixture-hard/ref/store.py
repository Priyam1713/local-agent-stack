class Store:
    def __init__(self, items):
        self._items = list(items)

    def __len__(self):
        return len(self._items)

    def slice(self, offset, limit):
        return self._items[offset:offset + limit]
