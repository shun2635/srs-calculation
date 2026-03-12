# Specification: constrained synthetic ranking workflow

## Summary

This spec defines a constrained synthetic-game workflow that adds TU-style generation, with `v(emptyset)=0`, monotonicity, and superadditivity, alongside the current unconstrained generator, and makes the resulting ranking outputs comparable through both axiom satisfaction rates and rule-rank correlations.

The initial scope replaces the simple variant switch with a composable constraint-set model. The first supported constraints are `empty_zero`, `monotone`, and `superadditive`, while `tu` is treated as a shorthand profile expanding to all three. Output paths and analysis artifacts become constraint-set aware, and generation configuration plus output-layout resolution are refactored so future constrained generators remain easy to add.

## Problem

The current root synthetic workflow has a few structural gaps.

- `gen-games` can only generate one kind of complete cooperative game: the current unconstrained iid table
- synthetic outputs use fixed directories such as `games/nN` and `rankings/nN`, which do not support side-by-side constrained runs cleanly
- the `src/` tree already contains axiom-evaluation core logic, but the public synthetic workflow does not expose an aggregate axiom-rate path with root-surface PNG heatmaps
- `rule-corr-heatmap` can render PNGs, but it does not currently emit machine-readable summaries that are easy to compare across constraint sets

As a result, it is hard to systematically compare how axiom satisfaction rates and rank correlations change between unconstrained and TU-constrained synthetic samples, or to extend the workflow toward richer combinations of constraints later.

## Goals

- introduce a composable constraint-set model for synthetic generation
- support `empty_zero`, `monotone`, and `superadditive` in the first implementation, with `tu` as a shorthand profile
- separate games, rankings, figures, heatmaps, and analysis outputs by constraint set
- expose aggregated axiom satisfaction for both coalition-scoped and individual-scoped rules through an extensible workflow
- preserve rule-correlation heatmaps while also writing summary CSV artifacts
- include axiom-summary PNG heatmaps in the public root synthetic workflow
- refactor the workflow so future constraints such as `convex` are straightforward to add

## Non-goals

- introducing a general constraint DSL or constraint solver in the first implementation
- restoring the entire legacy axiom-example PNG workflow to the public root CLI
- fully defining the mathematics of individual-scope axioms in this spec alone
- fixing the paper-facing interpretation of the experiment results in this spec

## Scope

In scope:

- `src/srs_calculation/application/game_generation`
- `src/srs_calculation/application/ranking`
- `src/srs_calculation/application/axiom_evaluation`
- `src/srs_calculation/application/experiments`
- `src/srs_calculation/interfaces/cli/game_gen.py`
- helper code for synthetic output-path resolution
- `docs/ja` and `docs/en` synthetic workflow documentation
- unit, integration, and end-to-end tests for the synthetic workflow

Out of scope:

- removing the `legacy/` archive
- changing the real-data workflow under `srs-real-gen`

## Proposed design

### 1. Make generation constraints first-class

Replace the current implicit `generate_synthetic_games(...)` behavior with explicit generation settings including:

- `constraints`: `tuple[str, ...]`
- `players`
- `count`
- `max_score`
- `seed`
- `out_dir`

Internally, the normalized constraint set switches the generation strategy.

- `unconstrained`: no structural constraint
- `empty_zero`: enforce `v(emptyset)=0`
- `monotone`: enforce `S ⊆ T => v(S) <= v(T)`
- `superadditive`: enforce `S ∩ T = emptyset => v(S ∪ T) >= v(S) + v(T)`
- `tu`: shorthand profile expanding to `empty_zero + monotone + superadditive`

The canonical representation should use the normalized post-expansion constraint set for path resolution and metadata.

Because constraints can be stacked, the generator may prefer a constructive algorithm over naive generate-and-reject. The implementation detail is open, but the resulting tables must satisfy:

- `empty_zero`: the empty coalition is always zero
- `monotone`: no monotonicity violation
- `superadditive`: no superadditivity violation
- `tu`: all three constraints simultaneously

### 2. Make the synthetic output layout constraint-set aware

For extensibility, the canonical synthetic layout should move toward:

