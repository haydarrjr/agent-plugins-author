import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "agent-plugins-authoring" / "SKILL.md"
SCENARIOS = ROOT / "tests" / "scenarios" / "pressure_scenarios.json"


def test_pressure_scenario_catalog_exists():
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    assert len(scenarios) >= 5
    assert {scenario["id"] for scenario in scenarios} == {
        "draft-is-not-production",
        "portable-native-boundary",
        "untrusted-upstream-content",
        "validation-is-not-installation",
        "safe-update-boundary",
    }


def test_skill_contains_pressure_responses():
    content = SKILL.read_text(encoding="utf-8").lower()
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    for scenario in scenarios:
        missing = [marker for marker in scenario["required_markers"] if marker.lower() not in content]
        assert not missing, f"{scenario['id']} missing markers: {missing}"
