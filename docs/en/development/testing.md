# Testing Design

This document defines the current test design for the `src/`-based implementation.

## Purpose

The test suite exists to support migration from `legacy/` to `src/` without losing behavior while still allowing architectural improvement.

The testing strategy therefore has two simultaneous goals:

- verify correctness of the new implementation in isolation
- verify behavioral parity with `legacy` where parity is required

## Test layers

The repository currently uses four main test layers.

### `tests/unit/`

Purpose:

- verify small, isolated behavior
- validate domain models and narrow infrastructure adapters
- fail fast when low-level logic regresses

Examples:

- `tests/unit/domain/`
- `tests/unit/infrastructure/`

Use unit tests for:

- deterministic domain logic
- validation rules
- small data transformations
- repository and renderer behavior that can be tested without broader workflow setup

### `tests/integration/`

Purpose:

- verify use-case orchestration across multiple modules
- verify infrastructure wiring and CLI adapters
- confirm that application services produce the expected files, outputs, or structured results

Examples:

- `tests/integration/application/`
- `tests/integration/interfaces/cli/`

Use integration tests for:

- application services
- CSV-backed ranking flows
- dataset ingestion
- CLI command behavior

### `tests/e2e/`

Purpose:

- verify user-facing workflows through the public CLI boundary
- exercise real file generation across multiple layers without monkeypatching the core path
- catch regressions that only appear when generation, ranking, and rendering are combined

Examples:

- `tests/e2e/interfaces/cli/`

Use end-to-end tests for:

- synthetic workflows from game generation to PNG output
- real-data workflows from dataset import to ranking artifacts and heatmaps
- release-critical paths that collaborators are expected to run directly

### `tests/parity/`

Purpose:

- compare new `src/` behavior against the `legacy` reference implementation
- reduce migration risk when porting rules and workflows

Examples:

- `tests/parity/ranking/`

Use parity tests when:

- a migrated capability is expected to preserve legacy behavior
- a ranking rule or workflow is being ported from `legacy`
- regressions need to be caught at the behavioral boundary rather than only through internal assertions

## Directory conventions

The default structure is:

```text
tests/
  unit/
    domain/
    infrastructure/
  integration/
    application/
    interfaces/
  e2e/
    interfaces/
      cli/
  parity/
    ranking/
```

When adding new tests:

- mirror the source-layer boundary when possible
- keep domain tests under `unit/domain`
- keep application workflow tests under `integration/application`
- keep CLI tests under `integration/interfaces/cli`
- keep full CLI workflows under `e2e/interfaces/cli`
- keep `legacy` comparison tests under `parity`

## What to test at each layer

### Domain

Prefer unit tests for:

- coalition-game validation
- ranking result contracts
- rule registry behavior
- pure ranking rule logic
- axiom predicate logic

### Application

Prefer integration tests for:

- applying ranking rules to in-memory games
- applying rules to game CSV directories
- dataset-level ranking workflows
- experiment runners

### Infrastructure

Prefer unit tests for:

- CSV repository behavior
- config loading
- plotting helpers where inputs and outputs are narrow enough to isolate

Use integration tests only when multiple adapters must work together.

### Interfaces

Prefer integration tests for:

- CLI help output
- command option wiring
- expected file generation side effects

### End-to-end workflows

Prefer end-to-end tests for:

- one-command or multi-command researcher workflows that should work in a clean temp directory
- flows that must render actual CSV and PNG artifacts
- smoke coverage for the supported Poetry CLI entry points

Do not use end-to-end tests for narrow option validation that is already covered by integration tests.

## Execution rules

The root Poetry environment is the standard execution environment for `src`-based tests.

Run the full suite:

```bash
poetry install
poetry run srs-test
```

Run a subset:

```bash
poetry run srs-test tests/unit -q
poetry run srs-test tests/integration/application/ranking/test_apply_ranking_rules.py
poetry run srs-test tests/e2e -q
poetry run srs-test tests/parity/ranking -q
```

## Default expectations for code changes

### When changing domain logic

Add or update:

- unit tests
- parity tests when the logic is migrated from `legacy`

### When changing application workflows

Add or update:

- integration tests
- end-to-end tests when the change affects a supported researcher workflow
- parity tests if the workflow is intended to preserve legacy behavior

### When changing CLI behavior

Add or update:

- integration CLI tests
- end-to-end tests when the change affects a supported researcher workflow
- docs that describe the supported command surface

## Review expectations

Reviewers should ask:

- does the chosen test layer match the type of change?
- are failure messages specific enough to diagnose regressions?
- is parity being checked where parity is part of the migration promise?
- are docs updated when the supported workflow or test command changes?

## Current limitation

The current suite is still migration-oriented. Some tests intentionally reflect compatibility-format behavior rather than the final ideal architecture. As the `src/` implementation becomes authoritative, some parity tests may later be retired or narrowed.
