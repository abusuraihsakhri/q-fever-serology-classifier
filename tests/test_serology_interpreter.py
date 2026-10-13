import csv
import json
import pytest
from serology_interpreter import SerologyInputError, interpret_serology, main, parse_titer


@pytest.mark.parametrize("input_value,expected", [("1:256", 256), ("256", 256), (256, 256), ("0", 0)])
def test_parse_titer(input_value, expected):
    assert parse_titer(input_value) == expected


@pytest.mark.parametrize("value", ["<1:16", "abc", "-1", "1:2.5", "inf", float("nan"), True, ""])
def test_invalid_titer(value):
    with pytest.raises(SerologyInputError):
        parse_titer(value)


def test_fourfold_seroconversion():
    result = interpret_serology(64, 256, 64)
    assert result["status"] == "acute_seroconversion_pattern"
    assert result["fourfold_phase_ii_rise"] is True


def test_threefold_not_confirmed():
    result = interpret_serology(32, 192, 64)
    assert result["status"] == "single_sample_supportive"
    assert result["fourfold_phase_ii_rise"] is False


def test_high_phase_i_needs_focus():
    assert interpret_serology(1024, 2048)["status"] == "investigate_persistent_focus"
    assert interpret_serology(1024, 2048, persistent_focus=True)["status"] == "persistent_pattern_with_focus"


def test_phase_ii_can_exceed_phase_i_in_persistent_infection():
    assert interpret_serology(1024, 8192, persistent_focus=True)["status"] == "persistent_pattern_with_focus"


def test_single_supportive_is_not_confirmed():
    assert interpret_serology(16, 128)["status"] == "single_sample_supportive"


def test_early_negative_not_rule_out():
    assert interpret_serology(0, 0)["status"] == "insufficient_serologic_evidence"


def test_zero_prior_is_not_fourfold():
    assert interpret_serology(0, 1024, 0)["fourfold_phase_ii_rise"] is False


def test_non_boolean_focus_rejected():
    with pytest.raises(SerologyInputError):
        interpret_serology(1024, 2048, persistent_focus="false")


def test_cli_single(capsys):
    assert main(["single", "--phase-i-igg", "1:64", "--phase-ii-igg", "1:256", "--prior-phase-ii-igg", "1:64"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "acute_seroconversion_pattern"


def test_cli_batch(tmp_path):
    infile = tmp_path / "serology.csv"
    outfile = tmp_path / "sub" / "results.csv"
    infile.write_text("phase_i_igg,phase_ii_igg,prior_phase_ii_igg,persistent_focus\n1024,2048,,yes\n64,256,64,no\n", encoding="utf-8")
    assert main(["batch", "-i", str(infile), "-o", str(outfile)]) == 0
    with outfile.open(newline="") as f:
        results = list(csv.DictReader(f))
    assert [r["status"] for r in results] == ["persistent_pattern_with_focus", "acute_seroconversion_pattern"]


def test_cli_batch_rejects_partial_rows(tmp_path):
    infile = tmp_path / "serology.csv"
    infile.write_text("phase_i_igg,phase_ii_igg\n1024,\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        main(["batch", "-i", str(infile), "-o", str(tmp_path / "out.csv")])
    assert not (tmp_path / "out.csv").exists()

def test_cli_csv_formula_injection_is_escaped(tmp_path):
    infile = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    infile.write_text("phase_i_igg,phase_ii_igg,comment\n64,256,=HYPERLINK(1)\n", encoding="utf-8")
    assert main(["batch", "-i", str(infile), "-o", str(output)]) == 0
    with output.open(newline="", encoding="utf-8") as stream:
        row = next(csv.DictReader(stream))
    assert row["comment"].startswith("'=")


def test_cli_csv_duplicate_computed_field_is_overwritten_once(tmp_path):
    infile = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    infile.write_text("phase_i_igg,phase_ii_igg,status\n64,256,stale\n", encoding="utf-8")
    assert main(["batch", "-i", str(infile), "-o", str(output)]) == 0
    with output.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames.count("status") == 1
        assert next(reader)["status"] == "single_sample_supportive"


def test_cli_csv_extra_columns_are_rejected(tmp_path):
    infile = tmp_path / "input.csv"
    outfile = tmp_path / "output.csv"
    infile.write_text("phase_i_igg,phase_ii_igg\n64,256,extra\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        main(["batch", "-i", str(infile), "-o", str(outfile)])
    assert not outfile.exists()