- `outputs/synthetic/<constraint_set_id>/games/nN/game_*.csv`
- `outputs/synthetic/<constraint_set_id>/rankings/nN/game_*.csv`
- `outputs/synthetic/<constraint_set_id>/figures/nN/game_*.png`
- `outputs/synthetic/<constraint_set_id>/heatmaps/nN/*.png`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/rule_corr_player.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/rule_corr_coalition.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/coalition/<axiom_id>/<rule>.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/coalition/summary.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/coalition/summary_heatmap.png`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/individual/<axiom_id>/<rule>.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/individual/summary.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/individual/summary_heatmap.png`

`constraint_set_id` is a deterministic slug derived from the normalized constraint set, for example:

- `unconstrained`
- `empty_zero+monotone`
- `empty_zero+monotone+superadditive`

This should be backed by one shared path resolver instead of the current command-local path logic.

Its responsibilities are:

- derive canonical paths from `constraints`, `players`, and `out_dir`
- allow explicit `--games-dir` and `--rankings-dir` to override the canonical paths
- be reused by `gen-games`, `apply-rules`, `make-figures`, `rank-heatmap`, `rule-corr-heatmap`, `evaluate-axioms`, and `axiom-summary-heatmap`

No compatibility alias should remain. The old `outputs/games`, `outputs/rankings`, `outputs/heatmaps`, and `outputs/axiom` layout should be removed from the canonical root workflow.

### 3. Add a public axiom-evaluation workflow to the root synthetic surface

The `src/` tree already provides `evaluate_axioms_for_results(...)`. A synthetic aggregation command should expose it.

Recommended surface:

- `srs-game-gen evaluate-axioms --players N --constraint <id>...`
- `srs-game-gen axiom-summary-heatmap --players N --constraint <id>... --scope coalition|individual`

Responsibilities:

- read rankings and the corresponding source games
- evaluate coalition-scoped and individual-scoped rules separately by scope
- write per-game count CSVs under `analysis/nN/axiom/<scope>/<axiom_id>/<rule>.csv`
- write aggregate summaries to `analysis/nN/axiom/<scope>/summary.csv`
- support `summary_heatmap.png` as a root-workflow artifact

The summary CSV should keep the legacy columns:

- `rule`
- `axiom`
- `constraints`
- `satisfied`
- `satisfied_rate`

The workflow does not need to restore the legacy violation-example PNGs, but it does need root-surface summary heatmaps.

Because the concrete individual-scope axioms will be specified later, the first implementation may prepare the extension points now:

- scope-aware CLI and output layout
- separate coalition and individual axiom registries
- a no-op or empty-registry behavior for `scope=individual` until concrete axioms are provided

### 4. Persist rule-correlation summaries as CSV

`rule-corr-heatmap` already computes the correlation matrices internally. Those matrices should also be written as reusable artifacts:

- `analysis/nN/rule_corr_player.csv`
- `analysis/nN/rule_corr_coalition.csv`

`rule-corr-heatmap` may either consume those summaries when rendering PNGs, or compute once and write both CSV and PNG in the same pass. The important requirement is to keep numeric correlation artifacts for constraint-set comparison.

### 5. Keep the existing figure and heatmap workflow constraint-set aware

`apply-rules`, `make-figures`, `rank-heatmap`, and `rule-corr-heatmap` should accept constraint selection and default to the same constraint-set root when explicit directories are not provided.

Minimal CLI surface:

- `srs-game-gen gen-games --constraint empty_zero --constraint monotone --constraint superadditive`
- `srs-game-gen gen-games --profile tu`
- `srs-game-gen apply-rules --constraint ...`
- `srs-game-gen make-figures --constraint ...`
- `srs-game-gen rank-heatmap --constraint ...`
- `srs-game-gen rule-corr-heatmap --constraint ...`
- `srs-game-gen evaluate-axioms --constraint ...`
- `srs-game-gen axiom-summary-heatmap --constraint ... --scope coalition|individual`

### 6. Refactoring direction

Three extractions are worth doing up front:

- a constraint-set aware `SyntheticOutputLayout`
- a `SyntheticGenerationSpec` and/or `SyntheticGenerator`
- a `ConstraintSet` and `ConstraintProfile` normalizer

That keeps generator branching out of the CLI and makes future constraints a local change in the generation layer plus path definitions.

