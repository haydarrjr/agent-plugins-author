import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "reconcile_surfaces.py"


def test_all_checked_in_surfaces_reconcile_without_host_inference():
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), str(ROOT), "--skip-native-validator", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    assert report["codex_plugin_adapter"]["status"] == "PASS"
    assert report["codex_ide_adapter"]["status"] == "PASS"
    assert report["github_copilot"]["status"] == "PASS"
    assert report["marketplace"]["status"] == "PASS"
    assert report["mcp_host_config"]["status"] == "NOT_RUN"
    assert report["provenance"]["adapter_lock"]["status"] == "PASS"


def test_no_machine_specific_path_contracts_remain():
    candidates = [
        ROOT / "skills" / "agent-plugins-authoring" / "scripts",
        ROOT / "skills" / "agent-plugins-authoring" / "references",
    ]
    forbidden = "C:\\Users\\onder"
    for directory in candidates:
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".md", ".yaml", ".json"}:
                assert forbidden not in path.read_text(encoding="utf-8"), path
