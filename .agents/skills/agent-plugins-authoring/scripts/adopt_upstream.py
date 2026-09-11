#!/usr/bin/env python3
"""Explicitly adopt a selected upstream schema snapshot."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

from common import sha256_bytes, stable_json, strict_json_load


def source_for(source_root: Path, version: str, filename: str) -> Path:
    direct = source_root / f"schemas/{version}/{filename}"
    if direct.is_file():
        return direct
    return source_root / version / filename


def adopt(lock_path: Path, source_root: Path, version: str, experimental: bool) -> dict:
    original_lock_bytes = lock_path.read_bytes()
    lock = strict_json_load(lock_path)
    observed = lock.get("observed", {})
    observed_version = next(
        (item for item in observed.get("versions", []) if item.get("version") == version),
        {"version": version, "status": "UNKNOWN"},
    )
    if observed_version.get("status") == "WORKING_DRAFT" and not experimental:
        raise ValueError("draft adoption requires --experimental")

    source_files = {
        "schemas/%s/plugin.schema.json" % version: source_for(source_root, version, "plugin.schema.json"),
        "schemas/%s/mcp.schema.json" % version: source_for(source_root, version, "mcp.schema.json"),
    }
    payloads: dict[str, bytes] = {}
    for relative, source in source_files.items():
        if not source.is_file():
            raise FileNotFoundError(f"missing adoption source: {source}")
        payloads[relative] = source.read_bytes()
    plugin_schema = json.loads(payloads[next(path for path in payloads if path.endswith("plugin.schema.json"))].decode("utf-8"))
    if plugin_schema.get("$id") != f"https://agent-plugins.org/schemas/{version}/plugin.schema.json":
        raise ValueError("plugin schema id does not match selected version")

    previous = copy.deepcopy(lock.get("adopted", {}))
    new_adopted = {
        "version": version,
        "status": observed_version.get("status", "UNKNOWN"),
        "repository": observed.get("repository", "agentplugins/agent-plugins-spec"),
        "ref": observed.get("ref", "main"),
        "commit": observed.get("commit", ""),
        "tree": observed.get("tree", ""),
        "files": [{"path": path, "sha256": sha256_bytes(data)} for path, data in sorted(payloads.items())],
    }
    new_lock = copy.deepcopy(lock)
    new_lock["adopted"] = new_adopted
    old_files: dict[Path, bytes | None] = {}
    staged_files: list[tuple[Path, Path]] = []
    try:
        target_dir = lock_path.parent
        with tempfile.TemporaryDirectory(prefix="agent-plugins-adopt-", dir=target_dir) as temp_name:
            temp_root = Path(temp_name)
            for relative, data in payloads.items():
                target = target_dir / version / Path(relative).name
                target.parent.mkdir(parents=True, exist_ok=True)
                old_files[target] = target.read_bytes() if target.is_file() else None
                staged = temp_root / Path(relative).name
                staged.write_bytes(data)
                staged_files.append((staged, target))
            lock_stage = temp_root / "upstream-lock.json"
            lock_stage.write_text(stable_json(new_lock), encoding="utf-8")
            for staged, target in staged_files:
                os.replace(staged, target)
            os.replace(lock_stage, lock_path)
    except Exception:
        for target, old_bytes in old_files.items():
            if old_bytes is None:
                try:
                    target.unlink()
                except FileNotFoundError:
                    pass
            else:
                target.write_bytes(old_bytes)
        lock_path.write_bytes(original_lock_bytes)
        raise

    return {
        "schema_version": "agent-plugins-author-report.v2",
        "mode": "adopt",
        "status": "PASS",
        "adopted": new_adopted,
        "previous": previous,
        "experimental": experimental,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_lock = Path(__file__).resolve().parents[1] / "references" / "upstream" / "upstream-lock.json"
    parser.add_argument("--lock", type=Path, default=default_lock)
    parser.add_argument("--source-root", type=Path, default=default_lock.parent)
    parser.add_argument("--version", required=True)
    parser.add_argument("--experimental", action="store_true")
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    try:
        report = adopt(args.lock, args.source_root, args.version, args.experimental)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = {
            "schema_version": "agent-plugins-author-report.v2",
            "mode": "adopt",
            "status": "FAIL",
            "error": str(exc),
        }
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {report.get('error', report.get('adopted', {}).get('version', ''))}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
