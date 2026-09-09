import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / ".codex-plugin" / "plugin.json"
SCRIPT = ROOT / "skills" / "agent-plugins-authoring" / "scripts" / "reconcile_manifests.py"


def cachebuster_path() -> Path | None:
    candidates = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "skills" / ".system" / "plugin-creator" / "scripts" / "update_plugin_cachebuster.py")
    candidates.append(Path.home() / ".codex" / "skills" / ".system" / "plugin-creator" / "scripts" / "update_plugin_cachebuster.py")
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def test_codex_adapter_has_creator_scaffold_shape():
    manifest = json.loads(ADAPTER.read_text(encoding="utf-8"))
    assert manifest["name"] == "agent-plugins-author"
    assert manifest["skills"] == "./skills/"
    assert "mcpServers" not in manifest
    assert "apps" not in manifest


def test_manifest_reconciliation_passes():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(ROOT), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"


def test_plugin_creator_cachebuster_keeps_a_single_suffix(tmp_path):
    cachebuster = cachebuster_path()
    if cachebuster is None:
        pytest.skip("plugin-creator cachebuster helper is host-provided and unavailable in this runner")
    package = tmp_path / "agent-plugins-author"
    (package / ".codex-plugin").mkdir(parents=True)
    shutil.copy2(ADAPTER, package / ".codex-plugin" / "plugin.json")
    first = subprocess.run(
        [sys.executable, str(cachebuster), str(package), "--cachebuster", "first"],
        capture_output=True,
        text=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, str(cachebuster), str(package), "--cachebuster", "second"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert json.loads((package / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"] == "0.1.0+codex.second"
