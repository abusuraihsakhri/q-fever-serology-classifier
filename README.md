# Q Fever Serology Classifier

Conservative interpretation of *Coxiella burnetii* phase I and phase II IgG indirect immunofluorescence (IFA) titers. The static browser application runs entirely on the user's device. A Python interpreter supports single-case and CSV workflows; a separate FastAPI route exposes the same Python rules.

**Clinical limitation:** This is an educational laboratory interpretation aid, **not** a validated diagnostic device, an independent clinical diagnosis, or a treatment recommendation. Test timing, clinical findings, paired specimens, laboratory cutoffs, and evidence of a persistent infection focus must be assessed by a qualified clinician.

## How to use

Open `index.html` through a static HTTP server or the deployed GitHub Pages application. Enter the current phase I and phase II IgG titers (e.g. `1:64` and `1:256`), an optional earlier phase II IgG titer, and whether a compatible persistent focus has been clinically identified. The interface requires no account, API key, or server-side Python.

To run locally:

```bash
python -m http.server 8080
# Open http://localhost:8080/
```

### Interpretation rules

- **Acute seroconversion pattern:** ≥4-fold rise in phase II IgG between paired IFA specimens. Paired testing is preferably performed 3–6 weeks apart. Compatible clinical presentation still matters.
- **Single supportive sample:** phase II IgG ≥1:128 may support acute infection but cannot confirm it alone. Laboratory-specific cutoffs should be checked.
- **High phase I IgG:** ≥1:1024 requires evaluation for persistent infection. A compatible persistent focus (e.g., endocarditis or vascular infection) is an essential diagnostic component; titer alone is insufficient.
- **Early negative results:** do not exclude acute Q fever; consider PCR early in illness and follow-up testing under clinical guidance.

Only quantitative IFA IgG denominators are used. IgM is not classified on its own. A reported `<1:16` result is not automatically converted to zero. A prior titer entered as zero cannot establish a quantitative fourfold increase.

References: [CDC, Clinical and Laboratory Diagnosis (2024)](https://www.cdc.gov/q-fever/hcp/diagnosis-testing/index.html); [CDC, Diagnosis and Management of Q Fever (MMWR, 2013)](https://www.cdc.gov/mmwr/preview/mmwrhtml/rr6203a1.htm).

## Python

Python 3.10+ is required. The clinical interpreter uses only the Python standard library.

```bash
python serology_interpreter.py single --phase-i-igg 64 --phase-ii-igg 256 --prior-phase-ii-igg 64
python serology_interpreter.py single --phase-i-igg 1024 --phase-ii-igg 2048 --persistent-focus
python serology_interpreter.py batch -i sample_serology.csv -o results.csv
```

Use `phase_i_igg` and `phase_ii_igg` as required CSV headers; `prior_phase_ii_igg` and `persistent_focus` are optional. Boolean focus values: `yes/no`, `true/false`, or `1/0`. Rows are evaluated locally; invalid titers abort the export.

The installed command is `q-fever-interpret`:

```bash
python -m pip install -e .
q-fever-interpret single --phase-i-igg 64 --phase-ii-igg 256 --prior-phase-ii-igg 64
```

**Compatibility:** `q_fever_serology.py` (`calculate_metrics`, `single`, `batch`) and `cli.py`'s older audit commands remain available for existing integrations. Their arbitrary weighted scores and operational alert thresholds are *legacy demonstrations*, **not Q fever serologic criteria**. Do not use their severity labels for clinical decisions.

## Optional local API

```bash
python -m pip install -e ".[web]"
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py serve --host 127.0.0.1 --port 8000
```

`POST /api/serology/interpret` accepts JSON:

```json
{"phase_i_igg":"1:64","phase_ii_igg":"1:256","prior_phase_ii_igg":"1:64","persistent_focus":false}
```

The older operational endpoints (`/api/audit`, `/api/chat`, `/api/audit/logs`, `/health`, `/metrics`) remain for compatibility. The chat mode returns mock text; it does not run or verify clinical reasoning. The audit endpoint's metric thresholds are not medically validated. This development API has **no authentication**; bind it only to trusted interfaces, and do not place it on the public internet or submit protected health information. Docker Compose binds to localhost and requires an explicitly supplied audit key.

## Privacy, verification, and technology

- The static app uses HTML, CSS, and JavaScript modules. It has no analytics, remote fonts, API requests, browser storage, or telemetry. External CDC links open only when selected. Do not enter patient identifiers.
- The Python clinical rules are implemented separately in `serology_interpreter.py`; automated Python and JavaScript test vectors cover key serologic patterns and invalid inputs.
- The optional FastAPI/Pydantic service provides in-memory audit records and HMAC verification. Regex checks for common identifiers are **not** comprehensive de-identification or a HIPAA compliance guarantee.
- The browser UI targets current evergreen desktop and mobile browsers with JavaScript modules. The Python tools run on Python 3.10–3.12.

Run tests with:

```bash
python -m pip install -e ".[dev]"
pytest -q
node --test tests/test_browser.mjs
```

License: [MIT](LICENSE).
