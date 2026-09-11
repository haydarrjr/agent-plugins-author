# Astra-aware skill authoring

## 1. Scope

Use this reference when creating, updating, or auditing skill metadata and
root instructions. It describes routing quality, context economy, and
progressive disclosure; it does not replace the portable or host contracts.

## 2. Description design

Lead with the job, then name the narrow trigger scope. Keep descriptions short
enough to survive initial index shortening. `Use when ...` is a valid pattern,
not a required syntax. Avoid broad phrases such as “working with databases”
when the skill is only for migrations.

## 3. Progressive disclosure

Keep the root `SKILL.md` a router: enough context to choose the workflow,
important boundaries, and links to conditional references. Put detailed
contracts, examples, and deterministic mechanics in `references/` or
`scripts/`.

## 4. Root SKILL.md design

Describe the goal, domain knowledge, important authority boundary, useful
resources, and completion condition. Do not duplicate every reference in the
root document.

## 5. References versus scripts

Use a reference for knowledge that should be read selectively. Use a script for
deterministic parsing, validation, materialization, reconciliation, or package
construction. Scripts must be safe to rerun and must not write credentials.

## 6. Decision boundaries

Keep destructive actions, upstream adoption, installation, publication, and
live readback explicit. A validator may report `PASS` only for its own gate;
it must not upgrade installation, host, or live evidence.

## 7. Persistence and completion

For implementation and update requests, continue through the requested change,
affected validation, package-caused corrections, and final reconciliation.
Stop only for a real authority, credential, destructive, or unresolved-source
boundary, and report that boundary explicitly.

## 8. AGENTS.md policy

Do not generate `AGENTS.md` as a copy of a skill workflow. Add it only when a
repository-wide invariant genuinely needs persistent context, and keep it
short enough not to load architecture material on every task.

## 9. Targeted verification

Use `validate_skill_design.py` for metadata, disclosure, recipes, collisions,
and context budget. Pair it with trigger fixtures covering positive, negative,
ambiguous, and competing-skill prompts. Select the narrowest contract and
behavior checks for the changed surface; reserve full validation for package or
release gates.

## 10. Trigger and non-trigger evaluation

String similarity is only a candidate signal. Review collisions semantically,
and preserve an explicit negative set for prompts that should remain outside
the skill. A routing fixture is evidence about the description, not proof of
host behavior or model-wide quality.
