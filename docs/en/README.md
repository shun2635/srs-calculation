# Guide for LAMSADE Collaborators

This guide is the shortest path to understanding the repository without starting from the implementation details.

Maintenance note: this document should stay aligned in content with [`../ja/README.md`](../ja/README.md). When onboarding content or navigation changes here, review the Japanese version as well.

Structure note: the `en/` and `ja/` documentation trees should stay aligned in structure. When a section is added, moved, or removed in one tree, mirror the change in the other tree.

## What this repository is

- A research codebase for cooperative-game-based ranking rules
- A place for both synthetic experiments and real-data analysis
- The supported Poetry CLI is now published from the repository root
- `real-gen` is already wired to the `src` implementation from that root project
- Module-entry points for migrated slices also exist in [`../../src/`](../../src/)
- Documented at the top level so collaborators can navigate the project more easily

## Main capabilities

### Synthetic experiments

The root CLI contract currently supports the following synthetic workflow through `srs-game-gen`:

- generate complete coalition game tables
- compute ranking columns for multiple rules
- create ranking figures

Axiom evaluation and some aggregate synthetic commands are not yet part of the supported root CLI surface.

### Real-data experiments

The `real-gen` CLI can:

- import feature-mask performance tables as coalition-game data
- reuse the migrated ranking rules exposed from `src`
- generate figures and heatmaps for each dataset

## Recommended reading order

1. [`../../README.md`](../../README.md)
2. [`architecture.md`](architecture.md)
3. [`architecture/README.md`](architecture/README.md)
4. [`../../src/README.md`](../../src/README.md)
5. [`research-workflow.md`](research-workflow.md)
6. [`../../legacy/docs/README.md`](../../legacy/docs/README.md) only when detailed rule descriptions are needed

## Where to look depending on your question

### I want the code map

Read [`architecture.md`](architecture.md), then inspect:

- [`architecture/module-boundaries.md`](architecture/module-boundaries.md)
- [`../../src/README.md`](../../src/README.md)
- [`../../src/`](../../src/) as the default implementation target
- [`../../legacy/src/gamegen`](../../legacy/src/gamegen) and [`../../legacy/src/realgen`](../../legacy/src/realgen) only when historical implementation detail is required

### I want the mathematical rule descriptions

Read:

- [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

### I want to reproduce the experiment flow

Read:

- [`research-workflow.md`](research-workflow.md)
- the root CLI contract in [`../../README.md`](../../README.md)

## Setup

```bash
poetry install
poetry run real-gen --help
poetry run srs-game-gen --help
poetry run srs-test
```

## Minimal examples

```bash
# Synthetic workflow
poetry run srs-game-gen gen-games -p 4 -c 100 --out outputs
poetry run srs-game-gen apply-rules -p 4 --out outputs
poetry run srs-game-gen make-figures --rankings-dir outputs/rankings --out outputs

# Real-data pipeline
mkdir -p inputs/feature_mask_tables/<dataset_id>
poetry run real-gen import-game <dataset_id>
poetry run real-gen apply-rules <dataset_id>
poetry run real-gen make-figures <dataset_id>
```

## Interpretation of the documentation layers

- `docs/en/` and `docs/ja/`: language-specific documentation entry points
- `docs/en/architecture`, `docs/en/development`, `docs/en/adr`, `docs/en/specs`: standards for the new implementation
- `src/`: implementation of record for supported workflows
- `legacy/README.md`: historical CLI reference
- `legacy/docs/`: retained historical technical and mathematical appendices

This split is intentional. Normal collaborator workflows should start from the root CLI and `docs/`, while `legacy/` is retained as a historical archive rather than a primary entry point.
