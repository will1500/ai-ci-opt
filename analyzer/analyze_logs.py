#!/usr/bin/env python3
import sys
import os
import re
from pathlib import Path
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze pytest logs and generate a Markdown report.")
    parser.add_argument("log_dir", help="Directory containing pytest logs")
    parser.add_argument("--slow-threshold", type=float, default=0.25, help="Threshold in seconds to flag slow tests")
    parser.add_argument("--output", default="ci_analysis_report.md", help="Markdown report filename")
    return parser.parse_args()

def analyze_logs(log_dir, slow_threshold):
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "slow_tests": [],
        "flaky_tests": []
    }

    raw_output = []

    for log_file in Path(log_dir).glob("*.log"):
        with open(log_file) as f:
            for line in f:
                raw_output.append(line.rstrip())
                # Count passed/failed/skipped/errors
                if re.search(r"\.\s+\[100%\]", line):
                    summary["passed"] += line.count(".")
                    summary["total"] += line.count(".")
                if re.search(r"FAILED", line):
                    summary["failed"] += 1
                    summary["total"] += 1
                if re.search(r"ERROR", line):
                    summary["errors"] += 1
                    summary["total"] += 1
                if re.search(r"skipped", line, re.IGNORECASE):
                    summary["skipped"] += 1
                    summary["flaky_tests"].append(line.strip())

                # Capture slow tests like: test_example.py::test_func 0.45s
                slow_match = re.search(r"(\S+::\S+)\s+(\d+\.\d+)s", line)
                if slow_match:
                    test_name, duration = slow_match.groups()
                    duration = float(duration)
                    if duration >= slow_threshold:
                        summary["slow_tests"].append((test_name, duration))

    return summary, raw_output

def generate_markdown(summary, raw_output, output_file, slow_threshold):
    with open(output_file, "w") as f:
        f.write("# 📊 CI Test Analysis Report\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total Tests:** {summary['total']}\n")
        f.write(f"- ✅ Passed: {summary['passed']}\n")
        f.write(f"- ❌ Failed: {summary['failed']}\n")
        f.write(f"- ⚠️ Skipped: {summary['skipped']}\n")
        f.write(f"- 🔥 Errors: {summary['errors']}\n")
        f.write(f"- ⏱️ Duration threshold for slow tests: {slow_threshold}s\n\n")

        f.write("---\n\n## Slow tests (>{}s)\n\n".format(slow_threshold))
        if summary["slow_tests"]:
            for test_name, duration in summary["slow_tests"]:
                f.write(f"- ⏳ {test_name}: {duration:.2f}s\n")
        else:
            f.write("No slow tests detected.\n")

        f.write("\n---\n\n## Flaky tests (skipped or intermittent failures)\n\n")
        if summary["flaky_tests"]:
            for test in summary["flaky_tests"]:
                f.write(f"- ⚠️ {test}\n")
        else:
            f.write("No flaky tests detected.\n")

        f.write("\n---\n\n## Raw Pytest Output\n\n```\n")
        f.write("\n".join(raw_output))
        f.write("\n```\n")

    print(f"✅ Analysis complete: {output_file} (slow threshold = {slow_threshold}s)")

def main():
    args = parse_args()
    summary, raw_output = analyze_logs(args.log_dir, args.slow_threshold)
    generate_markdown(summary, raw_output, args.output, args.slow_threshold)

if __name__ == "__main__":
    main()
