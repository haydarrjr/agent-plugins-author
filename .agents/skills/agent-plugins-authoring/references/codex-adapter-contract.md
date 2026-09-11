# Codex adapter contract

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
file. Use the creator helpers and preserve existing ordering/display metadata.

For repository distribution, keep a repo-scoped catalog at:

```text
<repository-root>/.agents/plugins/marketplace.json
```

When the plugin is at the repository root, the catalog may use a Git-backed
root entry:

```json
{
  "name": "agent-plugins-author",
  "plugins": [
    {
      "name": "agent-plugins-author",
      "source": {
        "source": "url",
        "url": "https://github.com/haydarrjr/agent-plugins-author.git",
        "ref": "main"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

This catalog is separate from the personal marketplace and from the public
Universal Plugins Directory. A GitHub repository and repo marketplace can be
ready for installation without implying OpenAI public-directory publication.

## Parity

Reconciliation must prove that portable and native manifests agree on plugin
identity and intended version while allowing native-only interface metadata.
Portable fields must not be polluted with Codex-only fields.

## Marketplace modes

Use `development` mode for a moving `main` ref. Use `release` mode for a tag
or immutable commit SHA. The deterministic marketplace renderer must reject a
release catalog that points at `main`. A marketplace catalog is not evidence
of IDE plugin support, installation, host readback, publication, or live use.

## Existing-plugin updates

For an explicitly requested local update:

1. Read and validate the marketplace name.
2. Run the creator cachebuster helper when a native package update requires it.
3. Reinstall only when local installation is explicitly in scope.
4. Start a new conversation/thread for host testing.
5. Test representative requests and record host readback separately.

For a GitHub/workspace distribution request, change source, commit, push, and
read GitHub CI. Do not mutate a personal marketplace or local plugin cache.

Never infer installation, enablement, publication, or live state from source
validation or marketplace configuration alone.

## v1 boundary

This plugin is skills-only. Do not create `.mcp.json`, `.app.json`, hooks, or
client-specific credentials unless a later request explicitly expands scope.
An optional portable `mcp.json` may be translated to a credential-free
`.codex/config.toml.example` only for a package that explicitly includes MCP.
