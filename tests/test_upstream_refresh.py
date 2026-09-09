import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "refresh_upstream.py"
LOCK = ROOT / "skills" / "agent-plugins-authoring" / "references" / "upstream" / "upstream-lock.json"


def test_offline_refresh_is_read_only_and_reports_adopted_baseline(tmp_path):
    output = tmp_path / "refresh-report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--lock",
            str(LOCK),
            "--source-root",
            str(ROOT / "skills" / "agent-plugins-authoring" / "references" / "upstream"),
            "--offline",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] in {"NO_CHANGE", "DRAFT_AVAILABLE"}
    assert report["adopted"]["version"] == "1.0.0"
    assert json.loads(LOCK.read_text(encoding="utf-8"))["adopted"]["version"] == "1.0.0"
