import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"


def test_repo_marketplace_points_to_public_plugin_root():
    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    assert marketplace["name"] == "agent-plugins-author"
    assert marketplace["interface"]["displayName"] == "Agent Plugins Author"
    assert len(marketplace["plugins"]) == 1

    entry = marketplace["plugins"][0]
    assert entry["name"] == "agent-plugins-author"
    assert entry["source"] == {
        "source": "url",
        "url": "https://github.com/haydarrjr/agent-plugins-author.git",
        "ref": "main",
    }
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["category"] == "Productivity"
