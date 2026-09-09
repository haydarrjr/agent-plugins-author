#!/usr/bin/env python3
"""Reconcile the portable manifest with the Codex-native adapter."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import PORTABLE_SCHEMA, make_issue, stable_json, strict_json_load, status_from_issues


def creator_validator_path() -> Path | None:
    candidates = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py")
    candidates.extend(
        [
            Path.home() / ".codex" / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py",
            Path("C:/Users/onder/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py"),
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def reconcile(root: Path, run_native_validator: bool = True) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    portable_path = root / "plugin.json"
    native_path = root / ".codex-plugin" / "plugin.json"
    try:
        portable = strict_json_load(portable_path)
    except (OSError, ValueError) as exc:
        portable = {}
        issues.append(make_issue("PORTABLE_MANIFEST", str(exc), "plugin.json"))
    try:
        native = strict_json_load(native_path)
    except (OSError, ValueError) as exc:
        native = {}
        issues.append(make_issue("NATIVE_MANIFEST", str(exc), ".codex-plugin/plugin.json"))

    if not isinstance(portable, dict) or not isinstance(native, dict):
        issues.append(make_issue("MANIFEST_SHAPE", "both manifests must be JSON objects"))
    else:
        if portable.get("$schema") != PORTABLE_SCHEMA:
            issues.append(make_issue("PORTABLE_SCHEMA", "portable manifest does not target 1.0.0", "plugin.json"))
        for field in ("name", "version", "description"):
            if portable.get(field) != native.get(field):
                issues.append(make_issue("IDENTITY_MISMATCH", f"portable/native {field} differs", field))
        if native.get("skills") != "./skills/":
            issues.append(make_issue("SKILLS_PATH", "native adapter must point to ./skills/", ".codex-plugin/plugin.json"))
        for field in ("mcpServers", "apps"):
            if field in native and not (root / (".mcp.json" if field == "mcpServers" else ".app.json")).is_file():
                issues.append(make_issue("MISSING_COMPANION", f"native {field} requires its companion file", ".codex-plugin/plugin.json"))
        if "skills" in portable or "mcpServers" in portable or "apps" in portable:
            issues.append(make_issue("PORTABLE_NATIVE_MIX", "portable manifest contains native fields", "plugin.json"))

    creator_status = "NOT_RUN"
    if run_native_validator:
        validator = creator_validator_path()
        if validator is None:
            creator_status = "UNVERIFIED"
        else:
            result = subprocess.run(
                [sys.executable, str(validator), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            creator_status = "PASS" if result.returncode == 0 else "FAIL"
            if result.returncode != 0:
                detail = (result.stdout + result.stderr).strip().replace("\n", " ")
                issues.append(make_issue("CREATOR_VALIDATION", detail or "plugin-creator validator failed"))

    status = status_from_issues(issues)
    return {
        "schema_version": "agent-plugins-author-report.v1",
        "status": status,
        "portable": {"status": "PASS" if not any(item["code"].startswith("PORTABLE") or item["code"] == "PORTABLE_SCHEMA" for item in issues) else "FAIL"},
        "codex_adapter": {"status": status, "creator_validator": creator_status},
        "checks": {
            "identity": "PASS" if not any(item["code"] == "IDENTITY_MISMATCH" for item in issues) else "FAIL",
            "portable_native_separation": "PASS" if not any(item["code"] == "PORTABLE_NATIVE_MIX" for item in issues) else "FAIL",
            "creator_validator": creator_status,
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    parser.add_argument("--skip-native-validator", action="store_true")
    args = parser.parse_args()
    report = reconcile(args.plugin_root, run_native_validator=not args.skip_native_validator)
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
