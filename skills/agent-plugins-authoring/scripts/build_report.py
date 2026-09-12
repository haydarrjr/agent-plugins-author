#!/usr/bin/env python3
"""Build the v2 Agent Plugins Author evidence report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import stable_json, strict_json_load, validate_portable
from reconcile_surfaces import reconcile_surfaces
from refresh_upstream import local_report, online_report
from validate_skill_design import lint as lint_skill_design


REPORT_SCHEMA = "agent-plugins-author-report.v2"


def _upstream_gate_status(status: str) -> str:
    if status in {"NO_CHANGE", "DRAFT_AVAILABLE"}:
        return "PASS"
    if status in {"SOURCE_UNAVAILABLE", "SOURCE_CONFLICT", "LOCAL_BASELINE_STALE", "PUBLISHED_CHANGE"}:
        return "UNVERIFIED"
    return "UNVERIFIED"


def build(
    root: Path,
    online: bool = False,
    run_native_validator: bool = True,
    eval_path: Path | None = None,
) -> dict[str, Any]:
    portable, portable_issues = validate_portable(root)
    skill_design = lint_skill_design(root, eval_path)
    surfaces = reconcile_surfaces(root, run_native_validator=run_native_validator)
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
    upstream_gate = _upstream_gate_status(upstream.get("status", "NOT_RUN"))
    security_status = portable["checks"].get("security", "NOT_RUN")
    source_statuses = [
        portable["status"],
        skill_design["status"],
        security_status,
        surfaces["status"],
        surfaces.get("github_copilot", {}).get("status", "UNVERIFIED"),
        upstream_gate,
    ]
    if "FAIL" in source_statuses:
        status = "FAIL"
    elif "UNVERIFIED" in source_statuses or "NOT_RUN" in source_statuses:
        status = "UNVERIFIED"
    else:
        status = "PASS"

    plugin_installation = {
        "status": "NOT_RUN",
        "checks": ["source and marketplace evidence do not prove installation"],
    }
    ide_discovery = {
        "status": "NOT_RUN",
        "checks": ["source parity does not prove Codex IDE, VS Code, or Copilot host discovery"],
    }
    host_readback = {"status": "NOT_RUN", "checks": []}
    live_status = {"status": "NOT_RUN", "checks": []}
    return {
        "schema_version": REPORT_SCHEMA,
        "mode": "audit",
        "status": status,
        "portable": {
            "status": portable["status"],
            "checks": portable["checks"],
            "skill_count": portable["skill_count"],
            "issues": portable_issues,
        },
        "skill_design": skill_design,
        "security": {"status": security_status, "checks": portable["checks"].get("security", "NOT_RUN")},
        "upstream": {**upstream, "gate_status": upstream_gate},
        "codex_plugin_adapter": surfaces.get("codex_plugin_adapter", {"status": "UNVERIFIED"}),
        "codex_ide_adapter": surfaces.get("codex_ide_adapter", {"status": "UNVERIFIED"}),
        "github_copilot": surfaces.get("github_copilot", {"status": "UNVERIFIED"}),
        "marketplace": surfaces.get("marketplace", {"status": "NOT_RUN"}),
        "mcp_host_config": surfaces.get("mcp_host_config", {"status": "NOT_RUN"}),
        "tests": {"status": "NOT_RUN", "checks": {"change_scoped": "NOT_RUN", "determinism": "NOT_RUN", "full_suite": "NOT_RUN"}},
        "plugin_installation": plugin_installation,
        "installation": plugin_installation,
        "ide_skill_discovery": ide_discovery,
        "host_readback": host_readback,
        "live_status": live_status,
        "provenance": surfaces.get("provenance", {}),
        "next_action": "Run the affected source-local validators and deterministic package gate; installation, host readback, and live status remain separate optional operations.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--online", action="store_true", help="refresh allowlisted GitHub sources")
    parser.add_argument("--skip-native-validator", action="store_true")
    parser.add_argument("--eval-file", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build(
        args.plugin_root,
        online=args.online,
        run_native_validator=not args.skip_native_validator,
        eval_path=args.eval_file,
    )
    encoded = stable_json(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    elif args.format == "json":
        print(encoded, end="")
    else:
        print(f"{report['status']}: {args.plugin_root}")
        print(
            " ".join(
                f"{name}={report[name]['status']}"
                for name in ("portable", "skill_design", "security", "codex_plugin_adapter", "codex_ide_adapter", "github_copilot", "marketplace")
                if name in report
            )
        )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
