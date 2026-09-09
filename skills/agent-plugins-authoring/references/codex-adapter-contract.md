# Codex adapter contract

## Scaffold

Use the bundled `plugin-creator` skill and scripts for the native adapter:

```text
C:\Users\onder\.codex\skills\.system\plugin-creator\scripts\create_basic_plugin.py
C:\Users\onder\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py
C:\Users\onder\.codex\skills\.system\plugin-creator\scripts\read_marketplace_name.py
C:\Users\onder\.codex\skills\.system\plugin-creator\scripts\update_plugin_cachebuster.py
```

The native manifest is `.codex-plugin/plugin.json` and points to
`./skills/`. It is an adapter, not the portable authority.

The default personal marketplace is:

```text
C:\Users\onder\.agents\plugins\marketplace.json
```

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

## Existing-plugin updates

For a local update:

1. Read and validate the marketplace name.
2. Run the creator cachebuster helper.
3. Reinstall through the documented CLI flow.
4. Start a new conversation/thread.
5. Test representative requests and record host readback separately.

Never infer installation, enablement, publication, or live state from source
validation or marketplace configuration alone.

## v1 boundary

This plugin is skills-only. Do not create `.mcp.json`, `.app.json`, hooks, or
client-specific credentials unless a later request explicitly expands scope.
