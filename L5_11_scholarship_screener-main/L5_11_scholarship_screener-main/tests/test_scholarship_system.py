"""Functional and regression tests for the scholarship screener."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scholarship_system import ScholarshipScreener, calculate_merit_score


class ScholarshipScreenerTests(unittest.TestCase):
    """Verify safe formula parsing and applicant eligibility rules."""

    def setUp(self):
        self.screener = ScholarshipScreener()

    def test_default_merit_score(self):
        self.assertEqual(calculate_merit_score(9.1, 4), 99)

    def test_custom_formula_works(self):
        self.screener.change_formula("gpa * 12 + credits")
        self.assertTrue(
            self.screener.evaluate_applicant(
                "A100", {"gpa": 8, "credits": 2, "income": 50_000}
            )
        )

    def test_rejects_code_execution_and_keeps_previous_formula(self):
        with self.assertRaises(ValueError):
            self.screener.change_formula("__import__('os').system('echo danger')")
        self.assertEqual(self.screener.formula, "gpa * 10 + credits * 2")

    def test_rejects_unsafe_arithmetic(self):
        for formula in ("gpa ** 999", "gpa / 0", "gpa + unknown", "gpa * True"):
            with self.subTest(formula=formula):
                with self.assertRaises(ValueError):
                    self.screener.change_formula(formula)

    def test_rejects_invalid_applicants(self):
        examples = [
            {"gpa": 12.5, "credits": -3, "income": -1},
            {"gpa": 6.5},
            {"gpa": True, "income": 10_000},
            {"gpa": 9, "credits": -1, "income": 10_000},
            {"gpa": 9, "income": -1},
        ]
        for example in examples:
            with self.subTest(example=example):
                with self.assertRaises(ValueError):
                    self.screener.evaluate_applicant("Invalid", example)
        self.assertNotIn("Invalid", self.screener.results)

    def test_income_boundary_and_logs(self):
        first_log = []
        self.assertFalse(
            self.screener.evaluate_applicant(
                "A", {"gpa": 10, "income": 800_000}, first_log
            )
        )
        self.assertTrue(
            self.screener.evaluate_applicant(
                "B", {"gpa": 10, "income": 799_999}
            )
        )
        self.assertEqual(len(first_log), 1)

    def test_json_round_trip(self):
        self.screener.evaluate_applicant("A", {"gpa": 9, "income": 100_000})
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "results.json"
            self.screener.persist_results(output)
            self.assertIn("A", json.loads(output.read_text(encoding="utf-8")))
            new_screen = ScholarshipScreener()
            new_screen.load_results(output)
            self.assertEqual(new_screen.results, self.screener.results)

    def test_missing_and_bad_json_give_clear_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "absent.json"
            with self.assertRaises(ValueError):
                self.screener.load_results(output)
            output.write_text("{bad json", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.screener.load_results(output)

    def test_sample_program_only_shortlists_valid_applicants(self):
        source_file = Path(__file__).resolve().parents[1] / "scholarship_system.py"
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run(
                [sys.executable, str(source_file)],
                input="\n",
                text=True,
                capture_output=True,
                cwd=folder,
                check=True,
            )
            self.assertIn("Skipped U003", result.stdout)
            self.assertIn("Skipped U004", result.stdout)
            self.assertIn("U001 score =", result.stdout)
            self.assertIn("U005 score =", result.stdout)
            stored = json.loads(
                (Path(folder) / "scholarships.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("U003", stored)
            self.assertNotIn("U004", stored)


if __name__ == "__main__":
    unittest.main()
