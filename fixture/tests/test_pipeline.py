import pytest
from pkg.pipeline import parse_stage, validate_stage, transform_stage, run_pipeline

def test_parse_splits_on_commas_not_whitespace():
    assert parse_stage("New York, USA, Old Town") == ["New York", "USA", "Old Town"]

def test_validate_raises_on_empty_field():
    with pytest.raises(ValueError):
        validate_stage(["ok", "", "also ok"])
    assert validate_stage(["ok", "also ok"]) == ["ok", "also ok"]

def test_transform_preserves_abbreviations():
    assert transform_stage(["New York", "USA"]) == ["New York", "USA"]

def test_full_pipeline_end_to_end():
    assert run_pipeline("New York, USA, Old Town") == ["New York", "USA", "Old Town"]
