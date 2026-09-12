# `agent-plugins-author-report.v2`

Reports are value-free, deterministic except for an optional observation time,
and distinguish source evidence from host evidence.

Required top-level fields:

```text
schema_version
mode
status
portable
skill_design
security
upstream
codex_plugin_adapter
codex_ide_adapter
github_copilot
marketplace
mcp_host_config
tests
plugin_installation
ide_skill_discovery
host_readback
live_status
next_action
```

Each scoped object has at least `status` and `checks` or an equivalent scoped
evidence payload. Valid statuses are `PASS`, `FAIL`, `UNVERIFIED`, and
`NOT_RUN`.

The combined `status` is `PASS` only when required source-local gates pass and
the adopted upstream snapshot is locally verifiable. `UNVERIFIED` is used for
an unavailable or conflicting source capability. Installation, host
discovery, host readback, client acceptance, publication, and live status are
never inferred from source validation.

`codex_plugin_adapter=PASS` covers the native Codex manifest.
`codex_ide_adapter=PASS` covers generated standalone-skill parity.
`github_copilot=PASS` covers Agent Plugins 1.0 Copilot source semantics and the
checked-in `.github/plugin/marketplace.json`; it does not prove a VS Code or
Copilot host installed or exercised the plugin. `marketplace` remains the
Codex repo-catalog evidence for backward compatibility. `mcp_host_config` is
`NOT_RUN` when the package has no portable `mcp.json`.
