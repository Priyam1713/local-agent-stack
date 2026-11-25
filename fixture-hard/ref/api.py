import base64
import binascii


def _encode(offset):
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def _decode(cursor):
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise ValueError(f"invalid cursor {cursor!r}") from None
    if not raw.isdigit():
        raise ValueError(f"invalid cursor {cursor!r}")
    return int(raw)


def list_page(store, cursor=None, page_size=10):
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 100:
        raise ValueError("page_size must be an int from 1 to 100")
    offset = 0 if cursor is None else _decode(cursor)
    items = store.slice(offset, page_size)
    end = offset + len(items)
    return {"items": items, "next_cursor": _encode(end) if end < len(store) else None}
