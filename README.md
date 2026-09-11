# Agent Plugins Author

Agent Plugins Author is a skills-only plugin for creating, auditing, updating,
and packaging portable Agent Plugins with separate Codex plugin and Codex IDE
skill surfaces.

## Source and distribution surfaces

- `plugin.json` — portable Agent Plugins 1.0.0 manifest and authority.
- `.codex-plugin/plugin.json` — Codex plugin adapter.
- `skills/agent-plugins-authoring/` — canonical authoring skill, references,
  and deterministic helpers.
- `.agents/skills/` — generated Codex IDE standalone-skill adapter; never edit
  this surface by hand.
- `.agents/plugins/marketplace.json` — repo-scoped GitHub marketplace catalog.
- `provenance/` — upstream and adapter identity records.
- `tests/` — contract, security, design, routing, parity, and determinism tests.

The portable package remains skills-only. It does not bundle an MCP server,
credentials, hooks, or client-specific connection files. If a future package
explicitly adds portable `mcp.json`, the host adapter may render a
credential-free `.codex/config.toml.example`.

## Install from GitHub

Add this repository as a Codex marketplace source:

```text
codex plugin marketplace add haydarrjr/agent-plugins-author --ref main
codex plugin marketplace list
```

Then refresh the Plugins Directory in the ChatGPT desktop app, select **Agent
Plugins Author**, install it, and test it in a new conversation. Codex CLI can
also browse configured marketplaces. The Codex IDE extension does not install
plugins; use the generated `.agents/skills/` surface there.

For a reproducible release, render the repo catalog with an immutable tag or
commit instead of the moving `main` development ref:

```text
python skills/agent-plugins-authoring/scripts/render_marketplace.py . --mode release --ref <tag-or-commit>
```

## Authoring policy

The published Agent Plugins 1.0.0 contract is the production target. Agent
Plugins 1.1.0 is observed as a working-draft probe only. Refresh is read-only
and reports a diff; adopting a new upstream baseline is explicit and preserves
the last-known-good snapshot on failure.

Descriptions are concise and narrowly triggered. The root skill is a small
router; detailed contracts are conditionally disclosed through references and
deterministic scripts. Validation, installation, host readback, publication,
and live status are independent evidence layers.

## Local validation

From the repository root:

```text
python -B -m pytest -q tests
python skills/agent-plugins-authoring/scripts/validate_agent_plugin.py . --format json
python skills/agent-plugins-authoring/scripts/validate_skill_design.py . --format json
python skills/agent-plugins-authoring/scripts/materialize_ide_adapter.py . --check --format json
python skills/agent-plugins-authoring/scripts/reconcile_surfaces.py . --format json
python skills/agent-plugins-authoring/scripts/build_report.py . --format json
```

The package gate also runs the deterministic archive builder and verifies that
repeated output has the same bytes. Host installation and readback are not
performed by the source-local validation suite.

## Public-directory boundary

This repository is ready for GitHub/repo-marketplace distribution and for a
skills-only public submission package. A GitHub repository does not by itself
publish a plugin to OpenAI's Universal Plugins Directory. That publication
requires the OpenAI submission portal, verified developer identity, review,
and an explicit publish action.

## License

MIT. See [LICENSE](LICENSE).
