import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "materialize_ide_adapter.py"
VALIDATOR = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "validate_codex_ide_adapter.py"


def test_generated_ide_surface_has_exact_canonical_parity():
    result = subprocess.run(
        [sys.executable, "-B", str(MATERIALIZER), str(ROOT), "--check", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    assert report["expected_files"] == report["actual_files"]
    assert report["checks"]["hash_parity"] == "PASS"


def test_ide_adapter_reports_stale_generated_content(tmp_path):
    output = tmp_path / "skills"
    materialize = subprocess.run(
        [sys.executable, "-B", str(MATERIALIZER), str(ROOT), "--output", str(output), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert materialize.returncode == 0, materialize.stdout + materialize.stderr
    target = output / "agent-plugins-authoring" / "SKILL.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nlocal drift\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-B", str(VALIDATOR), str(ROOT), "--output", str(output), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    report = json.loads(result.stdout)
    assert any(issue["code"] == "IDE_SKILL_HASH_MISMATCH" for issue in report["issues"])
    assert not (output / "AGENTS.md").exists()
