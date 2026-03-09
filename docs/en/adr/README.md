# Architectural Decision Records

This directory stores Architectural Decision Records for the new implementation and for repository-level technical decisions.

## When to add an ADR

Add an ADR when a decision:

- changes module boundaries
- introduces or removes a major dependency
- affects long-term maintainability
- changes how `src/` and `legacy/` should coexist

## Naming convention

Use sequential file names:

- `0001-short-title.md`
- `0002-short-title.md`

Keep titles short and decision-oriented.

## Minimum sections

- Status
- Context
- Decision
- Consequences

## Starting point

Use [`0000-template.md`](0000-template.md) as the template for new ADRs.

## Current ADRs

- [`0001-ranking-domain-foundation.md`](0001-ranking-domain-foundation.md): makes ranking domain foundation the first migration slice into `src/`
- [`0002-retire-legacy-only-synthetic-commands.md`](0002-retire-legacy-only-synthetic-commands.md): closes selected historical synthetic commands as archive-only instead of migrating them into the root CLI contract
