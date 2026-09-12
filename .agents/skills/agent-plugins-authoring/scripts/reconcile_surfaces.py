#!/usr/bin/env python3
"""Reconcile every checked-in Agent Plugin distribution surface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import PORTABLE_SCHEMA, SECRET_VALUE_PATTERNS, make_issue, stable_json, strict_json_load, validate_mcp_manifest
from materialize_ide_adapter import reconcile as reconcile_ide
from reconcile_manifests import reconcile as reconcile_manifests
from render_mcp_config import render as render_mcp_config
from validate_copilot_surface import validate as validate_copilot_surface


def _repository_url(manifest: dict[str, Any]) -> str | None:
    value = manifest.get("repository")
    if not isinstance(value, str) or not value.startswith("https://"):
        return None
    return value[:-4] if value.endswith(".git") else value


def marketplace_status(root: Path, manifest: dict[str, Any], native: dict[str, Any]) -> dict[str, Any]:
    """Validate the Codex repository marketplace independently of Copilot."""
    path = root / ".agents" / "plugins" / "marketplace.json"
    if not path.is_file():
        return {"status": "NOT_RUN", "surface": "codex_repo", "path": str(path), "checks": [], "issues": []}
    issues: list[dict[str, str]] = []
    try:
        catalog = strict_json_load(path)
    except (OSError, ValueError) as exc:
        return {"status": "FAIL", "surface": "codex_repo", "path": str(path), "checks": [], "issues": [make_issue("MARKETPLACE_JSON", str(exc), str(path))]}
    name = manifest.get("name")
    entries = catalog.get("plugins", []) if isinstance(catalog, dict) else []
    matching = [entry for entry in entries if isinstance(entry, dict) and entry.get("name") == name]
    mode = None
    if len(matching) != 1:
        issues.append(make_issue("MARKETPLACE_ENTRY", "expected exactly one entry for the portable plugin", str(path)))
    else:
        entry = matching[0]
        source = entry.get("source", {})
        expected_url = (_repository_url(manifest) or "") + ".git"
        if source.get("source") != "url" or source.get("url") != expected_url:
            issues.append(make_issue("MARKETPLACE_IDENTITY", "Codex marketplace URL must match portable repository identity", str(path)))
        ref = source.get("ref")
        if not isinstance(ref, str) or not ref:
            issues.append(make_issue("MARKETPLACE_REF", "Codex marketplace source requires a ref", str(path)))
        mode = "development" if source.get("ref") == "main" else "release"
        expected_policy = {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
        if entry.get("policy") != expected_policy:
            issues.append(make_issue("MARKETPLACE_POLICY", "Codex marketplace policy must keep installation and authentication explicit", str(path)))
        expected_category = native.get("interface", {}).get("category", "Productivity")
        if entry.get("category") != expected_category:
            issues.append(make_issue("MARKETPLACE_CATEGORY", "Codex marketplace category must match the native adapter", str(path)))
    return {
        "status": "PASS" if not issues else "FAIL",
        "surface": "codex_repo",
        "path": str(path),
        "mode": mode if matching else None,
        "ref": matching[0].get("source", {}).get("ref") if matching else None,
        "checks": {
            "identity": "PASS" if not any(item["code"] == "MARKETPLACE_IDENTITY" for item in issues) else "FAIL",
            "policy": "PASS" if not any(item["code"] == "MARKETPLACE_POLICY" for item in issues) else "FAIL",
        },
        "issues": issues,
    }


def mcp_host_status(root: Path) -> dict[str, Any]:
    mcp_path = root / "mcp.json"
    if not mcp_path.is_file():
        return {"status": "NOT_RUN", "applicable": False, "checks": ["no portable mcp.json"], "issues": []}
    try:
        structural = validate_mcp_manifest(mcp_path, root)
        if structural:
            return {"status": "FAIL", "applicable": True, "checks": [], "issues": structural}
        rendered, render_report = render_mcp_config(root)
        output = root / ".codex" / "config.toml.example"
        issues = list(render_report.get("issues", []))
        if render_report.get("status") == "PASS":
            if not output.is_file():
                issues.append(make_issue("MCP_HOST_CONFIG_MISSING", "portable mcp.json requires generated .codex/config.toml.example", str(output)))
            elif output.read_text(encoding="utf-8") != rendered:
                issues.append(make_issue("MCP_HOST_CONFIG_STALE", "Codex host config example differs from mcp.json", str(output)))
            for pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(rendered):
                    issues.append(make_issue("MCP_HOST_CONFIG_SECRET", "generated Codex config contains a secret-like value", str(output)))
                    break
        return {
            "status": "PASS" if not issues else "FAIL",
            "applicable": True,
            "checks": {"portable_mcp": "PASS", "credential_free": "PASS" if not issues else "FAIL"},
            "issues": issues,
        }
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "applicable": True, "checks": [], "issues": [make_issue("MCP_HOST_CONFIG", str(exc))]}


def adapter_lock_status(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    path = root / "provenance" / "adapter-lock.json"
    if not path.is_file():
        return {"status": "NOT_RUN", "path": str(path), "checks": [], "issues": []}
    issues: list[dict[str, str]] = []
    try:
        lock = strict_json_load(path)
    except (OSError, ValueError) as exc:
        return {"status": "FAIL", "path": str(path), "checks": [], "issues": [make_issue("ADAPTER_LOCK_JSON", str(exc), str(path))]}
    plugin = lock.get("plugin", {}) if isinstance(lock, dict) else {}
    if plugin.get("name") != manifest.get("name") or plugin.get("version") != manifest.get("version"):
        issues.append(make_issue("ADAPTER_LOCK_IDENTITY", "adapter lock plugin identity differs from portable manifest", str(path)))
    surfaces = lock.get("surfaces", {}) if isinstance(lock, dict) else {}
    if surfaces.get("portable", {}).get("skills") != "skills/":
        issues.append(make_issue("ADAPTER_LOCK_CANONICAL", "adapter lock must name skills/ as canonical source", str(path)))
    if surfaces.get("codex_ide", {}).get("skills") != ".agents/skills/":
        issues.append(make_issue("ADAPTER_LOCK_IDE", "adapter lock must name .agents/skills/ as generated Codex IDE surface", str(path)))
    copilot = surfaces.get("github_copilot", {})
    if copilot.get("skills") != "skills/" or copilot.get("marketplace") != ".github/plugin/marketplace.json":
        issues.append(make_issue("ADAPTER_LOCK_COPILOT", "adapter lock must record canonical Copilot skills and marketplace surfaces", str(path)))
    return {
        "status": "PASS" if not issues else "FAIL",
        "path": str(path),
        "checks": {"identity": "PASS" if not any(item["code"] == "ADAPTER_LOCK_IDENTITY" for item in issues) else "FAIL"},
        "issues": issues,
    }


def reconcile_surfaces(
    root: Path,
    run_native_validator: bool = True,
    creator_validator: Path | None = None,
) -> dict[str, Any]:
    try:
        manifest = strict_json_load(root / "plugin.json")
    except (OSError, ValueError):
        manifest = {}
    try:
        native = strict_json_load(root / ".codex-plugin" / "plugin.json")
    except (OSError, ValueError):
        native = {}
    manifest_report = reconcile_manifests(root, run_native_validator, creator_validator)
    ide_report = reconcile_ide(root)
    codex_marketplace = marketplace_status(root, manifest, native)
    copilot = validate_copilot_surface(root, require_marketplace=True)
    mcp = mcp_host_status(root)
    lock = adapter_lock_status(root, manifest)
    surface_reports = [manifest_report, ide_report, codex_marketplace, copilot, mcp, lock]
    issues: list[dict[str, str]] = []
    for report in surface_reports:
        issues.extend(report.get("issues", []))
    if any(report.get("status") == "FAIL" for report in surface_reports):
        status = "FAIL"
    elif any(report.get("status") == "UNVERIFIED" for report in surface_reports):
        status = "UNVERIFIED"
    else:
        status = "PASS"
    return {
        "schema_version": "agent-plugins-author-report.v2",
        "status": status,
        "portable": manifest_report.get("portable", {"status": "UNVERIFIED"}),
        "codex_plugin_adapter": manifest_report.get("codex_plugin_adapter", {"status": "UNVERIFIED"}),
        "codex_ide_adapter": ide_report,
        "github_copilot": copilot,
        "marketplace": codex_marketplace,
        "mcp_host_config": mcp,
        "provenance": {"adapter_lock": lock},
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--creator-validator", type=Path)
    parser.add_argument("--skip-native-validator", action="store_true")
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    report = reconcile_surfaces(
        args.plugin_root,
        run_native_validator=not args.skip_native_validator,
        creator_validator=args.creator_validator,
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
