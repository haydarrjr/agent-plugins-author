import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".github" / "plugin" / "marketplace.json"
VALIDATOR = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "validate_copilot_surface.py"
RENDERER = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "render_copilot_marketplace.py"


def test_copilot_marketplace_points_to_agent_plugins_root():
    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert marketplace["name"] == manifest["name"]
    assert marketplace["owner"]["name"] == manifest["author"]["name"]
    assert len(marketplace["plugins"]) == 1
    entry = marketplace["plugins"][0]
    assert entry["name"] == manifest["name"]
    assert entry["version"] == manifest["version"]
    assert entry["source"] == "."
    assert entry["strict"] is True


def test_copilot_surface_and_renderer_pass():
    for command in (
        [sys.executable, str(VALIDATOR), str(ROOT), "--require-marketplace", "--format", "json"],
        [sys.executable, str(RENDERER), str(ROOT), "--check", "--format", "json"],
    ):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)["status"] == "PASS"


def test_agent_plugins_1_0_rejects_legacy_root_copilot_components(tmp_path):
    package = tmp_path / "package"
    skill = package / "skills" / "example"
    skill.mkdir(parents=True)
    (package / "plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "example",
                "version": "0.1.0",
                "description": "Example plugin",
            }
        ),
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        "---\nname: example\ndescription: Validate an example plugin.\n---\n\n# Example\n",
        encoding="utf-8",
    )
    (package / "agents").mkdir()
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(package), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert any(issue["code"] == "COPILOT_NAMESPACE" for issue in report["issues"])
