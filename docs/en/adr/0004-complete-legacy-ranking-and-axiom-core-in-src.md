# ADR-0004: Complete the Legacy Synthetic Ranking and Axiom Core in `src`

## Status

Accepted

## Context

ADR-0001 deliberately started with a narrow first batch of ranking rules. That first slice is now established, and the repository needs the rest of the synthetic ranking core in `src/` to avoid keeping the domain split across two trees.

The remaining gap was:

- coalition-scoped synthetic ranking rules
- rank-column serialization for those rules
- coalition-ranking axiom evaluators

## Decision

The repository expands the `src/` core to include:

- all legacy synthetic ranking rules
- a scope-aware ranking result model that supports player and coalition outputs
- compatibility-format serialization for the full synthetic rule family
- coalition-ranking axiom evaluators under `src/srs_calculation/domain/axioms`
- an application-layer axiom evaluation use case

This decision does not publish archive-only axiom CLI commands in the root contract.

## Consequences

Positive:

- `src/` now contains the full legacy synthetic ranking core instead of only a first batch
- real-data and synthetic workflows can share one rule registry in `src/`
- axiom logic no longer exists only in the retained archive

Negative:

- the shared ranking result model becomes more complex because it must represent both player and coalition outputs
- serializer logic must carry a few compatibility-specific special cases such as `ud` / `du`

Operational:

- tests must protect the expanded registry surface
- docs must distinguish between migrated axiom core and archive-only axiom CLI commands

## Related documents

- [`../specs/legacy-ranking-and-axiom-completion.md`](../specs/legacy-ranking-and-axiom-completion.md)
- [`0001-ranking-domain-foundation.md`](0001-ranking-domain-foundation.md)
