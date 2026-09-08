"""A 3-stage text-processing pipeline. Each stage has its own independent bug.
ALL THREE must be fixed — fixing only one or two will not make the tests pass.
"""


def parse_stage(raw):
    # BUG: splits on any whitespace, so "New York" becomes two fields instead
    # of one. Should split only on commas.
    return [f.strip() for f in raw.split()]


def validate_stage(fields):
    # BUG: silently drops empty fields instead of raising, hiding malformed
    # input from the caller.
    return [f for f in fields if f]


def transform_stage(fields):
    # BUG: title-cases every field, including ones that are already all-caps
    # abbreviations (e.g. "USA" incorrectly becomes "Usa").
    return [f.title() for f in fields]


def run_pipeline(raw):
    return transform_stage(validate_stage(parse_stage(raw)))
