#!/usr/bin/env python3
"""Build a scoped Agent Plugins Author evidence report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import stable_json, strict_json_load, validate_portable
from reconcile_manifests import reconcile
from refresh_upstream import local_report, online_report


def _marketplace_entry_status(plugin_name: str, path: Path, repo_root: Path | None) -> dict:
    try:
        marketplace = strict_json_load(path)
    except (OSError, ValueError) as exc:
        return {"status": "FAIL", "checks": [str(exc)], "path": str(path)}
    entries = [item for item in marketplace.get("plugins", []) if item.get("name") == plugin_name]
    if len(entries) != 1:
        return {"status": "FAIL", "checks": ["expected exactly one marketplace entry"], "path": str(path)}
    entry = entries[0]
    source = entry.get("source", {})
    if repo_root is None:
        expected = f"./plugins/{plugin_name}"
        if source.get("source") != "local" or source.get("path") != expected:
            return {"status": "FAIL", "checks": ["marketplace source path mismatch"], "path": str(path)}
        return {"status": "PASS", "checks": ["local personal marketplace entry matches"], "path": str(path), "surface": "personal"}

    if source.get("source") == "url":
        url = source.get("url", "")
        if not isinstance(url, str) or not url.startswith("https://"):
            return {"status": "FAIL", "checks": ["repo marketplace URL source must be HTTPS"], "path": str(path)}
        return {"status": "PASS", "checks": ["Git-backed repo marketplace entry matches"], "path": str(path), "surface": "repo"}

    if source.get("source") == "git-subdir":
        url = source.get("url", "")
        subdir = source.get("path", "")
        if not isinstance(url, str) or not url.startswith("https://") or not isinstance(subdir, str) or not subdir.startswith("./"):
            return {"status": "FAIL", "checks": ["repo marketplace git-subdir entry is invalid"], "path": str(path)}
        return {"status": "PASS", "checks": ["Git-backed subdirectory marketplace entry matches"], "path": str(path), "surface": "repo"}

    if source.get("source") == "local":
        relative = source.get("path")
        if not isinstance(relative, str) or not relative.startswith("./"):
            return {"status": "FAIL", "checks": ["repo marketplace local path must start with ./"], "path": str(path)}
        candidate = (path.parent.parent.parent / relative).resolve()
        root = repo_root.resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return {"status": "FAIL", "checks": ["repo marketplace local path escapes repository root"], "path": str(path)}
        return {"status": "PASS", "checks": ["local repo marketplace entry matches"], "path": str(path), "surface": "repo"}

    return {"status": "FAIL", "checks": ["unsupported marketplace source"], "path": str(path)}


def marketplace_status(plugin_name: str, root: Path) -> dict:
    repo_path = root / ".agents" / "plugins" / "marketplace.json"
    if repo_path.is_file():
        return _marketplace_entry_status(plugin_name, repo_path, root)

    personal_path = Path.home() / ".agents" / "plugins" / "marketplace.json"
    if personal_path.is_file():
        return _marketplace_entry_status(plugin_name, personal_path, None)

    return {"status": "NOT_RUN", "checks": [], "path": str(repo_path), "surface": "repo"}


def build(root: Path, online: bool = False) -> dict:
    portable, portable_issues = validate_portable(root)
    adapter = reconcile(root)
    lock_path = root / "skills" / "agent-plugins-authoring" / "references" / "upstream" / "upstream-lock.json"
    source_root = lock_path.parent
    if lock_path.is_file():
        try:
            lock = strict_json_load(lock_path)
            upstream = online_report(lock) if online else local_report(lock, source_root)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            upstream = {"status": "SOURCE_CONFLICT", "diff": [str(exc)]}
    else:
        upstream = {"status": "NOT_RUN", "diff": ["upstream lock is missing"]}

    try:
        portable_manifest = strict_json_load(root / "plugin.json")
    except (OSError, ValueError):
        portable_manifest = {}
    plugin_name = str(portable_manifest.get("name", root.resolve().name))
    marketplace = marketplace_status(plugin_name, root)
    required_pass = portable["status"] == "PASS" and adapter["status"] == "PASS"
    if not required_pass:
        status = "FAIL"
    elif upstream.get("status") in {"SOURCE_UNAVAILABLE", "SOURCE_CONFLICT", "LOCAL_BASELINE_STALE"}:
        status = "UNVERIFIED"
    else:
        status = "PASS"
    return {
        "schema_version": "agent-plugins-author-report.v1",
        "mode": "audit",
        "status": status,
        "portable": {
            "status": portable["status"],
            "checks": portable["checks"],
            "issues": portable_issues,
        },
        "upstream": upstream,
        "codex_adapter": adapter,
        "security": {"status": portable["checks"].get("security", "NOT_RUN")},
        "marketplace": marketplace,
        "installation": {"status": "NOT_RUN", "checks": []},
        "host_readback": {"status": "NOT_RUN", "checks": []},
        "tests": {"status": "NOT_RUN", "checks": []},
        "next_action": "Run the focused test suite and host installation/readback only when explicitly requested.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--online", action="store_true", help="refresh allowlisted GitHub sources")
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build(args.plugin_root, online=args.online)
    encoded = stable_json(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    elif args.format == "json":
        print(encoded, end="")
    else:
        print(f"{report['status']}: {args.plugin_root}")
        print(f"portable={report['portable']['status']} upstream={report['upstream'].get('status')} adapter={report['codex_adapter']['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
