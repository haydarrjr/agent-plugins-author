# Quality gates

Run gates in this order and keep their evidence separate:

1. **Portable structure** — root manifest, schema version, skill discovery,
   frontmatter, containment, and forbidden native fields.
2. **Security** — secrets, private keys, credential-bearing environment or
   headers, unsafe filenames, links, and path traversal.
3. **Upstream provenance** — exact commit/tree, schema hashes, adopted versus
   observed baseline, and published/draft status.
4. **Codex adapter** — native manifest shape, parity, and `plugin-creator`
   validation.
5. **Behavior** — pressure scenarios and representative authoring requests.
6. **Determinism** — repeated validation/report generation produces stable
   content except for explicitly transient timestamps.
7. **Optional host operations** — marketplace, installation, and host readback
   are run only when explicitly requested.

Every gate returns one of `PASS`, `FAIL`, `UNVERIFIED`, or `NOT_RUN`. A
failure or unknown source must not be upgraded by a later gate.

Recommended commands from the plugin root:

```text
python -m pytest -q tests
python <skill-creator>/scripts/quick_validate.py skills/agent-plugins-authoring
python <plugin-creator>/scripts/validate_plugin.py .
python skills/agent-plugins-authoring/scripts/validate_agent_plugin.py . --format json
python skills/agent-plugins-authoring/scripts/reconcile_manifests.py . --format json
```
