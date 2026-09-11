#!/usr/bin/env python3
"""Run deterministic, Astra-aware quality checks for skill design.

The linter deliberately separates objective errors from routing and context
warnings.  It is a design signal, not a semantic substitute for model-based
evaluation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from common import parse_frontmatter, relative_path, stable_json


FALLBACK_INDEX_BUDGET = 8_000
DESCRIPTION_WARN_CHARS = 240
DESCRIPTION_ERROR_CHARS = 400
ROOT_WARN_LINES = 80
ROOT_ERROR_LINES = 160

STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "use",
    "when",
    "with",
}
ACTION_WORDS = {
    "audit",
    "author",
    "build",
    "check",
    "create",
    "design",
    "generate",
    "implement",
    "maintain",
    "package",
    "port",
    "refresh",
    "review",
    "update",
    "validate",
}
DOMAIN_WORDS = {
    "adapter",
    "agent",
    "agents",
    "codex",
    "compatibility",
    "config",
    "ide",
    "manifest",
    "marketplace",
    "mcp",
    "plugin",
    "plugins",
    "repository",
    "skill",
    "skills",
    "upstream",
}
GENERIC_TRIGGER_PHRASES = (
    "working with",
    "anything related",
    "any database",
    "all database",
    "when coding",
    "for any",
    "in any",
)
RECIPE_PATTERNS = (
    re.compile(r"\balways\s+(?:first\s+)?(?:read|inspect|run|check)\b", re.I),
    re.compile(r"\bask\s+(?:for|permission)\b", re.I),
    re.compile(r"\bstop\s+(?:after|until)\b", re.I),
    re.compile(r"\bnever\s+proceed\b", re.I),
    re.compile(r"\brun\s+(?:all|everything|the full)\b", re.I),
)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9_-]*", text.lower())
        if token not in STOP_WORDS and len(token) > 2
    }


def _issue(severity: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    issue = {"severity": severity, "code": code, "message": message}
    if path:
        issue["path"] = path
    return issue


def _load_skills(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    skills_root = root / "skills"
    records: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    if not skills_root.is_dir():
        return records, [_issue("ERROR", "SKILLS_ROOT_MISSING", "skills/ is missing", "skills")]
    for skill_dir in sorted(
        (path for path in skills_root.iterdir() if path.is_dir()),
        key=lambda path: path.name.lower(),
    ):
        skill_file = skill_dir / "SKILL.md"
        rel = relative_path(root, skill_file)
        if not skill_file.is_file():
            issues.append(_issue("ERROR", "MISSING_SKILL_FILE", "skill directory must contain SKILL.md", rel))
            continue
        try:
            content = skill_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(_issue("ERROR", "SKILL_READ_ERROR", str(exc), rel))
            continue
        frontmatter, error = parse_frontmatter(content)
        if error:
            issues.append(_issue("ERROR", "INVALID_FRONTMATTER", error, rel))
            continue
        records.append(
            {
                "name": skill_dir.name,
                "dir": skill_dir,
                "path": rel,
                "content": content,
                "frontmatter": frontmatter,
                "description": frontmatter.get("description", "").strip(),
            }
        )
    return records, issues


def _lint_description(record: dict[str, Any], root: Path) -> list[dict[str, str]]:
    description = record["description"]
    path = record["path"]
    issues: list[dict[str, str]] = []
    if not description:
        return [_issue("ERROR", "DESCRIPTION_SCOPE", "description must explain the job and its trigger scope", path)]
    if len(description) > DESCRIPTION_ERROR_CHARS:
        issues.append(
            _issue(
                "ERROR",
                "DESCRIPTION_BLOAT",
                f"description is {len(description)} characters; keep the routing surface concise",
                path,
            )
        )
    elif len(description) > DESCRIPTION_WARN_CHARS:
        issues.append(
            _issue(
                "WARN",
                "DESCRIPTION_BLOAT",
                f"description is {len(description)} characters; shorter routing metadata is preferred",
                path,
            )
        )
    tokens = _tokens(description)
    frontloaded = _tokens(description[:96])
    if not tokens & ACTION_WORDS:
        issues.append(_issue("ERROR", "DESCRIPTION_SCOPE", "description must start with an actionable job", path))
    if not tokens & DOMAIN_WORDS:
        issues.append(_issue("WARN", "DESCRIPTION_SCOPE", "description does not name a narrow domain or artifact", path))
    if not frontloaded & (ACTION_WORDS | DOMAIN_WORDS):
        issues.append(
            _issue(
                "WARN",
                "TRIGGER_NOT_FRONTLOADED",
                "important action or domain terms should appear near the start of the description",
                path,
            )
        )
    lowered = description.lower()
    for phrase in GENERIC_TRIGGER_PHRASES:
        if phrase in lowered:
            issues.append(
                _issue(
                    "WARN",
                    "GENERIC_TRIGGER_OVERREACH",
                    f"generic trigger phrase broadens routing scope: {phrase}",
                    path,
                )
            )
    if lowered.startswith("use when"):
        issues.append(
            _issue(
                "INFO",
                "OPTIONAL_USE_WHEN_PATTERN",
                "Use when is supported but is not required; lead with the job and narrow scope",
                path,
            )
        )
    return issues


def _lint_root(record: dict[str, Any], root: Path) -> list[dict[str, str]]:
    content = record["content"]
    path = record["path"]
    issues: list[dict[str, str]] = []
    line_count = len(content.splitlines())
    if line_count > ROOT_ERROR_LINES:
        issues.append(_issue("ERROR", "ROOT_SKILL_BLOAT", f"root SKILL.md has {line_count} lines", path))
    elif line_count > ROOT_WARN_LINES:
        issues.append(_issue("WARN", "ROOT_SKILL_BLOAT", f"root SKILL.md has {line_count} lines", path))

    reference_dir = record["dir"] / "references"
    references = list(reference_dir.rglob("*")) if reference_dir.is_dir() else []
    if references and not re.search(r"references[/\\]", content, re.I):
        issues.append(
            _issue(
                "WARN",
                "NON_PROGRESSIVE_DISCLOSURE",
                "supporting references exist but the root router does not point to them",
                path,
            )
        )
    if re.search(r"always\s+(?:read|load|inspect).{0,80}reference|read\s+all\s+references", content, re.I):
        issues.append(
            _issue(
                "WARN",
                "UNCONDITIONAL_REFERENCE_LOAD",
                "references should be selected by workflow rather than loaded unconditionally",
                path,
            )
        )
    if re.search(r"always\s+run|run\s+(?:all|everything|the full)\s+(?:tests|suite)|blanket testing", content, re.I):
        issues.append(
            _issue(
                "WARN",
                "UNCONDITIONAL_TESTING",
                "verification should be change-scoped unless a release gate requires the full suite",
                path,
            )
        )
    if len(re.findall(r"^\s*(?:step\s+)?\d+[.)]\s+", content, re.I | re.M)) >= 5:
        issues.append(
            _issue(
                "WARN",
                "UNNECESSARY_RECIPE",
                "root skill contains a long itinerary; keep decisions and completion conditions instead",
                path,
            )
        )
    for pattern in RECIPE_PATTERNS:
        if pattern.search(content):
            issues.append(
                _issue(
                    "WARN",
                    "UNNECESSARY_RECIPE",
                    "generic procedural guardrail may over-constrain a capable authoring model",
                    path,
                )
            )
            break
    return issues


def _lint_collisions(records: list[dict[str, Any]], root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for index, left in enumerate(records):
        left_tokens = _tokens(left["description"])
        for right in records[index + 1 :]:
            right_tokens = _tokens(right["description"])
            common = left_tokens & right_tokens
            union = left_tokens | right_tokens
            similarity = len(common) / len(union) if union else 0.0
            if len(common) >= 3 and similarity >= 0.45:
                issues.append(
                    _issue(
                        "WARN",
                        "SKILL_TRIGGER_COLLISION",
                        f"candidate routing overlap with {right['name']} (Jaccard={similarity:.2f}); review semantically",
                        left["path"],
                    )
                )
    return issues


def _context_budget(records: list[dict[str, Any]]) -> dict[str, Any]:
    description_chars = sum(len(record["description"]) for record in records)
    projected = sum(
        len(record["name"]) + len(record["description"]) + len(record["path"]) + 12
        for record in records
    )
    if projected > FALLBACK_INDEX_BUDGET:
        risk = "TRUNCATION_RISK"
    elif projected > int(FALLBACK_INDEX_BUDGET * 0.8):
        risk = "PASS_WITH_WARNING"
    else:
        risk = "PASS"
    return {
        "skills": len(records),
        "description_chars": description_chars,
        "projected_index_chars": projected,
        "fallback_budget": FALLBACK_INDEX_BUDGET,
        "risk": risk,
    }


def _trigger_score(prompt: str, description: str) -> tuple[int, set[str]]:
    prompt_tokens = _tokens(prompt)
    description_tokens = _tokens(description)
    matched = prompt_tokens & description_tokens
    return len(matched), matched


def _evaluate_trigger_fixture(records: list[dict[str, Any]], path: Path | None) -> tuple[dict[str, Any], list[dict[str, str]]]:
    if path is None:
        return {"status": "NOT_RUN", "cases": []}, []
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "FAIL", "cases": []}, [_issue("ERROR", "TRIGGER_FIXTURE", str(exc), str(path))]
    if isinstance(fixture, list):
        fixture = {"skill": records[0]["name"] if records else "", "should_trigger": fixture}
    target_name = fixture.get("skill")
    target = next((record for record in records if record["name"] == target_name), None)
    if target is None:
        return {"status": "FAIL", "cases": []}, [_issue("ERROR", "TRIGGER_SKILL_MISSING", f"fixture skill is not present: {target_name}", str(path))]

    issues: list[dict[str, str]] = []
    cases: list[dict[str, Any]] = []

    def check_section(section: str, expected_trigger: bool) -> None:
        for item in fixture.get(section, []):
            prompt = item if isinstance(item, str) else str(item.get("prompt", ""))
            score, matched = _trigger_score(prompt, target["description"])
            actual = score >= 2
            cases.append({"section": section, "prompt": prompt, "score": score, "matched": sorted(matched), "triggers": actual})
            if actual != expected_trigger:
                issues.append(
                    _issue(
                        "ERROR",
                        "TRIGGER_ROUTING_MISMATCH",
                        f"{section} case routed={'yes' if actual else 'no'} with matched={sorted(matched)}",
                        str(path),
                    )
                )

    check_section("should_trigger", True)
    check_section("should_not_trigger", False)
    for item in fixture.get("ambiguous", []):
        prompt = item if isinstance(item, str) else str(item.get("prompt", ""))
        score, matched = _trigger_score(prompt, target["description"])
        cases.append({"section": "ambiguous", "prompt": prompt, "score": score, "matched": sorted(matched), "triggers": score >= 2})
    for item in fixture.get("competing_skill", []):
        prompt = item if isinstance(item, str) else str(item.get("prompt", ""))
        expected_skill = None if isinstance(item, str) else item.get("expected_skill")
        score, matched = _trigger_score(prompt, target["description"])
        actual = target["name"] if score >= 2 else None
        cases.append({"section": "competing_skill", "prompt": prompt, "score": score, "matched": sorted(matched), "selected": actual})
        if expected_skill != actual:
            issues.append(
                _issue(
                    "ERROR",
                    "SKILL_TRIGGER_COLLISION",
                    f"competing case selected {actual!r}; expected {expected_skill!r}",
                    str(path),
                )
            )
    return {"status": "FAIL" if issues else "PASS", "skill": target_name, "cases": cases}, issues


def lint(root: Path, eval_path: Path | None = None) -> dict[str, Any]:
    records, issues = _load_skills(root)
    for record in records:
        issues.extend(_lint_description(record, root))
        issues.extend(_lint_root(record, root))
    issues.extend(_lint_collisions(records, root))

    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        try:
            lines = len(agents_path.read_text(encoding="utf-8").splitlines())
        except OSError:
            lines = 0
        issues.append(
            _issue(
                "WARN",
                "AGENTS_CONTEXT_BLOAT",
                f"package-level AGENTS.md is present ({lines} lines); generate it only for justified repo-wide invariants",
                relative_path(root, agents_path),
            )
        )

    if eval_path is None:
        candidate = root / "tests" / "trigger-routing" / "agent-plugins-authoring.json"
        eval_path = candidate if candidate.is_file() else None
    trigger_eval, trigger_issues = _evaluate_trigger_fixture(records, eval_path)
    issues.extend(trigger_issues)
    errors = [issue for issue in issues if issue["severity"] == "ERROR"]
    warnings = [issue for issue in issues if issue["severity"] == "WARN"]
    info = [issue for issue in issues if issue["severity"] == "INFO"]
    return {
        "schema_version": "agent-plugins-author-skill-design.v1",
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "issues": issues,
        "skills": [{"name": record["name"], "path": record["path"], "description": record["description"]} for record in records],
        "context_budget": _context_budget(records),
        "trigger_eval": trigger_eval,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--eval-file", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    report = lint(args.plugin_root, args.eval_file)
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {args.plugin_root}")
        print(
            f"skills={len(report['skills'])} warnings={len(report['warnings'])} "
            f"context={report['context_budget']['risk']}"
        )
        for issue in report["issues"]:
            location = f" [{issue['path']}]" if "path" in issue else ""
            print(f"- {issue['severity']} {issue['code']}{location}: {issue['message']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
