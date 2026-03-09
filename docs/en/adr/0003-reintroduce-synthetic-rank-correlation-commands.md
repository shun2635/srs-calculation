# ADR-0003: Reintroduce Synthetic Rank-Correlation Commands into the Root CLI

## Status

Accepted

## Context

ADR-0002 retired a broad set of historical synthetic commands from the root CLI contract while the repository was still decoupling from `legacy/`.

That was correct at the time, but `rank-heatmap` and `rule-corr-heatmap` are narrower than the full historical synthetic surface:

- they are paper-facing analysis commands
- they operate on rankings CSV files already produced by the migrated `src/` workflow
- they do not require the archive-only axiom or pipeline commands
- their behavior is stable enough to describe as part of the supported methodology

At the same time, the repository now has:

- a root-supported `srs-game-gen` CLI
- a paper-facing synthetic methodology spec
- integration and e2e coverage for the migrated synthetic workflow

## Decision

The repository reintroduces the following commands into the supported root `srs-game-gen` surface:

- `rank-heatmap`
- `rule-corr-heatmap`

They are implemented in `src/` and published as part of the root CLI contract.

The migrated behavior preserves the core historical method:

- convert serialized `rank_*` columns into effective competition-style ranks
- evaluate player-scope rules on singleton rows
- evaluate coalition-scope rules on non-empty coalition rows
- compute rule-correlation matrices with `pandas.DataFrame.corr(method=...)`
- keep `spearman` as the default correlation method

This decision does not reopen the rest of the commands retired by ADR-0002. The following remain archive-only:

- `check-axioms`
- `summarize-axioms`
- `axiom-summary-heatmap`
- `pipeline`
- `make-figures-png`

## Consequences

Positive:

- the root-supported synthetic workflow now covers the main rank-comparison analyses used in research writing
- papers can describe rank-correlation analysis without referring readers back to `legacy/`
- the supported root CLI becomes more complete without reopening the full historical synthetic surface

Negative:

- ADR-0002 is no longer the latest decision for `rank-heatmap` and `rule-corr-heatmap`
- the repository now maintains additional plotting behavior in `src/`

Operational:

- root README and collaborator-facing docs must list these commands as supported
- synthetic methodology docs must describe the migrated rank-correlation method
- integration and e2e coverage must remain in place for both commands

## Alternatives considered

### Keep both commands archive-only

Rejected because the commands are narrow, useful, and already align with the migrated rankings workflow.

### Reintroduce all retired synthetic commands

Rejected because that would reopen a much larger migration surface than needed.

### Reintroduce only one of the two commands

Rejected because pairwise rank heatmaps and rule-correlation heatmaps are complementary views over the same rankings outputs.

## Related documents

- [`0002-retire-legacy-only-synthetic-commands.md`](0002-retire-legacy-only-synthetic-commands.md)
- [`../specs/synthetic-game-methodology.md`](../specs/synthetic-game-methodology.md)
- [`../architecture/legacy-removal-runbook.md`](../architecture/legacy-removal-runbook.md)
- [`../../../README.md`](../../../README.md)
