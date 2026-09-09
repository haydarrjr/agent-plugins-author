import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "skills" / "agent-plugins-authoring" / "references" / "upstream"
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "adopt_upstream.py"


def test_explicit_adoption_updates_only_the_selected_temp_baseline(tmp_path):
    lock = json.loads((UPSTREAM / "upstream-lock.json").read_text(encoding="utf-8"))
    lock_path = tmp_path / "upstream-lock.json"
    lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")
    source = tmp_path / "source" / "1.0.0"
    source.mkdir(parents=True)
    for name in ("plugin.schema.json", "mcp.schema.json"):
        shutil.copy2(UPSTREAM / "1.0.0" / name, source / name)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--lock",
            str(lock_path),
            "--source-root",
            str(tmp_path / "source"),
            "--version",
            "1.0.0",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    adopted = json.loads(lock_path.read_text(encoding="utf-8"))["adopted"]
    assert adopted["version"] == "1.0.0"
    assert (tmp_path / "1.0.0" / "plugin.schema.json").is_file()


def test_draft_adoption_fails_without_explicit_experimental_flag(tmp_path):
    lock = {
        "schema_version": "agent-plugins-author.upstream-lock.v1",
        "adopted": {"version": "1.0.0", "status": "PUBLISHED", "files": []},
        "observed": {"versions": [{"version": "1.1.0", "status": "WORKING_DRAFT"}]},
    }
    lock_path = tmp_path / "upstream-lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--lock", str(lock_path), "--source-root", str(tmp_path), "--version", "1.1.0", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    report = json.loads(result.stdout)
    assert "draft adoption requires" in report["error"]
    assert json.loads(lock_path.read_text(encoding="utf-8"))["adopted"]["version"] == "1.0.0"
