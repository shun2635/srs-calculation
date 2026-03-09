# Compatibility CSV Boundary

This package owns the compatibility-format CSV boundary used during migration.

## Intent

- keep historical `player*`, `score`, `rank`, `rank_*`, and `score_*` CSV conventions usable from `src/`
- make that compatibility explicit at the infrastructure boundary
- avoid treating `legacy/` as a runtime dependency

## Rule

Code outside `infrastructure/persistence/` should treat these files as a compatibility format owned by the new implementation, not as a reason to depend on the `legacy/` package tree.
