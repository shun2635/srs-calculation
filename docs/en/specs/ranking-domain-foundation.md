# Specification: Ranking Domain Foundation

## Summary

This specification defines the first concrete migration target from `legacy/` into `src/`: a new domain-centered ranking foundation that isolates coalition-game models, ranking-rule interfaces, and a first set of pure ranking rules from CLI, CSV, and plotting concerns.

## Problem

The current implementation in `legacy/` is useful as a research reference, but core ranking behavior is still embedded in a layout that mixes domain logic with command wiring, registry concerns, and file-oriented workflows. That makes large-scale collaboration harder in three ways:

- contributors have no stable domain layer to extend safely
- parity work against `legacy/` is harder than it needs to be
- new code risks repeating the same structural coupling in `src/`

The repository already documents `src/` as the preferred location for new implementation work, but there is not yet a real spec that defines the first capability to move.

## Goals

- establish the first production-oriented package slice under `src/srs_calculation/domain/`
- define stable domain models for coalition games and ranking results
- introduce a rule interface that multiple ranking rules can share
- port a first set of pure ranking rules from `legacy/` with parity-focused tests
- keep the migration narrow enough to complete without rebuilding the whole CLI stack

## Non-goals

- replacing the current `game-gen` CLI in this phase
- migrating plotting, heatmaps, or figure generation
- migrating the full real-data workflow
- changing CSV formats or output directory structure
- redesigning every ranking rule at once

## Scope

In scope:

- `src/srs_calculation/domain/` foundations for coalition games and ranking rules
- a minimal `src/srs_calculation/application/` service for applying selected rules to an in-memory game representation
- parity-oriented tests for the migrated rules
- documentation updates needed to explain the migrated slice

Out of scope:

- direct CLI migration
- persistence adapters beyond what tests minimally need
- real-data import and visualization flows
- axiom checking logic

## Proposed design

### Target modules

The first migrated slice should introduce at least the following modules.

```text
src/srs_calculation/
  domain/
    games/
      coalition_game.py
    ranking/
      result.py
      rule.py
      registry.py
      rules/
        shapley.py
        banzhaf.py
        lexcel.py
        ordinal_banzhaf.py
  application/
    ranking/
      apply_ranking_rules.py
```

The intent is to group domain code by feature area rather than under generic buckets such as `models/` or `rules/`.

### Domain model

The domain layer should define an in-memory representation for a cooperative game that is independent of CSV and pandas-specific concerns.

Minimum expectations:

- represent coalitions in a deterministic, hashable form
- represent coalition scores without binding the model to a DataFrame
- represent rule outputs in a structured form that can later be rendered to tables

Suggested domain concepts:

- `CoalitionGame`
- `CoalitionValue`
- `RuleScoreSet`
- `RuleRankSet`
- `RankingResult`

The implementation does not need to preserve these exact names, but it should preserve the separation of concerns they imply.

### Rule interface

Each ranking rule should implement a shared interface that:

- declares the rule identifier
- accepts a domain game object
- returns a structured result, not a DataFrame mutation

The interface should support rules that produce:

- score columns
- rank columns
- both score and rank outputs

The interface should not assume whether a rule is singleton-focused or coalition-focused. That distinction should remain rule-specific metadata.

### First migrated rules

The first implementation slice should port only rules that are mostly pure computational logic and do not require special plotting or dataset-specific behavior.

Recommended first batch:

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`

These rules are enough to validate the architecture while keeping the scope controlled.

### Application service

A minimal application-layer service should:

- accept an in-memory game object
- accept a list of rule identifiers
- resolve rules through the new registry
- return a structured aggregation of rule outputs

This service exists to prevent future interface code from calling rule modules ad hoc.

## Data and interfaces

This phase should not define a new public CLI.

Instead, the main interface contract is:

- input: an in-memory coalition game
- output: structured rule results that can later be serialized by infrastructure adapters

Compatibility note:

- the migrated rules must preserve semantic parity with the corresponding `legacy` rule outputs
- output-column naming compatibility should be retained at the serialization boundary, even if internal object names differ
- internal rule identifiers should prefer snake_case names such as `ordinal_banzhaf`

## Migration plan

### Step 1

Create the base domain models and rule interface under `src/`.

### Step 2

Port the selected first-batch rules from:

- `legacy/src/gamegen/rules/shapley.py`
- `legacy/src/gamegen/rules/banzhaf.py`
- `legacy/src/gamegen/rules/lexcel.py`
- `legacy/src/gamegen/rules/ordinal_banzhaf.py`

### Step 3

Create an application-layer rule runner that uses the new registry.

### Step 4

Add parity tests that compare `src/` outputs against `legacy` behavior on shared fixtures.

### Step 5

Document any intentional differences and decide whether a follow-up ADR is needed.

## Testing plan

The migrated slice should include:

- unit tests for coalition-game domain models
- unit tests for each migrated rule
- integration tests for the application-layer rule runner
- parity tests against `legacy` on representative small games

Recommended parity strategy:

- use small deterministic coalition games
- compare scores and ranks rule by rule
- include edge cases for ties and coalition ordering

## Open questions

- Should the first application-layer service return strongly typed objects only, or also include a tabular export helper for tests?
- Should singleton-only and coalition-wide rules share a single result contract, or should there be two related result types?

## Related documents

- [`../architecture/module-boundaries.md`](../architecture/module-boundaries.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../../../src/README.md`](../../../src/README.md)
