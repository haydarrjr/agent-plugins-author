import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "render_mcp_config.py"


def test_mcp_renderer_uses_environment_references_without_credentials(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "mcp.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
                "mcpServers": {
                    "remote": {
                        "type": "streamable-http",
                        "url": "https://example.invalid/mcp",
                        "headers": {"Authorization": "Bearer ${MCP_TOKEN}"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    output = package / ".codex" / "config.toml.example"
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), str(package), "--output", str(output), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    content = output.read_text(encoding="utf-8")
    assert "MCP_TOKEN" in content
    assert "hard-coded" not in content
    assert "Bearer ${MCP_TOKEN}" not in content
