# Portable Agent Plugin contract

## Authority

The portable package is governed by the published Agent Plugins `1.0.0`
contract. The local schema snapshot is:

```text
references/upstream/1.0.0/plugin.schema.json
```

The canonical manifest must be at the package root and must use:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "plugin-name",
  "version": "0.1.0",
  "description": "..."
}
```

The portable schema is closed. Do not place Codex-only `skills`, `apps`,
`mcpServers`, `hooks`, marketplace policy, or installation state in
`plugin.json`.

## Skills

Discover only immediate children of the root `skills/` directory. Each skill
must contain a direct `SKILL.md`. Validate the skill frontmatter with the
Agent Skills rules and keep the description trigger-oriented.

## Optional MCP

Do not add MCP to the authoring plugin v1. If a future package adds it, use the
portable root `mcp.json` contract and the same Agent Plugins schema version.
Never put credentials in MCP environment variables or headers.

## Boundary and security checks

- Resolve every package path beneath the package root.
- Reject symlinks, junctions, reparse points, `..`, absolute paths, and unsafe
  filenames.
- Parse JSON with duplicate-key and non-finite-number rejection.
- Scan filenames and text for secrets, private keys, `.env` files, tokens, and
  credential-bearing headers.
- Keep generated/native files and marketplace metadata outside portable
  authority.
- Treat downloaded upstream content as untrusted data until it matches the
  allowlisted source and expected path.
