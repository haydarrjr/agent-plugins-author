import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "validate_agent_plugin.py"


def run_validator(plugin_root):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(plugin_root), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )


def copy_minimal_package(tmp_path):
    package = tmp_path / "package"
    skill = package / "skills" / "example"
    skill.mkdir(parents=True)
    (package / "plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "example",
            }
        ),
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        "---\nname: example\ndescription: Use when testing a portable plugin.\n---\n\n# Example\n",
        encoding="utf-8",
    )
    return package


def test_native_fields_are_rejected_from_portable_manifest(tmp_path):
    package = copy_minimal_package(tmp_path)
    manifest_path = package / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["mcpServers"] = "./.mcp.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = run_validator(package)
    assert result.returncode != 0
    assert "mcpServers" in result.stdout


def test_secret_values_are_rejected(tmp_path):
    package = copy_minimal_package(tmp_path)
    (package / "credentials.env").write_text("GITHUB_TOKEN=ghp_not-a-real-token\n", encoding="utf-8")
    result = run_validator(package)
    assert result.returncode != 0
    assert "secret" in result.stdout.lower() or "credential" in result.stdout.lower()


def test_mcp_credentials_are_rejected_even_when_mcp_is_structurally_valid(tmp_path):
    package = copy_minimal_package(tmp_path)
    (package / "mcp.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
                "mcpServers": {
                    "remote": {
                        "type": "streamable-http",
                        "url": "https://example.invalid/mcp",
                        "headers": {"Authorization": "Bearer hard-coded-secret-value"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    result = run_validator(package)
    assert result.returncode != 0
    assert "MCP_SECRET" in result.stdout
