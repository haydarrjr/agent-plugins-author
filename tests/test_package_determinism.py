import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "build_package.py"


def test_package_builder_is_byte_deterministic(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    for output in (first, second):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(ROOT), "--output", str(output), "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
