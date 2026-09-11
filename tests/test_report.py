import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "build_report.py"


def test_report_keeps_host_evidence_separate_from_local_validation():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(ROOT), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert {
        "schema_version",
        "mode",
        "status",
        "portable",
        "skill_design",
        "upstream",
        "codex_plugin_adapter",
        "codex_ide_adapter",
        "security",
        "marketplace",
        "mcp_host_config",
        "plugin_installation",
        "ide_skill_discovery",
        "installation",
        "host_readback",
        "live_status",
        "tests",
        "next_action",
    }.issubset(report)
    assert report["status"] == "PASS"
    assert report["schema_version"] == "agent-plugins-author-report.v2"
    assert report["installation"]["status"] == "NOT_RUN"
    assert report["plugin_installation"]["status"] == "NOT_RUN"
    assert report["ide_skill_discovery"]["status"] == "NOT_RUN"
    assert report["host_readback"]["status"] == "NOT_RUN"
    assert report["marketplace"]["status"] == "PASS"
