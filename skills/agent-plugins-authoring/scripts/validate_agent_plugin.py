#!/usr/bin/env python3
"""Validate a portable Agent Plugin package without mutating it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import stable_json, validate_portable


def build_report(root: Path) -> dict:
    portable, issues = validate_portable(root)
    return {
        "schema_version": "agent-plugins-author-report.v1",
        "mode": "audit",
        "status": portable["status"],
        "portable": {
            "status": portable["status"],
            "checks": portable["checks"],
            "skill_count": portable["skill_count"],
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    report = build_report(args.plugin_root)
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {args.plugin_root}")
        for issue in report["issues"]:
            location = f" [{issue['path']}]" if "path" in issue else ""
            print(f"- {issue['code']}{location}: {issue['message']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
