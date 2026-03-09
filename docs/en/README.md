# Guide for LAMSADE Collaborators

This guide is the shortest path to understanding the repository without starting from the implementation details.

Maintenance note: this document should stay aligned in content with [`../ja/README.md`](../ja/README.md). When onboarding content or navigation changes here, review the Japanese version as well.

Structure note: the `en/` and `ja/` documentation trees should stay aligned in structure. When a section is added, moved, or removed in one tree, mirror the change in the other tree.

## What this repository is

- A research codebase for cooperative-game-based ranking rules
- A place for both synthetic experiments and real-data analysis
- The published Poetry CLI currently lives in [`../../legacy/`](../../legacy/)
- Experimental entry points for migrated slices also exist in [`../../src/`](../../src/)
- Documented at the top level so collaborators can navigate the project more easily

## Main capabilities

### Synthetic experiments

The `game-gen` CLI can:

- generate complete coalition game tables
- compute ranking columns for multiple rules
- check axiom satisfaction in batch
- create heatmaps and summary figures

### Real-data experiments

The `real-gen` CLI can:

- import feature-mask performance tables as coalition-game data
- reuse the ranking rules defined in `gamegen`
- generate figures and heatmaps for each dataset

## Recommended reading order

1. [`../../README.md`](../../README.md)
2. [`architecture.md`](architecture.md)
3. [`architecture/README.md`](architecture/README.md)
4. [`../../src/README.md`](../../src/README.md)
5. [`research-workflow.md`](research-workflow.md)
6. [`../../legacy/docs/README.md`](../../legacy/docs/README.md) when detailed rule descriptions are needed

## Where to look depending on your question

### I want the code map

Read [`architecture.md`](architecture.md), then inspect:

- [`architecture/module-boundaries.md`](architecture/module-boundaries.md)
- [`../../src/README.md`](../../src/README.md)
- [`../../legacy/src/gamegen`](../../legacy/src/gamegen)
- [`../../legacy/src/realgen`](../../legacy/src/realgen)

### I want the mathematical rule descriptions

Read:

- [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

### I want to reproduce the experiment flow

Read:

- [`research-workflow.md`](research-workflow.md)
- [`../../legacy/config.yaml`](../../legacy/config.yaml)

## Setup

```bash
cd legacy
poetry install
poetry run game-gen --help
poetry run real-gen --help
poetry run pytest

# experimental src entry points
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen --help
```

## Minimal examples

```bash
cd legacy

# Synthetic pipeline
poetry run game-gen pipeline -p 4 -c 100 --out outputs

# Real-data pipeline
poetry run real-gen import-game <dataset_id>
poetry run real-gen apply-rules <dataset_id>
```

## Interpretation of the documentation layers

- `docs/en/` and `docs/ja/`: language-specific documentation entry points
- `docs/en/architecture`, `docs/en/development`, `docs/en/adr`, `docs/en/specs`: standards for the new implementation
- `src/`: target source tree for new code
- `legacy/README.md`: CLI usage for the current codebase
- `legacy/docs/`: detailed technical and mathematical appendices

This split is intentional while the repository is still centered on the legacy implementation. The published CLI is still legacy-first, but migrated ranking workflows and real-data import can already be exercised from `src/`.
