# Lab 5 - Reflection

**Note:** The repository README asks for answers to four reflection questions, but the supplied three-page lab handout does not include the wording of those questions. The following four question-and-answer topics align with its learning outcomes; replace the headings if your instructor supplies the exact questions separately.

## 1. How did Pylint, Bandit, and Flake8 help assess the program?

The tools examine different risks. Bandit highlights insecure patterns, particularly the dangerous `eval` used with a user-controlled formula and the silent exception handler. Pylint helps identify correctness and maintainability concerns such as mutable default arguments, unused imports, and poor file handling. Flake8 identifies formatting and syntax-style problems, including bare exceptions and naming-related unused symbols. Taken together, they provide more complete feedback than any one tool alone.

## 2. Which issue deserved the highest priority, and how was it fixed?

Arbitrary code execution through `eval` was the highest priority because a formula entered by a user could execute arbitrary Python statements. I replaced direct evaluation with a constrained arithmetic parser that accepts only `gpa`, `credits`, numeric constants, and basic arithmetic. Unsupported operations, unexpected names, code calls, oversized formulas, divide-by-zero cases, and nonfinite results are rejected. The program still supports safe customized formulas.

## 3. Did static analysis find every problem?

No. The starter contains a logic problem that a style or security scanner may not report: it can approve an applicant whose GPA is greater than 10 and whose income or extracurricular credits are negative. It also substitutes zero for missing income, which can distort eligibility decisions. I added input checks and regression tests to cover these scenarios. Static analysis is therefore a complement to functional testing, not a replacement.

## 4. What did this exercise teach about maintainability and verifying fixes?

Separating formula parsing, applicant validation, persistence, and the command-line interface makes it easier to understand and test each responsibility. Using explicit exceptions and UTF-8 file operations makes failures visible rather than silently ignoring them. Keeping genuine before-and-after reports gives evidence of improvement, and three focused commits make it easy to trace security, quality, and formatting changes independently. I also learned to review each tool's findings and rerun tests after refactoring so that cleaning the code does not break its intended behavior.
