#!/usr/bin/env python3
import os
import sys
import argparse
import re
from datetime import datetime

def parse_pytest_log(log_path):
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "slow_tests": [],
        "duration": 0.0,
        "raw_output": "",
    }

    if not os.path.isfile(log_path):
        print(f"Log file not found: {log_path}")
        return summary

    with open(log_path, "r") as f:
        content = f.read()
        summary["raw_output"] = content

    # Total tests and status
    total_match = re.search(r"collected (\d+) items", content)
    if total_match:
        summary["total"] = int(total_match.group(1))

    summary["passed"] = len(re.findall(r"\.\.\.", content))
    summary["failed"] = len(re.findall(r"F", content))
    summary["skipped"] = len(re.findall(r"s", content))
    summary["errors"] = len(re.findall(r"E", content))

    # Duration
    duration_match = re.search(r"in ([0-9.]+)s", content)
    if duration_match:
        summary["duration"] = float(duration_match.group(1))

    # Slow tests
    slow_matches = re.findall(r"(\d+\.\d+)s\s+(.+)", content)
    for dur, test_name in slow_matches:
        summary["slow_tests"].append({"test": test_name.strip(), "duration": float(dur)})

    return summary

def generate_markdown_report(summary, slow_threshold=0.25, output_file="ci_analysis_report.md"):
    with open(output_file, "w") as f:
        f.write("# 📊 CI Test Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total Tests:** {summary['total']}\n")
        f.write(f"- ✅ Passed: {summary['passed']}\n")
        f.write(f"- ❌ Failed: {summary['failed']}\n")
        f.write(f"- ⚠️ Skipped: {summary['skipped']}\n")
        f.write(f"- 🔥 Errors: {summary['errors']}\n")
        f.write(f"- ⏱️ Duration: {summary['duration']}s\n\n")

        # Slow tests
        f.write("---\n\n## Slow tests (>={}s)\n\n".format(slow_threshold))
        slow_tests = [t for t in summary["slow_tests"] if t["duration"] > slow_threshold]
        if slow_tests:
            for t in slow_tests:
                f.write(f"- {t['test']}: {t['duration']}s\n")
        else:
            f.write("No slow tests detected.\n")
        f.write("\n---\n\n")

        # Raw pytest output
        f.write("## Raw Pytest Output\n\n```\n")
        f.write(summary["raw_output"])
        f.write("\n```\n")

    print(f"✅ Analysis complete: {output_file} (slow threshold = {slow_threshold}s)")

def main():
    parser = argparse.ArgumentParser(description="Analyze pytest logs and generate a Markdown report")
    parser.add_argument("log_dir", help="Directory containing pytest logs")
    parser.add_argument("--slow-threshold", type=float, default=0.25, help="Threshold in seconds for slow tests")
    parser.add_argument("--output", default="ci_analysis_report.md", help="Output Markdown file")
    args = parser.parse_args()

    log_dir = args.log_dir
    pytest_log = os.path.join(log_dir, "pytest.log")
    summary = parse_pytest_log(pytest_log)
    generate_markdown_report(summary, slow_threshold=args.slow_threshold, output_file=args.output)

if __name__ == "__main__":
    main()
