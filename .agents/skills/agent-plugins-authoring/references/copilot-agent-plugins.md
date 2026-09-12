# GitHub Copilot and VS Code Agent Plugins

## Scope and authority

Use this reference when a plugin must run in GitHub Copilot in VS Code,
Copilot CLI, or Copilot app, or when it must be distributed through a Copilot
plugin marketplace. GitHub's current Agent Plugins 1.0 documentation is the
client authority for this surface:

https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference

Keep the portable Agent Plugins contract authoritative for portable files.

## Agent Plugins 1.0 core

GitHub Copilot recognizes the exact Agent Plugins 1.0 `$schema` at the root
`plugin.json`. Portable components remain fixed:

- `skills/<skill-name>/SKILL.md` for skills; each skill is an immediate child.
- `mcp.json` at the root when the package intentionally includes portable MCP.

Do not add legacy component-path fields such as `agents`, `skills`, `hooks`,
`mcpServers`, or `lspServers` to an Agent Plugins 1.0 `plugin.json`.

## Copilot-specific components

Agent Plugins 1.0 does not make agents, commands, rules, hooks, or LSP servers
portable. Add them only when the requested plugin actually needs them. Copilot
uses the `com.github.copilot` namespace:

```text
com.github.copilot/agents/
com.github.copilot/commands/
com.github.copilot/rules/
com.github.copilot/hooks/hooks.json
com.github.copilot/lsp.json
```

Client-specific manifest data belongs under
`extensions["com.github.copilot"]`. Do not leak Copilot-only fields into the
portable schema. Other Agent Plugins clients may ignore this namespace.

## Marketplace distribution

For a repository marketplace, prefer:

```text
.github/plugin/marketplace.json
```

A Copilot marketplace requires top-level `name`, `owner`, and `plugins`. Each
plugin entry requires `name` and `source`. When the marketplace and plugin live
in the same repository and the plugin is at the repository root, `source: "."`
is the simplest deterministic source; the marketplace registration itself can
be pinned to a branch, tag, or commit when reproducibility is required.

Keep `strict: true` for Agent Plugins 1.0 packages. Marketplace version, when
present, should match the plugin manifest. A GitHub or URL source may use a
full 40-character `sha` for immutable installs. Marketplace validity does not
prove installation or runtime discovery.

## VS Code and CLI use

VS Code and Copilot CLI can install Agent Plugins from a marketplace or a
GitHub/Git URL source. Source validation is separate from host acceptance.
When host testing is in scope, record installation, enablement, discovery, and
representative runtime readback as separate evidence rather than inferring it
from CI.

## Authoring completion

For a GitHub Copilot target, validate the portable package and the Copilot
surface. Validate `.github/plugin/marketplace.json` when marketplace
distribution is requested. Add only the client-specific components required by
the request; do not generate placeholder agents, hooks, rules, commands, or
LSP configuration merely to populate the namespace.
