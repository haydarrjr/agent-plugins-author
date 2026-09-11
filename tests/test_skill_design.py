import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "validate_skill_design.py"
PORTABLE_VALIDATOR = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "validate_agent_plugin.py"


def test_current_skill_design_and_trigger_fixture_pass():
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), str(ROOT), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    assert report["trigger_eval"]["status"] == "PASS"
    assert report["context_budget"]["risk"] == "PASS"
    assert not report["errors"]


def test_use_when_prefix_is_optional_for_portable_validation(tmp_path):
    package = tmp_path / "package"
    skill = package / "skills" / "example"
    skill.mkdir(parents=True)
    (package / "plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "example",
                "version": "0.1.0",
                "description": "Create and validate a narrow example skill.",
            }
        ),
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        "---\nname: example\ndescription: Create and validate a narrow example skill.\n---\n\n# Example\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-B", str(PORTABLE_VALIDATOR), str(package), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "INVALID_SKILL_DESCRIPTION" not in result.stdout


def test_pairwise_collision_is_a_warning_signal(tmp_path):
    package = tmp_path / "package"
    for name, description in (
        ("one", "Create and validate plugin manifests for Codex adapters."),
        ("two", "Create and validate plugin manifests for Codex IDE adapters."),
    ):
        skill = package / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
            encoding="utf-8",
        )
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), str(package), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert any(issue["code"] == "SKILL_TRIGGER_COLLISION" for issue in report["warnings"])
