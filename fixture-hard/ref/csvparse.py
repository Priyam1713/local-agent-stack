def parse_csv(text):
    if text == "":
        return []
    rows, row, field = [], [], []
    in_quotes = quoted = False
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if in_quotes:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field.append(c)
            i += 1
            continue
        if c == '"' and not field and not quoted:
            in_quotes = quoted = True
            i += 1
            continue
        if c == ",":
            row.append("".join(field))
            field, quoted = [], False
            i += 1
            continue
        if c == "\r" and i + 1 < n and text[i + 1] == "\n":
            i += 1
            c = "\n"
        if c == "\n":
            row.append("".join(field))
            rows.append(row)
            row, field, quoted = [], [], False
            i += 1
            continue
        field.append(c)
        i += 1
    if in_quotes:
        raise ValueError("unterminated quoted field")
    if field or row or quoted:
        row.append("".join(field))
        rows.append(row)
    return rows
