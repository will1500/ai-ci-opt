#!/usr/bin/env python3
"""
analyze_logs.py
- Parses pytest.log for total counts, duration, and per-test durations
- Detects slow tests above threshold (default 0.5s)
- Produces ci_analysis_report.md with summary, slow-tests, and raw output
Usage:
  python analyzer/analyze_logs.py <log_folder> [--slow-threshold=SECONDS]

Example:
  python analyzer/analyze_logs.py downloads/ci-logs --slow-threshold=0.25
"""

import sys
import os
import re
import argparse
from pathlib import Path

def parse_pytest_log(log_path):
    content = Path(log_path).read_text(errors="ignore")

    # overall counts and duration (e.g. "3 passed in 0.01s" or "1 failed, 2 passed, 1 skipped in 2.33s")
    summary_match = re.search(r"=*\s*([0-9,\s\w]+) in ([0-9.]+)s\s*=*", content)
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "total": 0,
        "duration": None,
        "raw_output": content,
        "per_test": {}   # mapping test_name -> duration (seconds)
    }

    if summary_match:
        raw_counts = summary_match.group(1)
        duration_str = summary_match.group(2)
        results["duration"] = float(duration_str)
        # extract numbers
        # e.g. "1 failed, 2 passed, 1 skipped"
        for m in re.finditer(r"(\d+)\s+passed", raw_counts):
            results["passed"] = int(m.group(1))
        for m in re.finditer(r"(\d+)\s+failed", raw_counts):
            results["failed"] = int(m.group(1))
        for m in re.finditer(r"(\d+)\s+skipped", raw_counts):
            results["skipped"] = int(m.group(1))
        for m in re.finditer(r"(\d+)\s+error", raw_counts):
            results["errors"] = int(m.group(1))
        results["total"] = results["passed"] + results["failed"] + results["skipped"] + results["errors"]

    # Parse per-test durations from pytest --durations output.
    # Pytest --durations=0 prints lines like:
    # "0.12s call test_sample.py::test_add"
    # or (depending on pytest version) "0.12s setup    test_sample.py::test_add"
    # We'll match "<seconds>s <phase> <whitespace> <testpath>::<testname>"
    per_test_pattern = re.compile(r"^\s*([0-9]+\.[0-9]+)s\s+\w+\s+(.+::.+)$", re.MULTILINE)
    for m in per_test_pattern.finditer(content):
        try:
            sec = float(m.group(1))
            test_id = m.group(2).strip()
            # Normalize test name to last part after ::
            # Keep full id for clarity
            results["per_test"][test_id] = sec
        except Exception:
            continue

    # Some pytest versions print durations like: "test_sample.py::test_add 0.12s"
    alt_pattern = re.compile(r"^(.+::.+)\s+([0-9]+\.[0-9]+)s$", re.MULTILINE)
    for m in alt_pattern.finditer(content):
        test_id = m.group(1).strip()
        sec = float(m.group(2))
        results["per_test"][test_id] = sec

    return results

def generate_markdown_report(results, slow_threshold=0.5):
    md = []
    md.append("# 📊 CI Test Analysis Report\n")
    md.append("## Summary\n")
    md.append(f"- **Total Tests:** {results.get('total', 0)}")
    md.append(f"- ✅ Passed: {results.get('passed', 0)}")
    md.append(f"- ❌ Failed: {results.get('failed', 0)}")
    md.append(f"- ⚠️ Skipped: {results.get('skipped', 0)}")
    md.append(f"- 🔥 Errors: {results.get('errors', 0)}")
    if results.get("duration") is not None:
        md.append(f"- ⏱️ Duration: {results['duration']}s")
    md.append("\n---\n")

    # Slow tests
    md.append(f"## Slow tests (>{slow_threshold}s)\n")
    slow = [(tid, sec) for tid, sec in results["per_test"].items() if sec > slow_threshold]
    if slow:
        slow_sorted = sorted(slow, key=lambda x: x[1], reverse=True)
        for tid, sec in slow_sorted:
            md.append(f"- 🔻 {tid} — **{sec:.3f}s**")
    else:
        md.append("No slow tests detected.\n")

    md.append("\n---\n")
    # Per-test durations table if available
    if results["per_test"]:
        md.append("## Per-test durations\n")
        md.append("| Test | Duration (s) |")
        md.append("|---:|---:|")
        for tid, sec in sorted(results["per_test"].items(), key=lambda x: x[1], reverse=True):
            md.append(f"| `{tid}` | {sec:.3f} |")
        md.append("\n")

    md.append("## Raw Pytest Output\n")
    md.append("```\n" + results["raw_output"] + "\n```")

    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Analyze pytest logs and detect slow tests.")
    parser.add_argument("log_folder", help="Folder containing pytest.log")
    parser.add_argument("--slow-threshold", type=float, default=0.5,
                        help="Seconds; tests slower than this are reported as slow (default: 0.5)")
    args = parser.parse_args()

    log_file = Path(args.log_folder) / "pytest.log"
    if not log_file.exists():
        print(f"Error: pytest.log not found in {args.log_folder}")
        return

    results = parse_pytest_log(str(log_file))
    report = generate_markdown_report(results, slow_threshold=args.slow_threshold)
    out_path = Path("ci_analysis_report.md")
    out_path.write_text(report)
    print(f"✅ Analysis complete: {out_path} (slow threshold = {args.slow_threshold}s)")

if __name__ == "__main__":
    main()
