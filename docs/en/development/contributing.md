# Contributing Guide

This document defines the default collaboration rules for shared development.

## Working assumptions

- `legacy/` is the current reference implementation
- `src/` is the preferred home for new implementation work
- the English and Japanese documentation trees should remain aligned

## Before starting a substantial change

Write a spec in [`../specs/`](../specs/) when the change:

- introduces a new workflow
- changes public CLI behavior
- modifies data formats
- affects multiple modules or teams

Write or update an ADR in [`../adr/`](../adr/) when the change:

- alters architecture boundaries
- introduces a new dependency with broad impact
- changes how modules depend on each other
- formalizes a long-lived technical decision

## Branch and pull request expectations

- keep pull requests small enough to review coherently
- separate architecture changes from mechanical migrations when possible
- link the relevant spec and ADR in the pull request description
- update docs in the same change when behavior or structure changes

## Code review expectations

Reviewers should check:

- boundary compliance with [`../architecture/module-boundaries.md`](../architecture/module-boundaries.md)
- test coverage appropriate to the risk of the change
- documentation updates
- migration impact relative to `legacy/`

## Documentation rules

- update both [`../../ja/README.md`](../../ja/README.md) and [`../README.md`](../README.md) when onboarding or navigation changes
- keep corresponding documents in `en/` and `ja/` aligned when structure or policy changes
- prefer adding a new focused document over turning a README into a catch-all reference
- when code changes package structure, workflow boundaries, or supported migration paths, update the corresponding architecture/spec docs in the same change

## Testing rules

- add unit tests for domain logic
- add integration tests for I/O and CLI wiring
- add end-to-end tests for major workflows when behavior crosses multiple layers

## Default path for new work

- add new production code under [`../../../src/`](../../../src/)
- keep `legacy/` changes limited to reference fixes, parity verification, or unavoidable maintenance
- document migration intent when porting behavior from `legacy/`
