import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "assets" / "icon.svg"
PROVENANCE = ROOT / "provenance" / "file-provenance.json"
ADAPTER = ROOT / ".codex-plugin" / "plugin.json"


def test_icon_is_self_contained_and_accessible_svg():
    data = ICON.read_text(encoding="utf-8")
    root = ET.fromstring(data)
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 256 256"
    assert root.attrib["role"] == "img"
    assert "aria-labelledby" in root.attrib
    assert "<script" not in data.lower()
    assert "href=" not in data.lower()
    assert "xlink:href" not in data.lower()
    assert data.count("http://www.w3.org/2000/svg") == 1
    assert "https://" not in data


def test_codex_adapter_references_the_original_icon():
    manifest = json.loads(ADAPTER.read_text(encoding="utf-8"))
    interface = manifest["interface"]
    assert interface["composerIcon"] == "./assets/icon.svg"
    assert interface["logo"] == "./assets/icon.svg"
    assert interface["logoDark"] == "./assets/icon.svg"


def test_icon_provenance_hash_matches_source():
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    record = provenance["files"]["assets/icon.svg"]
    digest = hashlib.sha256(ICON.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert record["origin"] == "original-authored"
    assert record["sha256"] == digest
