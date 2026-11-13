# Lab 7 - Fuzzing for Input Validation Bugs

Poojitha - PES1UG24AM192

## Submission

- `processor.py`: fixed application; valid output formats are preserved.
- `test_processor.py`: completed Hypothesis tests for all three functions, positive properties and deterministic regressions (34 pytest items).
- `Lab_7_Fuzz_Testing_Report.pdf`: required before/after screenshots and findings.
- `evidence/`: original execution logs and screenshots.
- `before/processor.py`: unchanged buggy starter for reproducing the failures.
- `before/test_processor.py`: same completed test suite used against the starter.

All work stays in this `Lab 7` directory. The original starter is retained only for before/after evidence; use the top-level `processor.py` for the fixed application.

## Run (PowerShell, inside Lab 7)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe processor.py
.\.venv\Scripts\python.exe -m pytest test_processor.py
```

Example valid inputs: `140:YES`, `48/2.5`, `CST_01`.
Example invalid inputs: `120:MAYBE`, `48/0`, `XYZ_01`.

To reproduce the original fuzz failures using the same suite:

```powershell
cd before
..\.venv\Scripts\python.exe -m pytest test_processor.py -k "no_crash or safe"
cd ..
```

The three selected fuzz tests are expected to fail against the original. The full fixed suite passes. `pytest.ini` excludes the intentional buggy `before` folder from default recursive discovery.

## Validation contract

- Rider specification: text up to 4096 characters, one colon, nonnegative integer height, and YES/NO (case insensitive). The existing 120 cm threshold remains. Invalid input returns an explicit error string.
- Throughput: text with one slash, finite nonnegative riders and finite strictly positive minutes. Return a finite rounded float, or `None` for invalid values (including overflowing ratios). Fractional riders remain accepted as in the starter; no new integer-only restriction is assumed.
- Restraint code: preserve the starter's first-three-character, case-insensitive lookup; return `Unknown restraint code` for unknown or invalid inputs.
- Non-string inputs and oversized text are rejected safely. EOF/Ctrl+C exits the CLI cleanly.

## Results and limits

The original three fuzz safety tests fail with minimized examples such as `None`, `''`, `b''`, and `'/'`. The manual original run also reproduces a division-by-zero crash. The fixed suite has 34 passing pytest items: six property tests configured for up to 300 examples each and 28 parameterized regression cases. Generated examples are not separate pytest items.

Evidence was executed in a Linux Python 3.12 environment on 13 November 2026, not on the student's Windows computer. These finite fuzz runs improve robustness but do not prove correctness for every possible Python object. The screenshot test commands explicitly load Hypothesis because unrelated ambient plugins were disabled in the execution terminal.
