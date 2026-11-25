"""Minimal CSV reader.

Specification for parse_csv(text: str) -> list[list[str]]:
- Fields are separated by commas. Records are separated by "\n" or "\r\n".
- A field that STARTS with a double quote is a quoted field. Inside it, commas, "\n" and
  "\r\n" are literal (kept exactly as written), and a doubled quote "" is one literal quote.
  The quoted field ends at the next single (undoubled) quote.
- A double quote that appears inside an unquoted field (not at its start) is literal:
  5"10,x  ->  ['5"10', 'x'].
- Empty fields are preserved: "a,,b" -> ['a', '', 'b'], and "x," -> ['x', ''].
  A quoted empty field "" is an empty string.
- A single trailing newline at the end of the text does NOT produce an extra record.
  An empty line in the middle is a record with one empty field: "a\n\nb" -> [['a'], [''], ['b']].
- Empty text returns [].
- A quoted field that is never closed raises ValueError.
"""


def parse_csv(text):
    return [line.split(",") for line in text.split("\n")]
