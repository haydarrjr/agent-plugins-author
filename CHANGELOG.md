# Changelog

## 0.3.0 — 2026-09-13

- Align skill and repository prompt design with OpenAI's GPT-6 Astra guidance:
  shorter routing metadata, contextual references, less procedural noise, safe
  local autonomy, and explicit completion boundaries.
- Add native Agent Plugins 1.0 compatibility guidance and validation for GitHub
  Copilot in VS Code, Copilot CLI, and Copilot app.
- Add deterministic `.github/plugin/marketplace.json` generation and validation
  while keeping the existing Codex marketplace as a separate client surface.
- Add `com.github.copilot/` namespace rules for optional Copilot-only agents,
  commands, rules, hooks, and LSP components.
- Extend evidence reconciliation, CI, tests, and provenance to cover the Copilot
  surface without inferring host installation or runtime behavior.

## 0.2.0

- Add Astra-aware skill design linting and trigger-routing fixtures.
- Add deterministic Codex IDE skill materialization and surface reconciliation.
- Separate v2 evidence for portable, Codex plugin, IDE, marketplace, MCP host,
  installation, host readback, and live status.
- Add development/release marketplace rendering and deterministic package build.
- Remove machine-specific host paths and keep optional MCP configuration
  credential-free.

## 0.1.1 — 2026-09-09

- Added the original Aether Scribe mythic guardian icon as a self-contained SVG.
- Added icon provenance and native Codex presentation metadata.

## 0.1.0 — 2026-09-09

- Added portable Agent Plugins 1.0.0 authoring workflow.
- Added Codex compatibility adapter and repo-scoped GitHub marketplace catalog.
- Added published/draft upstream classification and explicit adoption flow.
- Added security, provenance, determinism, and pressure-test gates.
