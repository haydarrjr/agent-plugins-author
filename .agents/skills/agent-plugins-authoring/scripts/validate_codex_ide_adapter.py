#!/usr/bin/env python3
"""Validate the generated Codex IDE adapter without mutating it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import stable_json
from materialize_ide_adapter import reconcile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    report = reconcile(args.plugin_root, args.output)
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {args.plugin_root}")
        for issue in report.get("issues", []):
            location = f" [{issue['path']}]" if "path" in issue else ""
            print(f"- {issue['code']}{location}: {issue['message']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
