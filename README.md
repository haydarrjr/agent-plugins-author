# Agent Plugins Author

Agent Plugins Author creates, audits, updates, and packages portable Agent
Plugins with Astra-aware skill design and independently verifiable Codex and
GitHub Copilot surfaces.

## Source and distribution surfaces

- `plugin.json` — portable Agent Plugins 1.0 manifest and authority.
- `skills/agent-plugins-authoring/` — canonical authoring skill, references,
  and deterministic helpers.
- `.codex-plugin/plugin.json` — native Codex plugin adapter.
- `.agents/skills/` — generated Codex IDE standalone-skill adapter; never edit
  this surface by hand.
- `.agents/plugins/marketplace.json` — Codex repository marketplace catalog.
- `.github/plugin/marketplace.json` — GitHub Copilot/VS Code marketplace catalog.
- `com.github.copilot/` — optional Copilot-only agents, commands, rules, hooks,
  or LSP components when a target plugin actually needs them; this authoring
  plugin does not add placeholders by default.
- `provenance/` — upstream and adapter identity records.
- `tests/` — contract, security, design, routing, parity, marketplace, and
  determinism tests.

The portable package remains skills-only. It does not bundle an MCP server,
credentials, hooks, or client-specific runtime components. A future target
plugin may add portable `mcp.json` or client-specific namespaces when its
requirements justify them.

## Install with Codex / ChatGPT

Add this repository as a Codex marketplace source:

```text
codex plugin marketplace add haydarrjr/agent-plugins-author --ref main
codex plugin marketplace list
```

Then refresh the Plugins Directory in a supporting ChatGPT/Codex host, select
**Agent Plugins Author**, install it, and record host readback separately from
source validation. The generated `.agents/skills/` surface remains available
for Codex IDE standalone-skill compatibility.

For a reproducible Codex release catalog, render it with an immutable tag or
commit instead of moving `main`:

```text
python skills/agent-plugins-authoring/scripts/render_marketplace.py . --mode release --ref <tag-or-commit>
```

## Install with GitHub Copilot / VS Code

GitHub Copilot in VS Code, Copilot CLI, and Copilot app support Agent Plugins
1.0 directly. Register this repository as a marketplace and install the plugin:

```text
copilot plugin marketplace add haydarrjr/agent-plugins-author
copilot plugin install agent-plugins-author@agent-plugins-author
```

A direct source install can also use the repository itself:

```text
copilot plugin install haydarrjr/agent-plugins-author
```

In VS Code, the same Agent Plugins surface can be installed from a configured
marketplace or from the repository source. Source/CI success does not prove a
specific VS Code or Copilot host has installed, enabled, discovered, or run the
plugin; record those host states independently when host testing is requested.

## Authoring policy

The published Agent Plugins 1.0.0 contract is the production target. Later
drafts are observed without silent adoption. Skill and repository prompt design
follows OpenAI's September 11, 2026 "Rethinking skills and prompts for GPT-6
Astra" guidance: concise routing metadata, progressive disclosure, low
permanent context, real decision boundaries, safe autonomy where evidenced,
and explicit completion boundaries.

GitHub Copilot-specific Agent Plugins 1.0 components use the
`com.github.copilot/` namespace. Portable skills and MCP stay client-neutral.
Codex and Copilot marketplaces are validated independently, and neither is
proof of host installation or live behavior.

## Local validation

From the repository root:

```text
python -B -m pytest -q tests
python skills/agent-plugins-authoring/scripts/validate_agent_plugin.py . --format json
python skills/agent-plugins-authoring/scripts/validate_skill_design.py . --format json
python skills/agent-plugins-authoring/scripts/validate_copilot_surface.py . --require-marketplace --format json
python skills/agent-plugins-authoring/scripts/materialize_ide_adapter.py . --check --format json
python skills/agent-plugins-authoring/scripts/reconcile_surfaces.py . --format json
python skills/agent-plugins-authoring/scripts/render_copilot_marketplace.py . --check --format json
python skills/agent-plugins-authoring/scripts/build_report.py . --format json
```

The package gate also builds the deterministic archive twice and compares the
bytes. Repository-local tests and validators do not install, publish, or mutate
a live host.

## Public-directory boundary

A GitHub repository or marketplace does not by itself publish a plugin to an
OpenAI public directory or a GitHub first-party marketplace. Those publication
steps remain explicit external actions with their own review and authority.

## License

MIT. See [LICENSE](LICENSE).
