# `agent-plugins-author-report.v1`

Reports are value-free, deterministic except for an optional observation time,
and must distinguish source evidence from host evidence.

Required top-level fields:

```text
schema_version
mode
status
portable
upstream
codex_adapter
security
marketplace
installation
host_readback
tests
next_action
```

Each scoped object has at least `status` and `checks`. Valid statuses are
`PASS`, `FAIL`, `UNVERIFIED`, and `NOT_RUN`.

The combined `status` is `PASS` only when required source-local gates pass.
Marketplace, installation, host readback, client acceptance, publication, and
live status remain independent fields and are never inferred.
