# Migration from `legacy/`

This document defines how the repository should evolve from the current legacy-centered codebase toward the new implementation under [`../../../src/`](../../../src/).

## Migration principles

- `legacy/` remains the reference implementation until a behavior is reproduced or intentionally replaced
- new production code should prefer `src/` over adding more complexity to `legacy/`
- migration should happen by capability, not by copying directories wholesale
- each migration step should keep tests and documentation synchronized

## Suggested migration order

### Phase 1: stabilize shared language

- document architecture boundaries
- define contribution rules
- create ADR and spec templates
- clarify which documents are authoritative

### Phase 2: extract domain logic

Start with logic that is easiest to test independently:

- ranking rules
- coalition representation
- axiom predicates or evaluators

Likely sources:

- [`../../../legacy/src/gamegen/rules`](../../../legacy/src/gamegen/rules)
- [`../../../legacy/src/gamegen/axioms`](../../../legacy/src/gamegen/axioms)

### Phase 3: rebuild workflows in `application/`

Reconstruct the major workflows as explicit services:

- synthetic game generation
- ranking application
- axiom checking
- real-data import orchestration

### Phase 4: move adapters and interfaces

After domain and application logic stabilize:

- rebuild CLI adapters
- move configuration loaders
- move CSV and plotting adapters

### Phase 5: deprecate legacy entry points

Only after parity is demonstrated:

- redirect users to the new CLI
- reduce legacy code to reference or archival status

## Workflow for making `legacy/` unreachable

To remove `legacy/` from the runtime path over time, follow this sequence:

1. create thin CLI shells in `src/`
2. move each shell-backed workflow into `application/` and `infrastructure/`
3. lock parity between the old CLI behavior and the `src/` workflow with tests
4. move user-facing README and docs entry points to the `src/` path
5. only then remove the public `legacy` scripts from package metadata

The important constraint is that the public entry point should switch only after the command's underlying use case already exists in `src/`.

## Mapping hints

- `legacy/src/gamegen/rules` -> `src/srs_calculation/domain/ranking/rules`
- coalition and game representations -> `src/srs_calculation/domain/games`
- `legacy/src/gamegen/axioms` -> `src/srs_calculation/domain/axioms`
- `legacy/src/gamegen/commands` -> `src/srs_calculation/interfaces/cli`
- `legacy/src/gamegen/io` -> `src/srs_calculation/infrastructure/persistence`
- `legacy/src/realgen/commands` -> `src/srs_calculation/interfaces/cli` plus `src/srs_calculation/application/`
- `legacy/config.yaml` loading -> `src/srs_calculation/infrastructure/config`

## Current progress

The repository already contains a first migrated ranking slice in `src/`:

- `domain/games` and `domain/ranking` for the in-memory ranking core
- `application/ranking/apply_ranking_rules.py` for rule execution on `CoalitionGame`
- `application/ranking/apply_ranking_rules_to_game_csv.py` for legacy-style game-CSV workflows
- `infrastructure/persistence/csv_game_repository.py` and `csv_ranking_repository.py` for legacy-compatible CSV boundaries
- `interfaces/cli/game_gen.py` for a thin synthetic-game CLI adapter over the migrated ranking workflow
- `application/ranking/apply_ranking_rules_to_real_dataset.py` for a dataset-scoped real-data ranking workflow
- `application/dataset_ingestion/import_feature_mask_table.py` for feature-mask dataset import
- `application/experiments/run_real_data_experiment.py` for canonical and extra real-data plotting workflows
- `interfaces/cli/real_gen.py` for a partial real-data CLI adapter over that migrated workflow
- `tests/` coverage for the persistence adapters and ranking application workflow
- parity tests for the first-batch ranking rules on deterministic fixtures

The next migration steps should build on these modules rather than recreating the same slice elsewhere.

The current CLI migration status is:

- `game-gen`: experimental `apply-rules` and `rank-game` entry points already exist in `src/`
- `real-gen`: experimental `import-game`, dataset-scoped `apply-rules`, `make-figures`, and `feature-rule-heatmap` entry points now exist in `src/`
- `real-gen` main extra figure families
  interaction-index / red-index tables and scatter / shapley values / ordinal banzhaf values / lexcel rank count / rp-index top-k / give top-k
  are also migrated into `src/`
- some legacy-only rendering compatibility details and peripheral options still remain

The current published-entry-point state is:

- the root `pyproject.toml` now publishes `real-gen` from the `src` CLI
- the root `pyproject.toml` also publishes `srs-game-gen` as the partial synthetic CLI from `src`
- `legacy/pyproject.toml` still keeps `game-gen` / `real-gen` as legacy entry points for reference

## Definition of done for a migrated capability

A capability should be considered migrated only when:

- behavior is implemented in `src/`
- automated tests cover the new implementation
- docs are updated
- the migration impact is recorded in an ADR if architecture changed
- the relationship to the corresponding legacy behavior is clear

## Anti-patterns to avoid

- copying a large legacy module into `src/` without refactoring boundaries
- mixing new architecture concepts directly into `legacy/`
- relying on undocumented behavioral differences between old and new paths
- merging large refactors without a spec or ADR when the architecture changes
