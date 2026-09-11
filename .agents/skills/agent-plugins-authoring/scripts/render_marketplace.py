#!/usr/bin/env python3
"""Render or verify the repository-scoped Git-backed marketplace catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import stable_json, strict_json_load


def _repository_url(manifest: dict[str, Any]) -> str:
    repository = manifest.get("repository")
    if not isinstance(repository, str) or not repository.startswith("https://"):
        raise ValueError("portable manifest repository must be an HTTPS URL")
    return repository[:-4] if repository.endswith(".git") else repository


def render(root: Path, mode: str = "development", ref: str | None = None) -> dict[str, Any]:
    manifest = strict_json_load(root / "plugin.json")
    native = strict_json_load(root / ".codex-plugin" / "plugin.json")
    if not isinstance(manifest, dict) or not isinstance(native, dict):
        raise ValueError("portable and native manifests must be JSON objects")
    name = manifest.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("portable manifest name is required")
    if mode not in {"development", "release"}:
        raise ValueError("marketplace mode must be development or release")
    selected_ref = ref or ("main" if mode == "development" else "")
    if not selected_ref:
        raise ValueError("release marketplace mode requires --ref with a tag or immutable commit")
    if mode == "release" and selected_ref == "main":
        raise ValueError("release marketplace mode must not point at moving main")
    interface = native.get("interface", {})
    display_name = interface.get("displayName", name)
    category = interface.get("category", "Productivity")
    return {
        "name": name,
        "interface": {"displayName": display_name},
        "plugins": [
            {
                "name": name,
                "source": {
                    "source": "url",
                    "url": _repository_url(manifest) + ".git",
                    "ref": selected_ref,
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": category,
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--mode", choices={"development", "release"}, default="development")
    parser.add_argument("--ref")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="verify the existing catalog without changing it")
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    try:
        catalog = stable_json(render(args.plugin_root, args.mode, args.ref))
        target = args.output or (args.plugin_root / ".agents" / "plugins" / "marketplace.json")
        if args.check:
            actual = target.read_text(encoding="utf-8")
            report = {
                "status": "PASS" if actual == catalog else "FAIL",
                "mode": args.mode,
                "ref": args.ref or ("main" if args.mode == "development" else None),
                "path": str(target),
                "issues": [] if actual == catalog else ["catalog differs from deterministic rendering"],
            }
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(catalog, encoding="utf-8")
            report = {"status": "PASS", "mode": args.mode, "ref": args.ref or ("main" if args.mode == "development" else None), "path": str(target), "issues": []}
    except (OSError, ValueError, TypeError) as exc:
        report = {"status": "FAIL", "issues": [str(exc)]}
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {report.get('path', args.plugin_root)}")
        for issue in report.get("issues", []):
            print(f"- {issue}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
