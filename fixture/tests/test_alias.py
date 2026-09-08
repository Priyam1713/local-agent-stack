from pkg.alias import resolve

def test_known_alias():
    assert resolve("co") == "checkout"

def test_unknown_falls_back_to_original():
    assert resolve("log") == "log"
