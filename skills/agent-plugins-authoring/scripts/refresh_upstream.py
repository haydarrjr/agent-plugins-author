#!/usr/bin/env python3
"""Observe allowlisted Agent Plugins sources and emit a non-mutating diff."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from common import sha256_file, stable_json, strict_json_load


SPEC_REPOSITORY = "agentplugins/agent-plugins-spec"
API_BASE = "https://api.github.com/repos/agentplugins/agent-plugins-spec"
RAW_BASE = "https://raw.githubusercontent.com/agentplugins/agent-plugins-spec"
ALLOWED_HOSTS = {"api.github.com", "raw.githubusercontent.com"}


def fetch(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"source host is not allowlisted: {parsed.hostname}")
    request = Request(url, headers={"User-Agent": "agent-plugins-author/0.1"})
    with urlopen(request, timeout=20) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch(url).decode("utf-8"))


def snapshot_path(source_root: Path, version: str, source_path: str) -> Path:
    direct = source_root / source_path
    if direct.is_file():
        return direct
    return source_root / version / Path(source_path).name


def local_report(lock: dict, source_root: Path) -> dict:
    adopted = lock.get("adopted", {})
    observed = lock.get("observed", {})
    diffs: list[str] = []
    files = []
    for entry in adopted.get("files", []):
        path = snapshot_path(source_root, str(adopted.get("version", "")), entry["path"])
        if not path.is_file():
            diffs.append(f"missing snapshot: {entry['path']}")
            continue
        actual = sha256_file(path)
        files.append({"path": entry["path"], "sha256": actual})
        if actual != entry.get("sha256"):
            diffs.append(f"hash changed: {entry['path']}")
    drafts = [version for version in observed.get("versions", []) if version.get("status") == "WORKING_DRAFT"]
    if diffs:
        status = "LOCAL_BASELINE_STALE"
    elif drafts:
        status = "DRAFT_AVAILABLE"
    else:
        status = "NO_CHANGE"
    return {
        "schema_version": "agent-plugins-author-report.v1",
        "mode": "refresh",
        "status": status,
        "adopted": {
            "version": adopted.get("version"),
            "status": adopted.get("status"),
            "repository": adopted.get("repository"),
            "commit": adopted.get("commit"),
            "tree": adopted.get("tree"),
            "files": files,
        },
        "observed": observed,
        "diff": diffs,
        "source": "local-snapshot",
    }


def parse_versions(readme: str, schema_paths: list[str]) -> list[dict[str, str]]:
    versions: dict[str, str] = {}
    for path in schema_paths:
        parts = path.split("/")
        if len(parts) >= 3 and parts[0] == "schemas":
            versions.setdefault(parts[1], "UNKNOWN")
    lowered = readme.lower()
    if "1.0.0" in versions:
        versions["1.0.0"] = "PUBLISHED" if "1.0.0" in lowered and "published" in lowered else "UNKNOWN"
    if "1.1.0" in versions:
        versions["1.1.0"] = "WORKING_DRAFT" if "1.1.0" in lowered and "working draft" in lowered else "UNKNOWN"
    return [{"version": version, "status": status} for version, status in sorted(versions.items())]


def online_report(lock: dict) -> dict:
    try:
        commit = fetch_json(f"{API_BASE}/commits/main")
        commit_sha = commit["sha"]
        tree_sha = commit["commit"]["tree"]["sha"]
        tree = fetch_json(f"{API_BASE}/git/trees/{tree_sha}?recursive=1")
        paths = [item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"]
        schema_paths = [path for path in paths if path.startswith("schemas/") and path.endswith("/plugin.schema.json")]
        readme = fetch(f"{RAW_BASE}/{commit_sha}/README.md").decode("utf-8", errors="replace")
        versions = parse_versions(readme, schema_paths)
        adopted = lock.get("adopted", {})
        adopted_files = []
        diffs: list[str] = []
        for entry in adopted.get("files", []):
            path = entry["path"]
            data = fetch(f"{RAW_BASE}/{commit_sha}/{path}")
            digest = hashlib.sha256(data).hexdigest()
            adopted_files.append({"path": path, "sha256": digest})
            if digest != entry.get("sha256"):
                diffs.append(f"hash changed: {path}")
        adopted_version = str(adopted.get("version", ""))
        adopted_status = next((item["status"] for item in versions if item["version"] == adopted_version), "UNKNOWN")
        has_draft = any(item["status"] == "WORKING_DRAFT" for item in versions)
        if diffs:
            status = "PUBLISHED_CHANGE" if adopted_status == "PUBLISHED" else "SOURCE_CONFLICT"
        elif has_draft:
            status = "DRAFT_AVAILABLE"
        else:
            status = "NO_CHANGE"
        return {
            "schema_version": "agent-plugins-author-report.v1",
            "mode": "refresh",
            "status": status,
            "adopted": {
                "version": adopted.get("version"),
                "status": adopted_status,
                "repository": SPEC_REPOSITORY,
                "commit": commit_sha,
                "tree": tree_sha,
                "files": adopted_files,
            },
            "observed": {
                "repository": SPEC_REPOSITORY,
                "ref": "main",
                "commit": commit_sha,
                "tree": tree_sha,
                "versions": versions,
            },
            "diff": diffs,
            "source": "github-allowlisted",
        }
    except (OSError, KeyError, TypeError, ValueError, URLError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "agent-plugins-author-report.v1",
            "mode": "refresh",
            "status": "SOURCE_UNAVAILABLE",
            "adopted": {
                "version": lock.get("adopted", {}).get("version"),
                "status": lock.get("adopted", {}).get("status"),
            },
            "observed": {},
            "diff": [],
            "error": str(exc),
            "source": "github-allowlisted",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_lock = Path(__file__).resolve().parents[1] / "references" / "upstream" / "upstream-lock.json"
    parser.add_argument("--lock", type=Path, default=default_lock)
    parser.add_argument("--source-root", type=Path, default=default_lock.parent)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--online", action="store_true", help="use the allowlisted GitHub source (the default)")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="json")
    args = parser.parse_args()
    try:
        lock = strict_json_load(args.lock)
        report = local_report(lock, args.source_root) if args.offline else online_report(lock)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = {
            "schema_version": "agent-plugins-author-report.v1",
            "mode": "refresh",
            "status": "SOURCE_CONFLICT",
            "adopted": {},
            "observed": {},
            "diff": [],
            "error": str(exc),
        }
    encoded = stable_json(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    elif args.format == "text":
        print(f"{report['status']}: adopted={report.get('adopted', {}).get('version')}")
        for item in report.get("diff", []):
            print(f"- {item}")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
