"""Cursor pagination over a Store.

Specification for list_page(store, cursor=None, page_size=10) -> dict:
- Returns {"items": [...], "next_cursor": str | None}.
- `cursor` is None for the first page; otherwise it must be a value previously returned as
  "next_cursor". Any other cursor (not decodable, negative, non-numeric, empty string)
  raises ValueError.
- `page_size` must be an int from 1 to 100 inclusive, otherwise ValueError.
- Following next_cursor from the first page visits every item exactly once, in order.
- "next_cursor" is None exactly when there are no more items after this page, including
  when this page ends exactly on the last item. An empty store gives one page:
  {"items": [], "next_cursor": None}.
"""
import base64


def _encode(offset):
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def _decode(cursor):
    return int(base64.urlsafe_b64decode(cursor.encode()).decode())


def list_page(store, cursor=None, page_size=10):
    offset = _decode(cursor) if cursor else 0
    items = store.slice(offset, page_size)
    more = len(items) == page_size or offset < len(store)
    return {"items": items, "next_cursor": _encode(offset + page_size) if more else None}
