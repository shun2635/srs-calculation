# Migration from `legacy/`

This document defines how the repository should evolve from the current legacy-centered codebase toward the new implementation under [`../../../src/`](../../../src/).

## Migration principles

- `legacy/` remains the reference implementation until a behavior is reproduced or intentionally replaced
- new production code should prefer `src/` over adding more complexity to `legacy/`
- migration should happen by capability, not by copying directories wholesale
- each migration step should keep tests and documentation synchronized

## Suggested migration order

### Phase 1: stabilize shared language

- document architecture boundaries
- define contribution rules
- create ADR and spec templates
- clarify which documents are authoritative

### Phase 2: extract domain logic

Start with logic that is easiest to test independently:

- ranking rules
- coalition representation
- axiom predicates or evaluators

Likely sources:

- [`../../../legacy/src/gamegen/rules`](../../../legacy/src/gamegen/rules)
- [`../../../legacy/src/gamegen/axioms`](../../../legacy/src/gamegen/axioms)

### Phase 3: rebuild workflows in `application/`

Reconstruct the major workflows as explicit services:

- synthetic game generation
- ranking application
- axiom checking
- real-data import orchestration

### Phase 4: move adapters and interfaces

After domain and application logic stabilize:

- rebuild CLI adapters
- move configuration loaders
- move CSV and plotting adapters

### Phase 5: deprecate legacy entry points

Only after parity is demonstrated:

- redirect users to the new CLI
- reduce legacy code to reference or archival status

## Mapping hints

- `legacy/src/gamegen/rules` -> `src/srs_calculation/domain/rules`
- `legacy/src/gamegen/axioms` -> `src/srs_calculation/domain/axioms`
- `legacy/src/gamegen/commands` -> `src/srs_calculation/interfaces/cli`
- `legacy/src/gamegen/io` -> `src/srs_calculation/infrastructure/io`
- `legacy/src/realgen/commands` -> `src/srs_calculation/interfaces/cli` plus `application/`
- `legacy/config.yaml` loading -> `src/srs_calculation/infrastructure/config`

## Definition of done for a migrated capability

A capability should be considered migrated only when:

- behavior is implemented in `src/`
- automated tests cover the new implementation
- docs are updated
- the migration impact is recorded in an ADR if architecture changed
- the relationship to the corresponding legacy behavior is clear

## Anti-patterns to avoid

- copying a large legacy module into `src/` without refactoring boundaries
- mixing new architecture concepts directly into `legacy/`
- relying on undocumented behavioral differences between old and new paths
- merging large refactors without a spec or ADR when the architecture changes
