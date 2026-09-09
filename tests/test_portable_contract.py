import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin.json"
VALIDATOR = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "validate_agent_plugin.py"


def test_portable_manifest_is_present_and_separate_from_codex_adapter():
    manifest = json.loads(PLUGIN.read_text(encoding="utf-8"))
    assert manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert manifest["name"] == "agent-plugins-author"
    assert "skills" not in manifest
    assert "mcpServers" not in manifest
    assert "apps" not in manifest


def test_portable_validator_passes_the_package():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(ROOT), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    assert report["portable"]["status"] == "PASS"
