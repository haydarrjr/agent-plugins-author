# Quality gates v3

Select gates by the affected surface. Applicable source/provenance, portable
contract, and security boundaries are required; the sequence below is a useful
progression, not a mandatory itinerary. Skip non-applicable client surfaces and
choose the narrowest evidence that can prove the requested outcome.

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
    `plugin-creator` validation when that client is targeted.
G7. **Codex IDE adapter** — generated `.agents/skills/` parity when that
    standalone-skill compatibility surface is targeted.
G8. **GitHub Copilot** — Agent Plugins 1.0 semantics, optional
    `com.github.copilot/` namespace, and Copilot marketplace when targeted.
G9. **MCP parity** — only when `mcp.json` exists; render host configuration
    without credentials where a client adapter requires it.
G10. **Marketplace** — validate each requested client marketplace independently.
G11. **Change-scoped verification** — affected tests/evals for ordinary
    changes; broader validation for cross-cutting changes.
G12. **Package determinism** — repeated package and report output is stable.
G13. **Optional installation/readback** — host operations remain separate.

Every gate returns `PASS`, `FAIL`, `UNVERIFIED`, or `NOT_RUN`. A warning from
skill design is visible but does not become an objective error by itself. A
failure or unknown source must not be upgraded by a later gate.

## Typical evidence guide

| Change | Usually relevant evidence |
| --- | --- |
| Description only | metadata lint and trigger evaluation |
| `SKILL.md` behavior | skill validator and targeted behavior evaluation |
| Reference only | reference/link validation and affected evaluation |
| Python validator | affected unit tests and deterministic replay |
| Portable manifest | schema, security, and affected surface reconciliation |
| Codex marketplace | deterministic Codex marketplace validation |
| Copilot marketplace | Copilot surface validator and deterministic Copilot marketplace validation |
| IDE adapter | materialize/check parity and affected discovery fixture |
| Upstream adoption | provenance, affected schemas, and regression suite |
| Release/package | complete applicable source-local package gates |

Use judgment when a change spans rows. Full-suite testing is appropriate for
package/release/adoption or broad cross-cutting changes, not as a ritual for
every edit.

Useful commands from the plugin root include:

```text
python -B -m pytest -q tests
python <skill-creator>/scripts/quick_validate.py skills/agent-plugins-authoring
python <plugin-creator>/scripts/validate_plugin.py .
python skills/agent-plugins-authoring/scripts/validate_agent_plugin.py . --format json
python skills/agent-plugins-authoring/scripts/validate_skill_design.py . --format json
python skills/agent-plugins-authoring/scripts/validate_copilot_surface.py . --require-marketplace --format json
python skills/agent-plugins-authoring/scripts/materialize_ide_adapter.py . --check --format json
python skills/agent-plugins-authoring/scripts/reconcile_surfaces.py . --format json
python skills/agent-plugins-authoring/scripts/build_package.py . --output package.zip --format json
```
