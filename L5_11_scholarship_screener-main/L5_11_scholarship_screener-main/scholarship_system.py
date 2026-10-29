"""Validate scholarship applications and safely persist eligible applicants."""

import ast
import json
import math
import operator
from pathlib import Path

DEFAULT_FORMULA = "gpa * 10 + credits * 2"
INCOME_LIMIT = 800_000
MERIT_CUTOFF = 85

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _evaluate_node(node, variables):
    """Calculate a limited arithmetic AST without executing Python code."""
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body, variables)
    if isinstance(node, ast.BinOp):
        operation = BINARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise ValueError("Unsupported arithmetic operator")
        return operation(
            _evaluate_node(node.left, variables),
            _evaluate_node(node.right, variables),
        )
    if isinstance(node, ast.UnaryOp) and isinstance(
        node.op, (ast.UAdd, ast.USub)
    ):
        value = _evaluate_node(node.operand, variables)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.Name) and node.id in variables:
        return variables[node.id]
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        if abs(node.value) <= 1_000:
            return node.value
    raise ValueError("Only numbers, gpa, credits and +, -, *, / are allowed")


def calculate_merit_score(gpa, credits, formula=DEFAULT_FORMULA):
    """Calculate a finite merit score from a restricted arithmetic formula."""
    if len(formula) > 100:
        raise ValueError("Formula must contain at most 100 characters")
    try:
        parsed = ast.parse(formula, mode="eval")
        score = _evaluate_node(parsed, {"gpa": gpa, "credits": credits})
        if not math.isfinite(score):
            raise ValueError("Score must be finite")
    except (SyntaxError, ArithmeticError) as exc:
        raise ValueError("Formula is not valid arithmetic") from exc
    return score


def _valid_number(value, name):
    """Reject invalid numeric applicant data, including Boolean values."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


class ScholarshipScreener:
    """Evaluate applicants and manage the resulting shortlist."""

    def __init__(self, formula=DEFAULT_FORMULA):
        self.results = {}
        self.formula = DEFAULT_FORMULA
        self.change_formula(formula)

    def change_formula(self, new_formula):
        """Accept a formula only after validating its allowed expression."""
        calculate_merit_score(9.0, 2, new_formula)
        self.formula = new_formula

    def evaluate_applicant(self, student_id, applicant, logs=None):
        """Validate and screen a student; record the result when valid."""
        if not isinstance(student_id, str) or not student_id.strip():
            raise ValueError("A nonempty student ID is required")
        for field in ("gpa", "income"):
            if field not in applicant:
                raise ValueError(f"Missing required field: {field}")
        gpa = _valid_number(applicant["gpa"], "GPA")
        credits = _valid_number(applicant.get("credits", 0), "Credits")
        income = _valid_number(applicant["income"], "Income")
        if not 0 <= gpa <= 10:
            raise ValueError("GPA must be between 0 and 10")
        if credits < 0 or income < 0:
            raise ValueError("Credits and income cannot be negative")

        score = calculate_merit_score(gpa, credits, self.formula)
        eligible = score >= MERIT_CUTOFF and income < INCOME_LIMIT
        self.results[student_id] = {"score": score, "eligible": eligible}
        if logs is not None:
            logs.append(f"{student_id} scored {score}")
        return eligible

    def persist_results(self, file_path="scholarships.json"):
        """Write readable, UTF-8 encoded JSON and close the file safely."""
        output = json.dumps(self.results, indent=2)
        Path(file_path).write_text(output, encoding="utf-8")

    def load_results(self, file_path="scholarships.json"):
        """Load saved results and report missing, corrupt or invalid JSON."""
        try:
            payload = Path(file_path).read_text(encoding="utf-8")
            data = json.loads(payload)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Cannot load scholarship results: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise ValueError("Saved results must be a JSON object")
        for record in data.values():
            if not isinstance(record, dict) or not isinstance(
                record.get("eligible"), bool
            ):
                raise ValueError(
                    "Saved result has an invalid eligibility field"
                )
            if not isinstance(record.get("score"), (int, float)):
                raise ValueError("Saved result has an invalid score field")
        self.results = data

    def print_shortlist(self):
        """Display eligible applicants, preserving their original order."""
        print("Shortlisted applicants:")
        for student_id, record in self.results.items():
            if record["eligible"]:
                print(f"  {student_id} score = {record['score']}")


def main():
    """Run the scholarship screening demonstration."""
    screener = ScholarshipScreener()
    applicants = [
        ("U001", {"gpa": 9.1, "credits": 4, "income": 450_000}),
        ("U002", {"gpa": 7.2, "credits": 1, "income": 300_000}),
        ("U003", {"gpa": 12.5, "credits": -3, "income": -1}),
        ("U004", {"gpa": 6.5}),
    ]
    for student_id, applicant in applicants:
        try:
            screener.evaluate_applicant(student_id, applicant)
        except ValueError as exc:
            print(f"Skipped {student_id}: {exc}")

    requested_formula = input(
        "Merit formula (Enter to keep default): "
    ).strip()
    if requested_formula:
        try:
            screener.change_formula(requested_formula)
        except ValueError as exc:
            print(f"Keeping default formula: {exc}")

    screener.evaluate_applicant(
        "U005", {"gpa": 8.4, "credits": 3, "income": 600_000}
    )
    screener.persist_results()
    screener.load_results()
    screener.print_shortlist()


if __name__ == "__main__":
    main()
