#!/usr/bin/env python3
"""Validate GitHub Copilot Agent Plugins 1.0 source and marketplace semantics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import PORTABLE_SCHEMA, make_issue, parse_frontmatter, relative_path, stable_json, strict_json_load


CLIENT_NAMESPACE = "com.github.copilot"
CLIENT_CHILDREN = {"agents", "commands", "rules", "hooks", "lsp.json"}
LEGACY_ROOT_COMPONENTS = {"agents", "commands", "rules", "hooks", "hooks.json", "lsp.json"}


def _marketplace_status(root: Path, manifest: dict[str, Any], required: bool) -> tuple[str, list[dict[str, str]]]:
    path = root / ".github" / "plugin" / "marketplace.json"
    if not path.is_file():
        if required:
            return "FAIL", [make_issue("COPILOT_MARKETPLACE_MISSING", "Copilot marketplace is required", relative_path(root, path))]
        return "NOT_RUN", []
    issues: list[dict[str, str]] = []
    try:
        catalog = strict_json_load(path)
    except (OSError, ValueError) as exc:
        return "FAIL", [make_issue("COPILOT_MARKETPLACE_JSON", str(exc), relative_path(root, path))]
    if not isinstance(catalog, dict):
        return "FAIL", [make_issue("COPILOT_MARKETPLACE_SHAPE", "marketplace must be a JSON object", relative_path(root, path))]
    owner = catalog.get("owner")
    if not isinstance(catalog.get("name"), str) or not catalog.get("name"):
        issues.append(make_issue("COPILOT_MARKETPLACE_NAME", "marketplace name is required", relative_path(root, path)))
    if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner.get("name"):
        issues.append(make_issue("COPILOT_MARKETPLACE_OWNER", "marketplace owner.name is required", relative_path(root, path)))
    entries = catalog.get("plugins")
    if not isinstance(entries, list):
        issues.append(make_issue("COPILOT_MARKETPLACE_PLUGINS", "marketplace plugins must be an array", relative_path(root, path)))
        entries = []
    name = manifest.get("name")
    matching = [entry for entry in entries if isinstance(entry, dict) and entry.get("name") == name]
    if len(matching) != 1:
        issues.append(make_issue("COPILOT_MARKETPLACE_ENTRY", "expected exactly one marketplace entry matching plugin.json name", relative_path(root, path)))
    else:
        entry = matching[0]
        source = entry.get("source")
        if not isinstance(source, (str, dict)):
            issues.append(make_issue("COPILOT_MARKETPLACE_SOURCE", "plugin source must be a relative path, GitHub source, or URL source", relative_path(root, path)))
        elif isinstance(source, dict) and source.get("source") not in {"github", "url"}:
            issues.append(make_issue("COPILOT_MARKETPLACE_SOURCE", "source object must use github or url", relative_path(root, path)))
        if entry.get("version") is not None and entry.get("version") != manifest.get("version"):
            issues.append(make_issue("COPILOT_MARKETPLACE_VERSION", "marketplace version must match plugin.json", relative_path(root, path)))
        if entry.get("strict", True) is not True:
            issues.append(make_issue("COPILOT_MARKETPLACE_STRICT", "Agent Plugins 1.0 marketplace entry must keep strict validation enabled", relative_path(root, path)))
    return ("PASS" if not issues else "FAIL"), issues


def validate(root: Path, require_marketplace: bool = False) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    try:
        manifest = strict_json_load(root / "plugin.json")
    except (OSError, ValueError) as exc:
        return {"status": "FAIL", "checks": {}, "issues": [make_issue("COPILOT_MANIFEST", str(exc), "plugin.json")]}
    if not isinstance(manifest, dict):
        return {"status": "FAIL", "checks": {}, "issues": [make_issue("COPILOT_MANIFEST", "plugin.json must be a JSON object", "plugin.json")]}
    if manifest.get("$schema") != PORTABLE_SCHEMA:
        issues.append(make_issue("COPILOT_AGENT_PLUGINS_SCHEMA", "Copilot Agent Plugins 1.0 requires the exact portable 1.0.0 schema", "plugin.json"))

    skills_root = root / "skills"
    if not skills_root.is_dir():
        issues.append(make_issue("COPILOT_SKILLS_ROOT", "Agent Plugins 1.0 skills/ directory is missing", "skills"))
    else:
        for skill_dir in sorted((path for path in skills_root.iterdir() if path.is_dir()), key=lambda path: path.name.lower()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                issues.append(make_issue("COPILOT_SKILL_FILE", "skill directory must contain SKILL.md", relative_path(root, skill_file)))
                continue
            try:
                frontmatter, error = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
            except OSError as exc:
                issues.append(make_issue("COPILOT_SKILL_READ", str(exc), relative_path(root, skill_file)))
                continue
            if error:
                issues.append(make_issue("COPILOT_SKILL_FRONTMATTER", error, relative_path(root, skill_file)))
            elif frontmatter.get("name") != skill_dir.name:
                issues.append(make_issue("COPILOT_SKILL_NAME", "SKILL.md name must match its immediate skills/ directory", relative_path(root, skill_file)))

    for component in sorted(LEGACY_ROOT_COMPONENTS):
        if (root / component).exists():
            issues.append(make_issue("COPILOT_NAMESPACE", f"Agent Plugins 1.0 client-specific component belongs under {CLIENT_NAMESPACE}/, not {component}", component))

    namespace = root / CLIENT_NAMESPACE
    if namespace.exists():
        if not namespace.is_dir():
            issues.append(make_issue("COPILOT_NAMESPACE", f"{CLIENT_NAMESPACE} must be a directory", CLIENT_NAMESPACE))
        else:
            for child in namespace.iterdir():
                if child.name not in CLIENT_CHILDREN:
                    issues.append(make_issue("COPILOT_NAMESPACE_CHILD", f"unsupported Copilot namespace child: {child.name}", relative_path(root, child)))
            hooks = namespace / "hooks"
            if hooks.exists() and (not hooks.is_dir() or not (hooks / "hooks.json").is_file()):
                issues.append(make_issue("COPILOT_HOOKS", "Copilot hooks must use com.github.copilot/hooks/hooks.json", relative_path(root, hooks)))

    marketplace_status, marketplace_issues = _marketplace_status(root, manifest, require_marketplace)
    issues.extend(marketplace_issues)
    return {
        "status": "PASS" if not issues else "FAIL",
        "checks": {
            "agent_plugins_1_0": "PASS" if not any(item["code"] == "COPILOT_AGENT_PLUGINS_SCHEMA" for item in issues) else "FAIL",
            "skills": "PASS" if not any(item["code"].startswith("COPILOT_SKILL") or item["code"] == "COPILOT_SKILLS_ROOT" for item in issues) else "FAIL",
            "client_namespace": "PASS" if not any(item["code"].startswith("COPILOT_NAMESPACE") or item["code"] == "COPILOT_HOOKS" for item in issues) else "FAIL",
            "marketplace": marketplace_status,
        },
        "marketplace": marketplace_status,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--require-marketplace", action="store_true")
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    report = validate(args.plugin_root, args.require_marketplace)
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
