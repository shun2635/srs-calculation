# ADR-0002: Retire Legacy-Only Synthetic Commands from the Root CLI Contract

## Status

Accepted

## Context

The repository now has an explicit root CLI contract centered on:

- `srs-real-gen`
- `srs-game-gen`
- `srs-test`

However, several historical synthetic commands still exist only under `legacy/`:

- `game-gen check-axioms`
- `game-gen summarize-axioms`
- `game-gen axiom-summary-heatmap`
- `game-gen rank-heatmap`
- `game-gen rule-corr-heatmap`
- `game-gen pipeline`
- `game-gen make-figures-png`

Leaving these commands in an undefined state creates long-term ambiguity:

- collaborators cannot tell whether they should wait for migration or stop relying on them
- docs cannot cleanly define the supported root execution surface
- the runbook for removing `legacy/` cannot distinguish required migrations from archive-only leftovers

The repository therefore needs a clear decision about whether these commands are still part of the supported root future.

## Decision

The commands listed above are retired from the root CLI contract.

This means:

- they are not planned as default migration targets into `src/`
- they are not part of the supported root workflow for collaborative use
- they remain available only as historical archive behavior under `legacy/` for as long as the archive exists
- primary docs should not direct collaborators to them as part of normal root-based operation

The supported synthetic root workflow remains limited to:

- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen make-figures`
- `srs-game-gen rank-game`

If one of the retired commands later becomes strategically necessary again, it should be reintroduced through a new spec or ADR rather than assumed back into scope.

## Consequences

Positive:

- the supported root CLI surface becomes smaller and unambiguous
- documentation can treat those commands as archive-only instead of "not yet migrated"
- legacy removal planning becomes clearer because fewer commands are mandatory migration targets

Negative:

- some historical research workflows will no longer be considered supported from the root project
- collaborators who still need those commands must treat them as archive behavior, not as the forward path

Operational consequences:

- root docs should describe these commands as archive-only
- future migration planning should not count these commands as required unless a new decision reopens them
- tests for the root CLI should not expect these commands to appear in the supported surface

## Alternatives considered

- Migrate every historical synthetic command into `src/`
  - rejected because it expands the root support surface beyond what is currently needed for collaborative use
- Leave the commands undocumented but implicitly possible future work
  - rejected because it preserves ambiguity and blocks clean deprecation planning
- Remove the commands from history immediately
  - rejected because keeping archive behavior available for reference remains useful during transition

## Related documents

- [`../architecture/legacy-removal-runbook.md`](../architecture/legacy-removal-runbook.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../../../README.md`](../../../README.md)
- [`../../../src/README.md`](../../../src/README.md)
