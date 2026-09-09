# Contributing

Changes should preserve the separation between the portable manifest and the
Codex adapter.

## Development rules

1. Treat the published Agent Plugins 1.0.0 contract as the production target.
2. Treat working-draft upstream material as probe/report input until explicitly
   adopted.
3. Do not place Codex-native `mcpServers`, `apps`, hooks, or marketplace fields
   in the portable root manifest.
4. Do not commit credentials, private keys, `.env` files, guessed application
   IDs, generated caches, or machine-local marketplace state.
5. Keep upstream provenance bound to the exact commit, tree, and file hashes.
6. Run the full validation suite before opening a pull request.

## Validation commands

```text
python -B -m pytest -q tests
python skills/agent-plugins-authoring/scripts/validate_agent_plugin.py . --format json
python skills/agent-plugins-authoring/scripts/reconcile_manifests.py . --format json
python skills/agent-plugins-authoring/scripts/refresh_upstream.py --offline --format json
```

Online refresh is allowlisted and read-only. Use `adopt_upstream.py` only when
the requested upstream version is explicitly approved for adoption.