## Data and interfaces

### CLI

New or changed public inputs:

- repeated `--constraint <id>`
- `--profile tu`
- a new `evaluate-axioms` command
- a new `axiom-summary-heatmap` command

If `--games-dir` or `--rankings-dir` is provided explicitly, those paths take precedence over constraint-derived canonical paths.

### Config

Allow constraint selection in the synthetic generation config.

Example:

```yaml
output_base: outputs
gen_games:
  profile: tu
  count: 100
  max_score: 31
  seed: 7
```

If needed for future growth, constraint-specific settings may later move into a separate section.

```yaml
synthetic:
  constraints:
    - empty_zero
    - monotone
    - superadditive
  profiles:
    tu:
      expands_to:
        - empty_zero
        - monotone
        - superadditive
```

The first implementation does not need the full nested structure, but `tu` should not become a permanent one-off special case.

### CSV contracts

New summary CSVs:

- `analysis/nN/rule_corr_player.csv`
- `analysis/nN/rule_corr_coalition.csv`
- `analysis/nN/axiom/coalition/summary.csv`
- `analysis/nN/axiom/coalition/summary_heatmap.png`
- `analysis/nN/axiom/individual/summary.csv`
- `analysis/nN/axiom/individual/summary_heatmap.png`

Per-game axiom CSV:

- header: `game,constraints,satisfied,satisfied_rate`

Rule-correlation CSV:

- headered matrix CSV
- index and columns reuse the `rank_*` column names
- values follow `pandas.DataFrame.corr(method=...)`

The game CSV format itself does not change. Constraint differences are expressed through the generation method and output paths, while preserving serializer compatibility.

## Migration plan

### Recommended implementation order

1. add the constraint-set aware output-layout resolver and route existing synthetic commands through it
2. add `ConstraintSet` normalization and `gen-games --constraint`
3. add a generator that satisfies `empty_zero`, `monotone`, and `superadditive`
4. add `evaluate-axioms`, `axiom-summary-heatmap`, and the scope-separated summary writers
5. add CSV summary output to `rule-corr-heatmap`
6. update docs and end-to-end workflow coverage

### Compatibility policy

The canonical layout should fully move to `outputs/synthetic/<constraint_set_id>/...`.

No path compatibility alias should remain. Existing docs, tests, and help text should be updated in the same change so the root synthetic workflow has one canonical layout only.

## Testing plan

- unit: constraint normalization expands `profile=tu` into `empty_zero+monotone+superadditive`
- unit: the constrained generator satisfies `v(emptyset)=0`, monotonicity, and superadditivity
- unit: the constraint-set aware path resolver returns the expected artifact paths
- integration: `apply-rules` reads from constraint-set aware directories and writes rankings correctly
- integration: `evaluate-axioms` writes CSVs with the expected headers
- integration: `axiom-summary-heatmap` writes scope-specific PNG outputs
- integration: `rule-corr-heatmap` writes both PNG and CSV artifacts
- e2e: `unconstrained` and `tu` can run under the same `out` root without collisions
- e2e: the full `gen-games -> apply-rules -> evaluate-axioms -> rule-corr-heatmap` workflow succeeds

## Recommended implementation slices

- Slice 1: introduce the path resolver and make the existing synthetic CLI constraint-set aware
- Slice 2: add constraint normalization and the TU-constrained generator
- Slice 3: add axiom aggregation, summary CSVs, and summary heatmaps
- Slice 4: persist rule-correlation CSV outputs and update docs

This sequence keeps the existing unconstrained workflow stable while the new comparison path is added incrementally.

## Open questions

- What are the concrete individual-scope axioms, rule mappings, and display labels?
- Should the canonical slug use the fully expanded set such as `empty_zero+monotone+superadditive`, or prefer a profile label such as `tu` when available?

## Related documents

- [`synthetic-game-methodology.md`](synthetic-game-methodology.md)
- [`legacy-ranking-and-axiom-completion.md`](legacy-ranking-and-axiom-completion.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../adr/0003-reintroduce-synthetic-rank-correlation-commands.md`](../adr/0003-reintroduce-synthetic-rank-correlation-commands.md)
- [`../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md`](../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md)
