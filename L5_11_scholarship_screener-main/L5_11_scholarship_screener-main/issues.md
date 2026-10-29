# Lab 5 - Identified Issues and Fixes

Source: `scholarship_system.py`, original 54-line starter program. Line numbers below refer to the **original** source before edits. The findings were initially identified through source inspection; the tool-specific `reports/before/` files must be generated on the local machine to verify their exact codes and severities.

| Issue | Type / tool | Original line(s) | Description | Fix approach |
|---|---|---:|---|---|
| Dynamic `eval()` | **Security** / Bandit B307 (expected) | 9-10, 46-49 | A user can supply a formula, which is later executed as Python code. This permits arbitrary code execution. | Replace `eval` with an AST allowlist for numeric literals, `gpa`, `credits`, and the basic arithmetic operators. Reject unauthorized syntax and nonfinite results. |
| Silent catch-all handler | **Security / reliability** / Bandit B110 and Flake8 E722 (expected) | 29-34 | Bare `except:` followed by `pass` hides file and JSON errors. | Catch expected file/JSON exceptions and raise descriptive errors instead. |
| Mutable default list | **Bug / quality** / Pylint W0102 (expected) | 11 | `logs=[]` is reused across separate calls and can leak state. | Use `logs=None`, then append only when an explicit list is provided. |
| Missing applicant validation | **Logic bug** / manual testing | 12-16, 44-45 | Invalid GPA above 10, negative credits, and negative income could be treated as valid. | Validate numeric types, finite values, GPA in 0-10, and nonnegative credits/income. |
| Missing income defaults to zero | **Logic bug** / manual testing | 14, 45 | An incomplete application is incorrectly treated as having no income. | Require both `gpa` and `income` before deciding eligibility. |
| Unsafe file handling | **Reliability / quality** / Pylint R1732 (expected) | 24-32 | Files are opened without context managers and without an explicit encoding. | Use `Path.write_text` and `Path.read_text` with UTF-8 and clear error handling. |
| Unused imports | **Quality** / Pylint W0611, Flake8 F401 (expected) | 2-3 | `math` and `sys` are unused in the original program. | Remove unused imports and import only necessary modules. The safe implementation uses `math` intentionally. |
| Inconsistent naming and Boolean comparison | **Style / quality** / Pylint C0103, Flake8 E712 (expected) | 36-40 | `printShortlist` does not use snake_case and `== True` is redundant. | Rename to `print_shortlist` and use truthy Boolean checks. |
| Unprotected script entry point | **Design / quality** / manual review | 53-54 | Importing the file executes the CLI immediately, interfering with testing. | Use `if __name__ == "__main__": main()`. |
| Formatting and blank lines | **Style** / Flake8 E30x and E501 (expected) | Throughout | Inconsistent spacing between functions, plus overly long statements. | Use standard Python indentation, two top-level blank lines, and wrap long expressions to 79 characters. |

## Priority and outcome

Security risks were addressed first, followed by code-quality/reliability fixes and Flake8 formatting. More than four distinct issues are corrected. The final version rejects applicants `U003` (out-of-range and negative values) and `U004` (missing income), while retaining eligible applicants `U001` and `U005` under the default formula.

## Verification

Run `python tools/generate_reports.py before` on the **unmodified** original repository, apply the three patches in order, then run `python tools/generate_reports.py after`. The resulting reports provide the authoritative tool findings and Pylint score. Run `python -m unittest discover -s tests -v` as a functional regression check.
