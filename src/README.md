# New Source Tree

This directory contains the in-progress new implementation of the repository.

## Policy

- new production code should be added here by default
- `legacy/` remains the reference implementation until parity is demonstrated
- architecture decisions for this tree are documented in [`../docs/en/architecture/`](../docs/en/architecture/) and mirrored in [`../docs/ja/architecture/`](../docs/ja/architecture/)

## Intended package tree

```text
src/
  srs_calculation/
    domain/
      games/
      ranking/
        rules/
      axioms/
    application/
      ranking/
      game_generation/
      axiom_evaluation/
      dataset_ingestion/
      experiments/
    infrastructure/
      config/
      persistence/
      plotting/
      datasets/
    interfaces/
      cli/
```

## Expected responsibilities

- `domain/`: core ranking, coalition, and axiom logic
- `application/`: workflow orchestration and use cases
- `infrastructure/`: storage, config, plotting, and external adapters
- `interfaces/`: CLI and other entry points

## Naming rules

- prefer feature-oriented package names such as `games/`, `ranking/`, and `axioms/`
- avoid generic buckets such as `models/`, `utils/`, and `common/` in the domain layer
- name application modules after use cases, for example `apply_ranking_rules_to_game_csv.py`
- use snake_case internal rule identifiers such as `ordinal_banzhaf`
- keep output-column naming decisions at the serialization boundary, not in core domain APIs

## Current implemented slice

The ranking migration slice currently includes:

- domain models and first-batch ranking rules under `domain/games` and `domain/ranking`
- application services for in-memory rule execution and legacy-style game-CSV workflows under `application/ranking`
- persistence adapters for legacy-compatible game CSV and rankings CSV files under `infrastructure/persistence`
- a thin synthetic-game CLI adapter for migrated `apply-rules` and `rank-game` workflows under `interfaces/cli`
- unit, integration, and legacy parity tests under `tests/`

## Experimental CLI

The `src` tree includes an experimental synthetic-game CLI for the migrated ranking slice.

Show the top-level help:

```bash
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen --help
```

Show command-specific help:

```bash
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen apply-rules --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen rank-game --help
```

Current supported commands:

- `apply-rules`: apply migrated rules to a directory of legacy-style game CSV files
- `rank-game`: apply one migrated rule to one legacy-style game CSV file

This CLI is intentionally partial. The full production CLI surface still lives under [`../legacy/`](../legacy/).

## Important rule

Do not copy large `legacy/` modules into this tree unchanged. Port behavior intentionally and document architectural differences when they matter.
