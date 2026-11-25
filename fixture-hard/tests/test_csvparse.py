import pytest

from pkg.csvparse import parse_csv


def test_simple():
    assert parse_csv("a,b,c\n1,2,3") == [["a", "b", "c"], ["1", "2", "3"]]


def test_trailing_newline():
    assert parse_csv("a,b\n1,2\n") == [["a", "b"], ["1", "2"]]


def test_crlf():
    assert parse_csv("a,b\r\n1,2\r\n") == [["a", "b"], ["1", "2"]]


def test_empty_text():
    assert parse_csv("") == []


def test_empty_fields():
    assert parse_csv("a,,b\nx,") == [["a", "", "b"], ["x", ""]]


def test_quoted_comma():
    assert parse_csv('name,note\n"Smith, J",hi') == [["name", "note"], ["Smith, J", "hi"]]


def test_escaped_quote():
    assert parse_csv('"say ""hi"""') == [['say "hi"']]


def test_newline_inside_quotes():
    assert parse_csv('a,"line1\nline2",c\nd,e,f') == [["a", "line1\nline2", "c"], ["d", "e", "f"]]


def test_crlf_inside_quotes_is_kept():
    assert parse_csv('"x\r\ny"\r\n') == [["x\r\ny"]]


def test_empty_quoted_field():
    assert parse_csv('"",a') == [["", "a"]]


def test_literal_quote_mid_field():
    assert parse_csv('5"10,x') == [['5"10', "x"]]


def test_blank_line_in_middle():
    assert parse_csv("a\n\nb") == [["a"], [""], ["b"]]


def test_unterminated_quote():
    with pytest.raises(ValueError):
        parse_csv('a,"oops\n')
