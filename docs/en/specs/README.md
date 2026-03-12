# Specifications

This directory stores feature and workflow specifications for substantial changes.

## When to write a spec

Write a spec when the change:

- spans multiple modules
- affects user-visible behavior
- changes data contracts
- requires phased migration
- needs agreement before implementation starts

## Naming convention

Use descriptive file names such as:

- `synthetic-pipeline-v2.md`
- `real-data-import-service.md`
- `cli-unification.md`

## Review expectation

Specs should be reviewed before implementation begins for larger changes. The goal is to reduce ambiguity across collaborators, not to create bureaucracy for trivial edits.

## Current specs

- [`ranking-domain-foundation.md`](ranking-domain-foundation.md): first concrete migration slice for the new `src/` implementation
- [`legacy-ranking-and-axiom-completion.md`](legacy-ranking-and-axiom-completion.md): expands the migrated `src/` core to the full legacy synthetic rule family plus axiom evaluators
- [`synthetic-game-methodology.md`](synthetic-game-methodology.md): current `srs-game-gen` simulation methodology and paper-facing wording
- [`tu-constrained-synthetic-workflow.md`](tu-constrained-synthetic-workflow.md): adds constrained synthetic generation and a constraint-set aware comparison workflow

## Template

Start from [`TEMPLATE.md`](TEMPLATE.md).
