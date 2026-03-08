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

1. Generate game tables with `game-gen gen-games`.
2. Apply ranking rules with `game-gen apply-rules` or `game-gen pipeline`.
3. Evaluate axiom satisfaction with `game-gen check-axioms`.
4. Produce heatmaps or summary plots for inspection.

Relevant locations:

- CLI reference: [`../../legacy/README.md`](../../legacy/README.md)
- Rule descriptions: [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- Axiom descriptions: [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

### 2. Real-data workflow

Use this when the research question starts from model evaluation tables or feature-subset experiments.

Typical sequence:

1. Place raw inputs under [`../../legacy/inputs/feature_mask_tables/`](../../legacy/inputs/feature_mask_tables/).
2. Normalize them with `real-gen import-game`.
3. Apply ranking rules with `real-gen apply-rules`.
4. Create figures and heatmaps with `real-gen make-figures` and `real-gen feature-rule-heatmap`.

Relevant locations:

- dataset input notes: [`../../legacy/inputs/README.md`](../../legacy/inputs/README.md)
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
3. Move to the `legacy/docs` appendices only when a rule definition or axiom condition needs to be checked precisely.
4. Treat [`../../legacy/`](../../legacy/) as the current implementation source of truth until the repository is refactored.

## Why the repository is documented this way

The code layout is still historical, but the collaboration requirements are current. The top-level docs are therefore meant to reduce onboarding cost for both Japanese-speaking and English-speaking collaborators without forcing a full code migration first.
