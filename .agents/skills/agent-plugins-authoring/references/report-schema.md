# `agent-plugins-author-report.v2`

Reports are value-free, deterministic except for an optional observation time,
and must distinguish source evidence from host evidence.

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
marketplace
mcp_host_config
tests
plugin_installation
ide_skill_discovery
host_readback
live_status
next_action
```

Each scoped object has at least `status` and `checks`. Valid statuses are
`PASS`, `FAIL`, `UNVERIFIED`, and `NOT_RUN`.

The combined `status` is `PASS` only when required source-local gates pass and
the adopted upstream snapshot is locally verifiable. `UNVERIFIED` is used for
an unavailable or conflicting source capability. Marketplace, installation,
IDE host discovery, host readback, client acceptance, publication, and live
status remain independent fields and are never inferred.

`codex_plugin_adapter=PASS` covers the native manifest only. A separate
`codex_ide_adapter=PASS` covers generated source parity only. Neither proves
installation or host behavior. `mcp_host_config=NOT_RUN` is explicit when the
package has no portable `mcp.json`.
