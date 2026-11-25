import inspect
import pathlib
import warnings

import pytest


def test_new_name():
    from pkg.textutil import normalize

    assert normalize("  Hello   World ") == "hello world"
    assert normalize.__name__ == "normalize"


def test_defined_in_core():
    from pkg.textutil import core

    assert core.normalize("A  B") == "a b"


def test_old_name_warns_and_matches():
    from pkg.textutil import normalise, normalize

    with pytest.warns(DeprecationWarning):
        assert normalise(" X  y") == normalize(" X  y") == "x y"


def test_new_name_does_not_warn():
    from pkg.textutil import normalize

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        normalize("a")


def test_report_emits_no_warning():
    from pkg import report

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert report.render(["  A  b", "C"]) == "- a b\n- c"


def test_exports():
    import pkg.textutil as t

    assert "normalize" in t.__all__ and "normalise" in t.__all__


def test_no_other_module_uses_old_name():
    import pkg

    root = pathlib.Path(inspect.getfile(pkg)).parent
    offenders = [
        str(p.relative_to(root))
        for p in root.rglob("*.py")
        if p.name != "core.py" and p.parent.name != "textutil" and "normalise" in p.read_text()
    ]
    assert offenders == []
