# Quality gates v2

Run the narrowest applicable gates in this order and keep their evidence
separate:

G0. **Source and provenance** — exact source identity, asset provenance, and
    adopted versus observed upstream baseline.
G1. **Portable contract** — root manifest, schema version, skill discovery,
    frontmatter, containment, and forbidden native fields.
G2. **Security** — secrets, private keys, credential-bearing environment or
    headers, unsafe filenames, links, and path traversal.
G3. **Skill design** — description scope, bloat, generic triggers, collisions,
    progressive disclosure, recipes, and context budget.
G4. **Trigger routing** — positive, negative, ambiguous, and competing-skill
    fixtures.
G5. **Progressive disclosure** — root router and conditional references.
G6. **Codex plugin adapter** — native manifest shape, parity, and
    `plugin-creator` validation.
G7. **Codex IDE adapter** — generated `.agents/skills/` parity and no generated
    `AGENTS.md`.
G8. **MCP parity** — only when `mcp.json` exists; render host configuration
    without credentials.
G9. **Marketplace** — repo catalog identity and development/release ref mode.
G10. **Change-scoped verification** — only affected tests/evals for ordinary
    changes; full suite for package/release/adoption gates.
G11. **Package determinism** — repeated package and report output is stable.
G12. **Optional installation/readback** — host operations remain separate.

Every gate returns `PASS`, `FAIL`, `UNVERIFIED`, or `NOT_RUN`. A warning from
skill design is visible but does not become an objective error by itself.

## Change-scoped matrix

| Change | Required verification |
| --- | --- |
| Description only | metadata lint and trigger eval |
| `SKILL.md` behavior | skill validator and targeted behavior eval |
| Reference only | reference/link validation and affected eval |
| Python validator | affected unit tests and deterministic replay |
| Manifest | schema and surface reconciliation |
| Marketplace | deterministic marketplace validation |
| IDE adapter | materialize/check parity and skill discovery fixture |
| Upstream adoption | provenance, affected schemas, and regression suite |
| Release/package | complete package gate |

Every gate returns one of `PASS`, `FAIL`, `UNVERIFIED`, or `NOT_RUN`. A
failure or unknown source must not be upgraded by a later gate.

Recommended commands from the plugin root:

```text
python -B -m pytest -q tests
python <skill-creator>/scripts/quick_validate.py skills/agent-plugins-authoring
python <plugin-creator>/scripts/validate_plugin.py .
python skills/agent-plugins-authoring/scripts/validate_agent_plugin.py . --format json
python skills/agent-plugins-authoring/scripts/validate_skill_design.py . --format json
python skills/agent-plugins-authoring/scripts/materialize_ide_adapter.py . --check --format json
python skills/agent-plugins-authoring/scripts/reconcile_surfaces.py . --format json
python skills/agent-plugins-authoring/scripts/build_package.py . --output package.zip --format json
```
