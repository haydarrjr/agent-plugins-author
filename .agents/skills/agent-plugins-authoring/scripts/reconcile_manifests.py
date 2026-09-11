#!/usr/bin/env python3
"""Reconcile the portable manifest with the Codex-native adapter.

This remains a compatibility entry point. Cross-surface reconciliation lives
in ``reconcile_surfaces.py``; this helper is intentionally limited to the
portable/native manifest boundary.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import PORTABLE_SCHEMA, make_issue, stable_json, strict_json_load


def creator_validator_path(explicit: Path | None = None) -> Path | None:
    """Resolve the optional host validator without machine-specific paths."""

    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    configured = os.environ.get("CODEX_PLUGIN_VALIDATOR")
    if configured:
        candidates.append(Path(configured))
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py")
    candidates.append(Path.home() / ".codex" / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py")
    codex = shutil.which("codex")
    if codex:
        executable = Path(codex).resolve()
        candidates.append(executable.parent.parent / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _status(issues: list[dict[str, str]], creator_status: str, run_native_validator: bool) -> str:
    if issues:
        return "FAIL"
    if run_native_validator and creator_status == "UNVERIFIED":
        return "UNVERIFIED"
    return "PASS"


def reconcile(
    root: Path,
    run_native_validator: bool = True,
    validator: Path | None = None,
) -> dict[str, Any]:
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
        if any(field in portable for field in ("skills", "mcpServers", "apps")):
            issues.append(make_issue("PORTABLE_NATIVE_MIX", "portable manifest contains native fields", "plugin.json"))

    creator_status = "NOT_RUN"
    if run_native_validator:
        selected = creator_validator_path(validator)
        if selected is None:
            creator_status = "UNVERIFIED"
        else:
            result = subprocess.run(
                [sys.executable, str(selected), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            creator_status = "PASS" if result.returncode == 0 else "FAIL"
            if result.returncode != 0:
                detail = (result.stdout + result.stderr).strip().replace("\n", " ")
                issues.append(make_issue("CREATOR_VALIDATION", detail or "plugin-creator validator failed"))

    status = _status(issues, creator_status, run_native_validator)
    adapter = {
        "status": status,
        "creator_validator": creator_status,
        "checks": {
            "identity": "PASS" if not any(item["code"] == "IDENTITY_MISMATCH" for item in issues) else "FAIL",
            "portable_native_separation": "PASS" if not any(item["code"] == "PORTABLE_NATIVE_MIX" for item in issues) else "FAIL",
            "native_manifest": "PASS" if not any(item["code"] in {"NATIVE_MANIFEST", "MANIFEST_SHAPE", "SKILLS_PATH"} for item in issues) else "FAIL",
        },
        "issues": issues,
    }
    return {
        "schema_version": "agent-plugins-author-report.v2",
        "status": status,
        "portable": {"status": "PASS" if not any(item["code"].startswith("PORTABLE") for item in issues) else "FAIL"},
        "codex_plugin_adapter": adapter,
        "codex_adapter": adapter,
        "checks": adapter["checks"],
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--creator-validator", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    parser.add_argument("--skip-native-validator", action="store_true")
    args = parser.parse_args()
    report = reconcile(
        args.plugin_root,
        run_native_validator=not args.skip_native_validator,
        validator=args.creator_validator,
    )
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
