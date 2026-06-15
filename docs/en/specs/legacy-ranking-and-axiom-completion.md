# Specification: Legacy Ranking and Axiom Completion

## Summary

This specification defines the migration slice that extends the original ranking-domain foundation to the full legacy synthetic ranking rule family and the coalition-ranking axiom evaluators.

## Goals

- migrate all legacy synthetic ranking rules into `src/`
- support both player-scope and coalition-scope ranking outputs in the shared domain result model
- preserve compatibility-format rankings CSV columns for the expanded rule set
- migrate the coalition-ranking axiom evaluators into `src/domain/axioms`
- keep root CLI contracts unchanged for archive-only axiom commands

## In scope

- the remaining synthetic rules from `legacy/src/gamegen/rules/`
- `CoalitionGame` support for preserving serialized base `rank` values
- compatibility-format rankings CSV serialization for coalition-scoped rules
- application-layer axiom evaluation over coalition-scoped ranking results
- tests for the expanded rule registry and axiom registry

## Out of scope

- publishing `check-axioms` or related commands in the root CLI
- migrating archive-only axiom figure commands as supported root workflows
- replacing the retained `legacy/` archive

## Migrated rule set

Player-scope rules:

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`

Coalition-scope rules:

- `group_shapley`
- `group_sum_shapley`
- `group_ordinal_banzhaf`
- `group_lexcel`
- `shapley_interaction`
- `banzhaf_interaction`
- `rp_index`
- `ud`
- `du`
- `red_index`

## Migrated axiom set

- `reversal-2p`
- `reversal-weak-n`
- `give-2p`
- `take-2p`
- `give-weak-n`
- `take-weak-n`
- `redundancy`

## Design notes

- player-scope and coalition-scope outputs share the same `RankingResult` shape, with scope carried by the nested score/rank sets
- coalition rules that depend on the serialized base `rank` column read it through `CoalitionGame.base_ranks_by_mask`
- compatibility-format column naming remains the serialization boundary, not a domain concern
- `ud` and `du` keep their auxiliary `score_*_up` and `score_*_down` columns through serializer-specific support

## Testing plan

- keep existing first-batch parity tests
- add registry and integration tests for the full rule set
- add registry and application tests for the migrated axiom evaluators
- keep the full root Poetry test suite green

## Related documents

- [`ranking-domain-foundation.md`](ranking-domain-foundation.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md`](../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md)
