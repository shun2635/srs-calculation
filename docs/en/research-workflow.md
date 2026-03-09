# Research Workflow

This document describes how to use the current repository in a collaborative research setting.

For contribution rules and the new implementation target, also read:

- [`development/contributing.md`](development/contributing.md)
- [`architecture/migration-from-legacy.md`](architecture/migration-from-legacy.md)

## Two parallel workflows

The repository supports two related but distinct workflows.

### 1. Synthetic-game workflow

Use this when the research question is about the comparative behavior of ranking rules under controlled game generation.

Typical sequence:

1. Generate game tables with `srs-game-gen gen-games`.
2. Apply ranking rules with `srs-game-gen apply-rules`.
3. Produce ranking figures with `srs-game-gen make-figures`.

Relevant locations:

- root CLI contract: [`../../README.md`](../../README.md)
- `src` entry point: [`../../src/README.md`](../../src/README.md)
- Rule descriptions: [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- Axiom descriptions: [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

Notes:

- synthetic commands such as `check-axioms` are archive-only under `legacy/` and are not part of the supported root CLI contract
- use `legacy/docs` only as an appendix for mathematical definitions

### 2. Real-data workflow

Use this when the research question starts from model evaluation tables or feature-subset experiments.

Typical sequence:

1. Place raw inputs under [`../../inputs/feature_mask_tables/`](../../inputs/feature_mask_tables/).
2. Normalize them with `real-gen import-game`.
3. Apply ranking rules with `real-gen apply-rules`.
4. Create figures and heatmaps with `real-gen make-figures` and `real-gen feature-rule-heatmap`.

Relevant locations:

- root CLI contract: [`../../README.md`](../../README.md)
- `src` entry point: [`../../src/README.md`](../../src/README.md)
- real-data design notes: [`../../legacy/docs/design/real_data.md`](../../legacy/docs/design/real_data.md)

## Reproducibility checklist

For collaborative work, keep the following stable whenever possible.

- commit hash of the repository
- `config.yaml` values used in the run
- CLI commands and options
- dataset identifier and schema file
- output directory retained for inspection

## Recommended collaboration pattern

For internal discussion in CMIS Lab or external discussion with LAMSADE:

1. Start with the English docs in [`./`](./).
2. Use the synthetic or real-data workflow depending on the research question.
3. Use the root CLI for execution and treat `src/` as the default implementation to inspect.
4. Move to the `legacy/docs` appendices only when a rule definition or axiom condition needs to be checked precisely.

## Why the repository is documented this way

The code layout still contains migration-era boundaries, but the primary collaboration path now goes through the root CLI and the top-level docs. This keeps onboarding practical without forcing collaborators to start from `legacy/`.
