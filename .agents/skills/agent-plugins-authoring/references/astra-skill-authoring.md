# Astra-aware skill and prompt authoring

## Scope and authority

Use this reference when creating, updating, or auditing skill metadata, root
instructions, or repository-wide agent guidance. It implements the principles
from OpenAI's September 11, 2026 guidance, "Rethinking skills and prompts for
GPT-6 Astra":

https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

This reference does not replace portable plugin, security, or host contracts.

## Descriptions and routing

Lead with the job and name the narrow trigger scope. Keep descriptions short
enough to survive index shortening while retaining the terms that distinguish
the skill from competing skills. `Use when ...` is valid but not required.
Evaluate positive, negative, ambiguous, and competing-skill prompts; lexical
similarity is only a routing signal, not proof of host behavior.

## Progressive disclosure

Keep root `SKILL.md` files as small routers: goal, authority boundaries,
completion condition, and contextual links. Put specialized contracts and
examples in `references/`; put deterministic parsing, validation,
materialization, reconciliation, or packaging in `scripts/`. When a task spans
surfaces, consult the references that are actually relevant rather than
artificially limiting the model to one document.

## Replace recipes with outcomes

Do not encode generic competent-engineer behavior or long itineraries merely
to control a capable model. Prefer desired outcomes, repository-specific
constraints, decision boundaries, and relevant references. Keep prescriptive
steps only when their order is itself a project invariant or protects a real
security, data, release, or irreversible-operation boundary.

## AGENTS.md migration

Treat `AGENTS.md` as broadly loaded context. Before keeping an instruction,
ask whether it needs to be present on every task in that scope. Replace blanket
reading requirements with contextual pointers, remove duplicated or obvious
engineering advice, and move narrow workflows into scoped guidance or skills.
Do not generate `AGENTS.md` as a copy of a skill workflow.

Preserve genuine institutional knowledge: architecture constraints, unusual
build or test commands, generated-code rules, dependency policy, formatting
that tooling cannot enforce, deployment restrictions, security boundaries,
directory ownership, project terminology, and irreversible-operation rules.
The target is lower prompting noise, not the shortest possible file.

## Decision boundaries and safe autonomy

Keep explicit approval or stop boundaries for destructive operations,
production changes, secrets, security-sensitive actions, irreversible
migrations, external side effects, upstream adoption, installation,
publication, and live readback. Do not preserve approval barriers that exist
only because older models were more aggressive.

Grant safe autonomy only when the repository actually supports the claim. For
this plugin repository, source-local tests and validators do not install,
publish, or mutate a live host, so affected checks may run and package-caused
failures may be corrected without per-step approval. Do not generalize that
statement to an arbitrary target repository without evidence.

## Completion and persistence

Define the completion boundary before implementation. For predictable safe
workflows, continue through implementation, relevant validation, correction of
issues introduced by the change, and final reconciliation. Stop when the
requested behavior works and relevant checks pass, or when a real authority or
external decision is required.

## Verification economy

Select verification by the affected surface. Applicable contract,
provenance, and security boundaries remain mandatory; test ordering itself is
not a ritual unless the repository makes it one. Reserve broad or full-suite
validation for cross-cutting, package, release, or upstream-adoption gates.
Avoid duplicating the same rule in `SKILL.md`, references, project docs, and
task prompts; keep it at the narrowest useful scope.
