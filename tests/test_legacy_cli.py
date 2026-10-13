from cli import _parse_bool
from q_fever_serology import calculate_metrics, process_batch, SerologyValidationError
import pytest


def test_false_string_is_false():
    assert _parse_bool("false") is False
    assert _parse_bool("TRUE") is True
    with pytest.raises(ValueError):
        _parse_bool("possibly")


def test_legacy_results_are_identified_as_nonclinical():
    assert "not a Q fever" in calculate_metrics(v1=100)["warning"]


def test_legacy_batch_does_not_overwrite_source(tmp_path):
    data = tmp_path / "legacy.csv"
    data.write_text("v1\n5\n", encoding="utf8")
    with pytest.raises(SerologyValidationError):
        process_batch(str(data), str(data))
    assert data.read_text(encoding="utf8") == "v1\n5\n"
