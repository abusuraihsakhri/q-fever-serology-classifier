import math
import pytest
from q_fever_serology import calculate_metrics, process_batch, SerologyValidationError


def test_q_fever_serology_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_q_fever_serology_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


# --- Edge case tests ---

def test_calculate_metrics_no_numeric_inputs():
    """When no numeric inputs provided, should use default value of 1.0."""
    res = calculate_metrics(name="test", label="abc")
    assert res["score"] == 1.0
    assert res["classification"] == "Low / Standard"
    assert res["inputs_evaluated"] == 2


def test_calculate_metrics_empty():
    """When no inputs provided, should use default value of 1.0."""
    res = calculate_metrics()
    assert res["score"] == 1.0
    assert res["inputs_evaluated"] == 0


def test_calculate_metrics_nan_raises():
    """NaN values should raise SerologyValidationError."""
    with pytest.raises(SerologyValidationError, match="Invalid numeric input"):
        calculate_metrics(v1=float("nan"))


def test_calculate_metrics_inf_raises():
    """Infinite values should raise SerologyValidationError."""
    with pytest.raises(SerologyValidationError, match="Invalid numeric input"):
        calculate_metrics(v1=float("inf"))


def test_calculate_metrics_negative_inf_raises():
    """Negative infinite values should raise SerologyValidationError."""
    with pytest.raises(SerologyValidationError, match="Invalid numeric input"):
        calculate_metrics(v1=float("-inf"))


def test_calculate_metrics_classification_tiers():
    """Test all three classification tiers."""
    # Low / Standard: score < 10
    res_low = calculate_metrics(v1=5.0)
    assert res_low["classification"] == "Low / Standard"
    assert res_low["score"] == 5.0

    # Moderate / Intermediate: 10 <= score < 25
    res_mod = calculate_metrics(v1=15.0)
    assert res_mod["classification"] == "Moderate / Intermediate"

    # High / Severe: score >= 25
    res_high = calculate_metrics(v1=30.0)
    assert res_high["classification"] == "High / Severe"


def test_calculate_metrics_weighted_score():
    """Test that secondary values are weighted by 1/index."""
    # score = v1 + v2 * (1/2) = 10 + 4*0.5 = 12.0
    res = calculate_metrics(v1=10.0, v2=4.0)
    assert res["score"] == 12.0


def test_process_batch_missing_file(tmp_path):
    """Missing input file should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))


def test_process_batch_empty_file(tmp_path):
    """Empty CSV file should raise SerologyValidationError."""
    csv_in = tmp_path / "empty.csv"
    csv_in.write_text("", encoding="utf-8")
    with pytest.raises(SerologyValidationError, match="empty"):
        process_batch(str(csv_in), str(tmp_path / "out.csv"))


def test_process_batch_headers_only(tmp_path):
    """CSV with headers but no data rows should raise SerologyValidationError."""
    csv_in = tmp_path / "headers_only.csv"
    csv_in.write_text("Patient,v1,v2\n", encoding="utf-8")
    with pytest.raises(SerologyValidationError, match="no data rows"):
        process_batch(str(csv_in), str(tmp_path / "out.csv"))


def test_process_batch_creates_output_directory(tmp_path):
    """Output directory should be created if it doesn't exist."""
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "subdir" / "nested" / "out.csv"
    csv_in.write_text("Patient,v1\nPat_001,10.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
