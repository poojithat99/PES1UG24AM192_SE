"""Capture genuine tool reports before or after applying the lab fixes.

Run from the root of the forked repository after installing pylint, bandit,
and flake8. The program intentionally does not fabricate a clean report.
"""

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

TOOL_COMMANDS = {
    "pylint": [sys.executable, "-m", "pylint", "scholarship_system.py"],
    "bandit": [sys.executable, "-m", "bandit", "-r", "scholarship_system.py"],
    "flake8": [sys.executable, "-m", "flake8", "scholarship_system.py"],
}


def capture(command, destination):
    """Run a tool, write its combined output and return its exit code."""
    process = subprocess.run(
        command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, encoding="utf-8", errors="replace",
    )
    output = process.stdout
    if process.stderr:
        output += ("\n" if output and not output.endswith("\n") else "")
        output += process.stderr
    destination.write_text(output, encoding="utf-8")
    return process.returncode, output


def main():
    """Generate tool reports and a comparison summary when both exist."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("before", "after"))
    args = parser.parse_args()
    if not Path("scholarship_system.py").is_file():
        parser.error("Run from the repository root (missing scholarship_system.py)")
    missing = [tool for tool in TOOL_COMMANDS if importlib.util.find_spec(tool) is None]
    if missing:
        parser.error(f"Install missing tools first: {', '.join(missing)}")

    destination = Path("reports") / args.phase
    destination.mkdir(parents=True, exist_ok=True)
    print(f"Generating real {args.phase} reports in {destination}:")
    status = {}
    for tool, command in TOOL_COMMANDS.items():
        exit_code, output = capture(command, destination / f"{tool}_report.txt")
        status[tool] = exit_code
        print(f"  {tool}: exit {exit_code}, {len(output.splitlines())} output lines")

    if args.phase == "after":
        version_lines = []
        for tool in TOOL_COMMANDS:
            _, output = capture(
                [sys.executable, "-m", tool, "--version"],
                destination / f"{tool}_version.txt",
            )
            version_lines.append(f"- {tool}: {output.splitlines()[0] if output else 'unknown'}")
        scores = []
        for phase in ("before", "after"):
            path = Path("reports") / phase / "pylint_report.txt"
            if path.is_file():
                report = path.read_text(encoding="utf-8")
                score = re.search(r"rated at\s+([0-9.]+)/10", report)
                scores.append((phase, score.group(1) if score else "not available"))
        summary = [
            "# Static analysis run summary", "",
            "Generated from actual runs. See the full text reports for findings.", "",
            "## Pylint score", "",
        ]
        summary.extend(f"- {phase}: {score}/10" for phase, score in scores)
        summary.extend([
            "", "## Final exit codes", "",
            *[f"- {tool}: {code}" for tool, code in status.items()],
            "", "## Tool versions", "", *version_lines, "",
            "A zero Flake8 exit code means no violations were reported. Bandit's",
            "exit code and findings must both be reviewed. Pylint target: > 9.5/10.",
            "", "## Functional tests", "",
            "Run: `python -m unittest discover -s tests -v`", "",
        ])
        Path("reports/analysis_summary.md").write_text(
            "\n".join(summary), encoding="utf-8"
        )
        if status["flake8"] != 0 or status["bandit"] != 0:
            print("WARNING: review final report findings before committing.")
        after_pylint = (destination / "pylint_report.txt").read_text(encoding="utf-8")
        match = re.search(r"rated at\s+([0-9.]+)/10", after_pylint)
        if not match or float(match.group(1)) <= 9.5:
            print("WARNING: verify Pylint score is strictly above 9.5/10.")
    print("Reports created. Open each text file to inspect actual findings.")


if __name__ == "__main__":
    sys.exit(main())
