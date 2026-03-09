# ADR-0001: Make Ranking Domain Foundation the First Migration Slice

## Status

Accepted

## Context

The repository already distinguishes between:

- `legacy/` as the current reference implementation
- `src/` as the target location for the next implementation

However, without an explicit first migration decision, contributors could reasonably start in several incompatible directions:

- rebuilding the CLI first
- migrating visualization code first
- porting real-data workflows first
- copying large `legacy` modules into `src/` without architectural separation

The project therefore needs a narrow, stable, and high-leverage first migration slice that establishes domain boundaries without forcing a full-stack rewrite.

The corresponding specification is:

- [`../specs/ranking-domain-foundation.md`](../specs/ranking-domain-foundation.md)

## Decision

The first migration slice from `legacy/` into `src/` will be the ranking domain foundation.

This decision means:

- the first new production-oriented code in `src/` will center on `domain/games` and `domain/ranking`
- a shared ranking-rule interface and registry will be created inside `domain/ranking`
- the initial migrated rule set will be limited to:
  - `shapley`
  - `banzhaf`
  - `lexcel`
  - `ordinal_banzhaf`
- a minimal application-layer rule runner may be added to orchestrate rule execution on in-memory game objects

This decision also means that the following remain out of scope for the first slice:

- CLI replacement
- plotting and heatmap migration
- real-data workflow migration
- axiom-checking migration
- broad copy-and-paste migration of `legacy` modules

## Consequences

Positive:

- the repository gets a real domain-oriented starting point in `src/`
- migration can be validated through parity tests against `legacy`
- contributors get a concrete scope that is large enough to matter and small enough to complete
- future CLI and infrastructure work can target a stable application/domain boundary

Negative:

- there will be temporary duplication between `legacy` and `src/`
- users will not get an immediate new CLI in the first migration phase
- later rules may reveal interface gaps that require follow-up ADRs

Operational consequences:

- new code for this capability should default to `src/`, not `legacy/`
- related implementation changes should reference this ADR
- any attempt to broaden the first slice substantially should be justified in a follow-up ADR or spec

## Alternatives considered

- Migrate the full CLI stack first
  - rejected because it mixes interfaces, I/O, and domain concerns too early
- Migrate the real-data pipeline first
  - rejected because it depends on stable ranking-domain abstractions that do not yet exist
- Copy existing `legacy` ranking modules directly into `src/`
  - rejected because it would preserve the old structural coupling rather than improve it

## Related documents

- [`../specs/ranking-domain-foundation.md`](../specs/ranking-domain-foundation.md)
- [`../architecture/module-boundaries.md`](../architecture/module-boundaries.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
