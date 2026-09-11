#!/usr/bin/env python3
"""Build a deterministic, source-backed plugin package archive."""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path
from typing import Any

from common import stable_json


EXCLUDED_DIRECTORIES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def package_files(root: Path, output: Path | None = None) -> list[Path]:
    output_resolved = output.resolve() if output else None
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if output_resolved and path.resolve() == output_resolved:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix().lower())


def build(root: Path, output: Path) -> dict[str, Any]:
    files = package_files(root, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {"status": "PASS", "path": str(output), "files": len(files), "sha256": digest}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    try:
        report = build(args.plugin_root, args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        report = {"status": "FAIL", "path": str(args.output), "issues": [str(exc)]}
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {report.get('path', args.output)}")
        if "sha256" in report:
            print(f"files={report['files']} sha256={report['sha256']}")
        for issue in report.get("issues", []):
            print(f"- {issue}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
