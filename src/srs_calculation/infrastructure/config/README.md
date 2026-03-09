# Root Config Rules

This package owns configuration loading for the root CLI surface.

## Supported lookup rule

The root CLI reads YAML configuration only when an explicit `--config <path>` is provided.

Lookup order:

1. explicit CLI arguments
2. explicit YAML file passed through `--config`
3. built-in defaults in `src/`

## Non-goals

- no implicit lookup of `legacy/config.yaml`
- no implicit lookup of `./config.yaml`
- no hidden repository-level config fallback
