import base64

import pytest

from pkg.api import list_page
from pkg.store import Store


def _walk(n, size):
    s = Store(range(n))
    got, cur, pages = [], None, 0
    while True:
        p = list_page(s, cur, size)
        got += p["items"]
        pages += 1
        cur = p["next_cursor"]
        if cur is None:
            return got, pages
        assert pages < 1000, "pagination never terminated"


@pytest.mark.parametrize("n", [0, 1, 5, 10, 11, 25])
@pytest.mark.parametrize("size", [1, 3, 5, 10, 12])
def test_walk_visits_everything_once(n, size):
    got, pages = _walk(n, size)
    assert got == list(range(n))
    assert pages == max(1, -(-n // size))


def test_exactly_full_last_page_has_no_next():
    s = Store(range(10))
    p1 = list_page(s, None, 5)
    p2 = list_page(s, p1["next_cursor"], 5)
    assert p1["items"] == [0, 1, 2, 3, 4]
    assert p2["items"] == [5, 6, 7, 8, 9] and p2["next_cursor"] is None


def test_empty_store():
    assert list_page(Store([])) == {"items": [], "next_cursor": None}


def test_default_page_size():
    p = list_page(Store(range(30)))
    assert p["items"] == list(range(10)) and p["next_cursor"] is not None


def test_store_slice():
    s = Store("abcdef")
    assert s.slice(0, 2) == ["a", "b"]
    assert s.slice(4, 10) == ["e", "f"]
    assert s.slice(9, 3) == []


@pytest.mark.parametrize(
    "bad",
    ["!!!", "", base64.urlsafe_b64encode(b"-1").decode(), base64.urlsafe_b64encode(b"abc").decode()],
)
def test_bad_cursor(bad):
    with pytest.raises(ValueError):
        list_page(Store(range(5)), bad, 2)


@pytest.mark.parametrize("size", [0, 101, -5])
def test_bad_page_size(size):
    with pytest.raises(ValueError):
        list_page(Store(range(5)), None, size)


def test_page_size_bounds_accepted():
    assert len(list_page(Store(range(200)), None, 100)["items"]) == 100
    assert len(list_page(Store(range(3)), None, 1)["items"]) == 1
