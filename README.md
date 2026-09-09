# Agent Plugins Author

Agent Plugins Author is a skills-only plugin for creating, auditing, porting,
refreshing, and packaging portable Agent Plugins with a Codex compatibility
adapter.

It is designed for authors who need a clean boundary between:

- the portable Agent Plugins contract;
- the Codex-native `.codex-plugin/plugin.json` adapter;
- upstream published and working-draft specifications;
- provenance, security, and deterministic validation; and
- marketplace configuration, installation, and host read-back evidence.

## What is included

- `plugin.json` — portable Agent Plugins 1.0.0 manifest.
- `.codex-plugin/plugin.json` — Codex compatibility adapter scaffolded in the
  `plugin-creator` style.
- `assets/icon.svg` — original Aether Scribe mythic guardian mark used by the
  Codex install surfaces.
- `skills/agent-plugins-authoring/` — the authoring workflow and its references.
- `scripts/` — deterministic refresh, adoption, validation, reconciliation, and
  report helpers inside the skill package.
- `.agents/plugins/marketplace.json` — a repo marketplace catalog that loads the
  plugin from this public GitHub repository root.
- `tests/` — contract, security, provenance, determinism, and pressure tests.

The v1 package is skills-only. It intentionally does not bundle an MCP server,
credentials, hooks, or client-specific connection files.

## Install from GitHub

Add this repository as a Codex marketplace source:

```text
codex plugin marketplace add haydarrjr/agent-plugins-author --ref main
codex plugin marketplace list
```

Then refresh the Plugins Directory in the ChatGPT desktop app, select **Agent
Plugins Author**, install it, and test it in a new conversation. For a
reproducible review, pin the marketplace source to an exact Git ref or commit
instead of `main`.

The repository catalog uses a Git-backed root entry, so the package can remain
at the repository root while the catalog stays at the documented
`.agents/plugins/marketplace.json` location.

## Authoring policy

The default production target is the published Agent Plugins 1.0.0 contract.
Agent Plugins 1.1.0 is observed as a working-draft probe only. A refresh is
read-only and reports changes; adopting a new upstream baseline is explicit and
preserves the last known-good snapshot on failure.

The skill never treats validation as proof of installation, host read-back,
publication, or live runtime state. Those are separate gates with separate
evidence.

## Local validation

From the repository root:

```text
python -B -m pytest -q tests
python <skill-creator>/scripts/quick_validate.py skills/agent-plugins-authoring
python <plugin-creator>/scripts/validate_plugin.py .
python skills/agent-plugins-authoring/scripts/validate_agent_plugin.py . --format json
python skills/agent-plugins-authoring/scripts/reconcile_manifests.py . --format json
python skills/agent-plugins-authoring/scripts/refresh_upstream.py --offline --format json
```

The GitHub Actions workflow runs the repository-independent checks. The local
`plugin-creator` validator is additionally run on hosts where that Codex skill
is installed.

## Public-directory boundary

This repository is ready for GitHub/repo-marketplace distribution and for a
skills-only public submission package. A GitHub repository does not by itself
publish a plugin to OpenAI's Universal Plugins Directory. That publication
requires the OpenAI submission portal, a verified developer identity, review,
and an explicit publish action.

## License

MIT. See [LICENSE](LICENSE).
