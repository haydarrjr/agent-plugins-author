# Codex adapter contract

## Scope

This reference covers the native Codex adapter and Codex marketplace only.
GitHub Copilot in VS Code/CLI/app consumes Agent Plugins 1.0 directly; use
[copilot-agent-plugins.md](copilot-agent-plugins.md) for that surface. Evidence
from one client must not be upgraded into evidence for another.

## Scaffold

Use the bundled `plugin-creator` skill and scripts for the native adapter:

```text
$CODEX_HOME/skills/.system/plugin-creator/scripts/create_basic_plugin.py
$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py
$CODEX_HOME/skills/.system/plugin-creator/scripts/read_marketplace_name.py
$CODEX_HOME/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py
```

When `CODEX_HOME` is unset, resolve the same helpers under the platform home
directory's `.codex/skills/.system/plugin-creator/scripts/` path.

The native manifest is `.codex-plugin/plugin.json` and points to
`./skills/`. It is an adapter, not the portable authority.

The default personal marketplace is resolved as `$HOME/.agents/plugins/marketplace.json`
(on Windows, use the platform home directory), never as a user-specific
hard-coded path.

Host helper resolution order is: explicit CLI/config override, `$CODEX_HOME`,
the platform home `.codex` directory, then capability discovery. If no helper
is available, report `UNVERIFIED`.

Its local source path is `./plugins/<plugin-name>`. Do not hand-edit this
file. Use creator helpers and preserve existing ordering/display metadata.

For repository distribution, keep the Codex repo catalog at:

```text
<repository-root>/.agents/plugins/marketplace.json
```

When the plugin is at the repository root, the catalog may use a Git-backed
root entry. This catalog is separate from the personal marketplace, GitHub
Copilot's `.github/plugin/marketplace.json`, and the OpenAI public directory.

## Parity

Reconciliation must prove that portable and native manifests agree on plugin
identity and intended version while allowing native-only interface metadata.
Portable fields must not be polluted with Codex-only fields.

## Marketplace modes

Use `development` mode for a moving `main` ref. Use `release` mode for a tag
or immutable commit SHA. The deterministic Codex marketplace renderer rejects
a release catalog that points at `main`. A catalog is source evidence, not
installation, host readback, publication, or live-use evidence.

## Existing-plugin updates

For an explicitly requested local Codex update, preserve marketplace identity,
use the creator cachebuster when the native package requires it, and reinstall
only when installation is in scope. Exercise host behavior in a fresh
conversation when host testing is requested and record that readback
separately. For GitHub/workspace distribution, update source and verify CI
without mutating a personal marketplace or local plugin cache.

Never infer installation, enablement, publication, or live state from source
validation or marketplace configuration alone.

## v1 boundary

This plugin is skills-only. Do not create `.mcp.json`, `.app.json`, hooks, or
client-specific credentials unless a later request explicitly expands scope.
An optional portable `mcp.json` may be translated to a credential-free
`.codex/config.toml.example` only for a package that explicitly includes MCP.
