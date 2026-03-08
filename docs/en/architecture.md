# Architecture Overview

This document explains the current architecture as it exists in the repository today. It is not a target architecture for a future refactor.

For the target architecture of the new implementation under `src/`, read:

- [`architecture/README.md`](architecture/README.md)
- [`architecture/module-boundaries.md`](architecture/module-boundaries.md)
- [`../../src/README.md`](../../src/README.md)

## High-level structure

The repository is effectively centered on a single Python project under [`../../legacy/`](../../legacy/), managed by Poetry.

- [`../../legacy/pyproject.toml`](../../legacy/pyproject.toml): package definition, dependencies, CLI entry points
- [`../../legacy/config.yaml`](../../legacy/config.yaml): default runtime configuration
- [`../../legacy/tests/`](../../legacy/tests/): CLI and behavior regression tests

The code is divided into two main packages.

## Package 1: `gamegen`

Path: [`../../legacy/src/gamegen`](../../legacy/src/gamegen)

Purpose:

- create synthetic cooperative games
- compute ranking values and ranking columns
- run axiom checks
- generate figures and heatmaps

Main subareas:

- [`../../legacy/src/gamegen/commands`](../../legacy/src/gamegen/commands): Click CLI commands
- [`../../legacy/src/gamegen/rules`](../../legacy/src/gamegen/rules): ranking rule implementations
- [`../../legacy/src/gamegen/axioms`](../../legacy/src/gamegen/axioms): axiom-checking logic and summary plots
- [`../../legacy/src/gamegen/io`](../../legacy/src/gamegen/io): CSV path and I/O helpers
- [`../../legacy/src/gamegen/ranking`](../../legacy/src/gamegen/ranking): rule registry

Operational flow:

1. Generate game tables.
2. Apply ranking rules.
3. Check axioms on generated ranking outputs.
4. Produce visual summaries.

## Package 2: `realgen`

Path: [`../../legacy/src/realgen`](../../legacy/src/realgen)

Purpose:

- convert real-data evaluation tables into a coalition-game representation
- reuse `gamegen` ranking logic
- create dataset-level visualizations

Main subareas:

- [`../../legacy/src/realgen/commands`](../../legacy/src/realgen/commands): real-data CLI commands
- [`../../legacy/src/realgen/rules`](../../legacy/src/realgen/rules): rules specific to observed data handling
- [`../../legacy/src/realgen/io`](../../legacy/src/realgen/io): feature-label helpers
- [`../../legacy/src/realgen/datasets.py`](../../legacy/src/realgen/datasets.py): dataset metadata and dispatch

Operational flow:

1. Import a dataset from raw CSV plus schema metadata.
2. Normalize it to the internal game-table format.
3. Apply ranking rules.
4. Produce figures and heatmaps.

## Data and outputs

Inputs:

- [`../../legacy/inputs/`](../../legacy/inputs/)
- especially [`../../legacy/inputs/feature_mask_tables/`](../../legacy/inputs/feature_mask_tables/)

Outputs:

- [`../../legacy/outputs/games/`](../../legacy/outputs/games/)
- [`../../legacy/outputs/rankings/`](../../legacy/outputs/rankings/)
- [`../../legacy/outputs/axiom/`](../../legacy/outputs/axiom/)
- [`../../legacy/outputs/heatmaps/`](../../legacy/outputs/heatmaps/)
- [`../../legacy/outputs/real/`](../../legacy/outputs/real/)

## Documentation layers

There are now two documentation layers.

- [`./`](./): English collaboration-facing overview documents
- [`../ja/`](../ja/): Japanese collaboration-facing overview documents
- [`../../legacy/docs/`](../../legacy/docs/): detailed design notes, ranking-rule explanations, and axiom definitions

Use the top-level docs first, then move to the legacy docs when you need precise implementation detail.

## Practical extension points

If you need to extend the codebase, these are the most likely entry points.

- Add or modify ranking rules in [`../../legacy/src/gamegen/rules`](../../legacy/src/gamegen/rules)
- Register new ranking behavior via [`../../legacy/src/gamegen/ranking/registry.py`](../../legacy/src/gamegen/ranking/registry.py)
- Add new CLI operations under [`../../legacy/src/gamegen/commands`](../../legacy/src/gamegen/commands) or [`../../legacy/src/realgen/commands`](../../legacy/src/realgen/commands)
- Describe mathematical behavior in [`../../legacy/docs/ranking/`](../../legacy/docs/ranking/)
- Document axiom logic in [`../../legacy/docs/axioms/`](../../legacy/docs/axioms/)

## Current limitation

The repository is still organized around the historical `legacy/` codebase. The new documentation improves readability for collaborators, but it does not yet change the code layout itself.
