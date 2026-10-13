"""Conservative, rule-based interpretation of Q fever IFA IgG titers.

This module reports serologic patterns; it does not diagnose infection or
recommend treatment. Reference: CDC clinical laboratory diagnosis of Q fever.
https://www.cdc.gov/q-fever/hcp/diagnosis-testing/index.html
"""
import argparse
import csv
import json
import math
from pathlib import Path


class SerologyInputError(ValueError):
    """Invalid or uninterpretable IFA titer."""


def parse_titer(value, *, optional=False):
    """Return reciprocal IFA endpoint dilution, e.g. 1:256 -> 256.

    A zero denotes an explicitly reported negative value. Nonquantitative
    results such as '<1:16' are rejected rather than treated as zero.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if optional:
            return None
        raise SerologyInputError("A phase I and phase II IgG titer is required.")
    if isinstance(value, bool):
        raise SerologyInputError("Titers must be numeric endpoint dilutions.")
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("1:"):
            value = value[2:]
        if not value.isdecimal():
            raise SerologyInputError("Use a titer denominator such as 256 or 1:256; report nonquantitative results separately.")
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SerologyInputError("Titers must be numeric endpoint dilutions.") from exc
    if not math.isfinite(numeric) or not numeric.is_integer() or numeric < 0 or numeric > 16777216:
        raise SerologyInputError("Titer denominators must be finite, nonnegative whole numbers up to 16777216.")
    return int(numeric)


def interpret_serology(phase_i_igg, phase_ii_igg, prior_phase_ii_igg=None, persistent_focus=False):
    """Assess IFA IgG findings using CDC qualitative laboratory principles.

    A fourfold phase II IgG rise supports acute infection; an isolated single
    titer is not confirmatory. Phase I IgG >=1:1024 suggests evaluation for
    persistent infection, which requires a clinically identified focus.
    """
    phase_i = parse_titer(phase_i_igg)
    phase_ii = parse_titer(phase_ii_igg)
    prior = parse_titer(prior_phase_ii_igg, optional=True)
    if not isinstance(persistent_focus, bool):
        raise SerologyInputError("persistent_focus must be a boolean.")
    fourfold = prior is not None and prior > 0 and phase_ii >= 4 * prior
    high_phase_i = phase_i >= 1024
    supportive_phase_ii = phase_ii >= 128
    findings = []
    if fourfold:
        findings.append("A >=4-fold rise in phase II IgG titer is demonstrated.")
    elif prior is not None and prior == 0:
        findings.append("A prior denominator of zero cannot establish a quantitative fourfold rise; consult laboratory interpretation.")
    elif prior is not None:
        findings.append("No >=4-fold rise in phase II IgG is demonstrated.")
    if high_phase_i:
        findings.append("Phase I IgG is >=1:1024, a level that warrants evaluation for persistent infection.")
    if supportive_phase_ii:
        findings.append("A single phase II IgG titer is >=1:128, supportive but not diagnostic of acute Q fever.")
    if phase_ii > phase_i:
        findings.append("Phase II IgG exceeds phase I IgG; this pattern is not diagnostic on its own.")
    if high_phase_i and persistent_focus:
        code = "persistent_pattern_with_focus"
        label = "Persistent Q fever: serology plus reported focus"
        guidance = "A compatible persistent focus and high phase I IgG fulfill key diagnostic elements; obtain specialist confirmation of the focus and full clinical assessment."
    elif high_phase_i:
        code = "investigate_persistent_focus"
        label = "High phase I IgG: assess for persistent focus"
        guidance = "Evaluate for endocarditis, vascular infection, or another persistent focus. High phase I IgG alone does not confirm chronic Q fever."
    elif fourfold:
        code = "acute_seroconversion_pattern"
        label = "Acute Q fever seroconversion pattern"
        guidance = "A >=4-fold phase II IgG rise on paired IFA supports acute Q fever in a clinically compatible patient. Verify timing and laboratory comparability."
    elif supportive_phase_ii:
        code = "single_sample_supportive"
        label = "Single-sample supportive serology"
        guidance = "A single phase II IgG titer cannot establish acute infection; correlate clinically and obtain paired sera when indicated."
    else:
        code = "insufficient_serologic_evidence"
        label = "No definitive serologic pattern from supplied values"
        guidance = "Early negative serology does not exclude Q fever; consider PCR in the early illness window and convalescent IFA 3–6 weeks later."
    return {
        "status": code,
        "interpretation": label,
        "phase_i_igg": phase_i,
        "phase_ii_igg": phase_ii,
        "prior_phase_ii_igg": prior,
        "persistent_focus_reported": persistent_focus,
        "fourfold_phase_ii_rise": fourfold,
        "findings": findings,
        "next_step": guidance,
        "limitations": "Educational interpretation of IFA IgG titers only. Clinical context, assay-specific cutoffs, specimen timing, PCR, and anatomic evidence are required. Not a standalone diagnosis or treatment recommendation.",
        "reference": "https://www.cdc.gov/q-fever/hcp/diagnosis-testing/index.html",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Interpret Q fever phase I/II IFA IgG serology (not diagnostic).")
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("single", help="Interpret one sample or paired sera")
    single.add_argument("--phase-i-igg", required=True)
    single.add_argument("--phase-ii-igg", required=True)
    single.add_argument("--prior-phase-ii-igg")
    single.add_argument("--persistent-focus", action="store_true")
    batch = sub.add_parser("batch", help="Interpret CSV rows with serology column names")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "single":
        print(json.dumps(interpret_serology(args.phase_i_igg, args.phase_ii_igg, args.prior_phase_ii_igg, args.persistent_focus), indent=2))
        return 0
    source, destination = Path(args.input), Path(args.output)
    if source.resolve() == destination.resolve():
        parser.error("Input and output files must differ.")
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"phase_i_igg", "phase_ii_igg"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            parser.error("CSV requires phase_i_igg and phase_ii_igg columns.")
        results = []
        for line, row in enumerate(reader, start=2):
            if None in row:
                parser.error(f"CSV line {line}: more values than header columns.")
            try:
                raw_focus = (row.get("persistent_focus") or "").strip().lower()
                if raw_focus not in ("", "false", "true", "0", "1", "no", "yes"):
                    raise SerologyInputError("persistent_focus must be yes/no or true/false")
                result = interpret_serology(row["phase_i_igg"], row["phase_ii_igg"], row.get("prior_phase_ii_igg"), raw_focus in ("true", "yes", "1"))
            except SerologyInputError as exc:
                parser.error(f"CSV line {line}: {exc}")
            # Preserve metadata while preventing spreadsheet formula execution on export.
            clean_row = {key: ("'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value) for key, value in row.items()}
            results.append({**clean_row, "status": result["status"], "interpretation": result["interpretation"], "fourfold_phase_ii_rise": result["fourfold_phase_ii_rise"], "next_step": result["next_step"]})
        calculated_columns = ["status", "interpretation", "fourfold_phase_ii_rise", "next_step"]
        columns = list(reader.fieldnames) + [name for name in calculated_columns if name not in reader.fieldnames]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
    print(f"Interpreted {len(results)} rows -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
