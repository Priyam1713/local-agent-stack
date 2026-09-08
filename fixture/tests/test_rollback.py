import pytest
from pkg.rollback import apply_all

def test_rolls_back_on_failure():
    items = [1, 2, 3]

    def add_one(lst):
        lst.append(1)

    def boom(lst):
        raise ValueError("boom")

    with pytest.raises(ValueError):
        apply_all(items, [add_one, add_one, boom])

    assert items == [1, 2, 3]

def test_applies_all_on_success():
    items = []

    def add_one(lst):
        lst.append(1)

    apply_all(items, [add_one, add_one])
    assert items == [1, 1]
