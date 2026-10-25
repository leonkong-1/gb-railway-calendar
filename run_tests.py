"""Run every check and write the results to test-results/.

    python run_tests.py

Each check is a standalone script in tests/ that exits 0 on a full match, 1 on any mismatch and 3 if its source
data is not available locally. Full output goes to test-results/<check>.txt and a summary to test-results/SUMMARY.md.
"""
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "test-results")

CHECKS = [
    ("railwaycalendar", "railwaycalendar.com year tables", [sys.executable, "tests/check_railwaycalendar.py"]),
    ("orr", "ORR railway period dates", [sys.executable, "tests/check_orr.py"]),
    ("planancy", "Planancy 2026-2030 Rail Weeks Calendar", [sys.executable, "tests/check_planancy.py"]),
    ("js_parity", "JavaScript engine vs Python data files", ["node", "tests/check_js_parity.js"]),
]
STATUS = {0: "pass", 1: "FAIL", 3: "skipped (source data not available locally)"}


def node_version():
    try:
        return subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "not installed"


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, worst = [], 0
    for key, name, cmd in CHECKS:
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            code, text = r.returncode, r.stdout + r.stderr
        except OSError as e:
            code, text = 3, f"SKIPPED: could not run {cmd[0]}: {e}\n"
        with open(os.path.join(OUT, f"{key}.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        m = re.search(r"(\d+) checks, (\d+) mismatches", text)
        checks, mismatches = (m.group(1), m.group(2)) if m else ("-", "-")
        rows.append((name, checks, mismatches, STATUS.get(code, f"error (exit {code})"), key))
        if code not in (0, 3):
            worst = 1
        print(f"{name}: {checks} checks, {mismatches} mismatches, {STATUS.get(code, code)}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Test results", "",
        f"Run {now} with Python {platform.python_version()} and Node {node_version()}.", "",
        "| Check | Checks | Mismatches | Result | Full output |",
        "|---|---:|---:|---|---|",
    ]
    lines += [f"| {n} | {c} | {mm} | {s} | [{k}.txt]({k}.txt) |" for n, c, mm, s, k in rows]
    lines += ["", "Regenerate with `python run_tests.py`. See the README for what each check covers.", ""]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return worst


if __name__ == "__main__":
    sys.exit(main())
