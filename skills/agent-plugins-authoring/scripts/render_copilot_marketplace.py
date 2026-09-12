#!/usr/bin/env python3
"""Render or verify the GitHub Copilot repository marketplace catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import stable_json, strict_json_load


def render(root: Path) -> dict[str, Any]:
    manifest = strict_json_load(root / "plugin.json")
    if not isinstance(manifest, dict):
        raise ValueError("portable manifest must be a JSON object")
    name = manifest.get("name")
    version = manifest.get("version")
    description = manifest.get("description")
    author = manifest.get("author", {})
    if not isinstance(name, str) or not name:
        raise ValueError("portable manifest name is required")
    if not isinstance(version, str) or not version:
        raise ValueError("portable manifest version is required for marketplace distribution")
    if not isinstance(description, str) or not description:
        raise ValueError("portable manifest description is required for marketplace distribution")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str):
        raise ValueError("portable manifest author.name is required for marketplace distribution")

    entry: dict[str, Any] = {
        "name": name,
        "description": description,
        "version": version,
        "source": ".",
        "author": author,
        "strict": True,
        "category": "Productivity",
    }
    for field in ("homepage", "repository", "license", "keywords"):
        if field in manifest:
            entry[field] = manifest[field]

    return {
        "name": name,
        "owner": {"name": author["name"]},
        "metadata": {
            "description": f"GitHub Copilot marketplace for {name}",
            "version": version,
        },
        "plugins": [entry],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    target = args.output or (args.plugin_root / ".github" / "plugin" / "marketplace.json")
    try:
        catalog = stable_json(render(args.plugin_root))
        if args.check:
            actual = target.read_text(encoding="utf-8")
            report = {
                "status": "PASS" if actual == catalog else "FAIL",
                "path": str(target),
                "issues": [] if actual == catalog else ["catalog differs from deterministic rendering"],
            }
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(catalog, encoding="utf-8")
            report = {"status": "PASS", "path": str(target), "issues": []}
    except (OSError, ValueError, TypeError) as exc:
        report = {"status": "FAIL", "path": str(target), "issues": [str(exc)]}
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {report['path']}")
        for issue in report.get("issues", []):
            print(f"- {issue}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
