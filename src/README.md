# New Source Tree

This directory is reserved for the new implementation of the repository.

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
- name application modules after use cases, for example `apply_ranking_rules.py`
- use snake_case internal rule identifiers such as `ordinal_banzhaf`
- keep output-column naming decisions at the serialization boundary, not in core domain APIs

## Important rule

Do not copy large `legacy/` modules into this tree unchanged. Port behavior intentionally and document architectural differences when they matter.
