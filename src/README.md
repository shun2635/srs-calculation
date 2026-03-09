# New Source Tree

This directory contains the in-progress new implementation of the repository.

## Policy

- new production code should be added here by default
- `legacy/` remains the reference implementation until parity is demonstrated
- the repository root Poetry project publishes `real-gen` from this tree
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
- application services for in-memory rule execution and compatibility-format game-CSV workflows under `application/ranking`
- persistence adapters for compatibility-format game CSV and rankings CSV files under `infrastructure/persistence`
- a dataset-scoped real-data ranking workflow under `application/ranking/apply_ranking_rules_to_real_dataset.py`
- a dataset-ingestion workflow for feature-mask tables under `application/dataset_ingestion/import_feature_mask_table.py`
- real-data plotting workflows, including canonical and extra figures, under `application/experiments/run_real_data_experiment.py`
- synthetic ranking-figure workflows under `application/experiments/run_synthetic_experiment.py`
- thin CLI adapters for migrated `game-gen` and partial `real-gen` workflows under `interfaces/cli`
- unit, integration, and legacy parity tests under `tests/`

## CLI

The `src` tree includes the published root CLI surface. The authoritative script names are stable:

- `real-gen`
- `srs-game-gen`
- `srs-test`

The repository root also publishes:

```bash
poetry run real-gen --help
poetry run srs-game-gen --help
poetry run srs-test
```

Show the top-level help:

```bash
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen --help
```

Show command-specific help:

```bash
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen make-figures --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen apply-rules --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen rank-game --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen import-game --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen apply-rules --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen make-figures --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen feature-rule-heatmap --help
```

Run the root test suite through Poetry:

```bash
poetry run srs-test
poetry run srs-test tests/unit -q
```

Current supported root commands:

- `srs-game-gen gen-games`: generate complete synthetic game CSV files under `outputs/games/nN/`
- `srs-game-gen make-figures`: render compatibility-format PNG figures from synthetic rankings CSV files
- `srs-game-gen apply-rules`: apply migrated rules to a directory of compatibility-format game CSV files
- `srs-game-gen rank-game`: apply one migrated rule to one compatibility-format game CSV file
- `real-gen import-game`: import one feature-mask dataset into `outputs/real/<dataset_id>/games/`
- `real-gen apply-rules`: apply migrated rules to `outputs/real/<dataset_id>/games/`
- `real-gen make-figures`: render canonical table-style PNG figures plus extra real-data figures from `outputs/real/<dataset_id>/rankings/`
- `real-gen feature-rule-heatmap`: render the canonical feature-by-rule heatmap

Archive-only historical commands are not part of the root CLI contract:

- `game-gen check-axioms`
- `game-gen summarize-axioms`
- `game-gen axiom-summary-heatmap`
- `game-gen rank-heatmap`
- `game-gen rule-corr-heatmap`
- `game-gen pipeline`
- `game-gen make-figures-png`
- unpublished real-data commands that exist only under `legacy/`

These commands are closed as archive-only behavior under [`../legacy/`](../legacy/) rather than default migration targets.

`real-gen` is now the published root CLI for this tree. `srs-game-gen` is still intentionally partial, but `gen-games`, `make-figures`, `apply-rules`, and `rank-game` are part of the supported root surface. The canonical real-data figures, the feature-rule heatmap, and the main extra figure family are migrated, while some legacy-only compatibility details still remain in archive-oriented code paths under [`../legacy/`](../legacy/).

Compatibility note:

- the historical CSV naming scheme is now owned by [`srs_calculation/infrastructure/persistence/`](srs_calculation/infrastructure/persistence/) as a compatibility layer
- that layer is a file-format concern, not a `legacy/` runtime dependency
- prefer the `compatible_*` persistence APIs when adding new code to this tree

## Important rule

Do not copy large `legacy/` modules into this tree unchanged. Port behavior intentionally and document architectural differences when they matter.
