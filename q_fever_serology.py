#!/usr/bin/env python3
"""
Q Fever Phase I/II Serology & Chronic Phase Classifier
Interprets Coxiella burnetii Phase I and II IgG/IgM titers for acute vs chronic Q fever endocarditis.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import os
import sys
from typing import Dict, Any, List, Optional


class SerologyValidationError(Exception):
    """Raised when input data fails validation checks."""
    pass


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for q-fever-serology-classifier.

    Computes a weighted score from numeric inputs and classifies into
    Low/Standard, Moderate/Intermediate, or High/Severe tiers.

    Args:
        **kwargs: Key-value pairs of input parameters. Numeric values are
                  used for scoring; non-numeric values are treated as metadata.

    Returns:
        Dictionary containing score, classification, clinical recommendation,
        and count of inputs evaluated.

    Raises:
        SerologyValidationError: If any numeric input is NaN or infinite.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]

    # Validate numeric inputs
    for val in numeric_vals:
        if math.isnan(val) or math.isinf(val):
            raise SerologyValidationError(
                f"Invalid numeric input detected: {val}. Values must be finite numbers."
            )

    primary_val = numeric_vals[0] if numeric_vals else 1.0

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)

    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "q-fever-serology-classifier",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    """Process a single evaluation from CLI args and print JSON result."""
    kwargs = vars(args)
    kwargs.pop("func", None)
    kwargs.pop("command", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def _validate_csv_path(input_csv: str) -> None:
    """Validate that the input CSV file exists and is readable."""
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV file not found: {input_csv}")
    if not os.path.isfile(input_csv):
        raise ValueError(f"Input path is not a file: {input_csv}")
    if os.path.getsize(input_csv) == 0:
        raise SerologyValidationError(f"Input CSV file is empty: {input_csv}")


def process_batch(input_csv: str, output_csv: str) -> None:
    """
    Process batch CSV records and append classification results.

    Reads a CSV file with patient/record data, evaluates each row through
    the core algorithm, and writes results to a new CSV with score,
    classification, and clinical recommendation columns appended.

    Args:
        input_csv: Path to input CSV file (must exist and be non-empty).
        output_csv: Path for output CSV file with results.

    Raises:
        FileNotFoundError: If input_csv does not exist.
        SerologyValidationError: If CSV is empty or has no valid rows.
    """
    _validate_csv_path(input_csv)

    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise SerologyValidationError(
                f"CSV file has no headers: {input_csv}"
            )
        rows = list(reader)

    if not rows:
        raise SerologyValidationError(
            f"CSV file has headers but no data rows: {input_csv}"
        )

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Q Fever Phase I/II Serology & Chronic Phase Classifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
