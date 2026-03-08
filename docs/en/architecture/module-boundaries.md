# Module Boundaries for the New Implementation

This document defines the intended package boundaries for code under [`../../../src/`](../../../src/).

## Target package tree

```text
src/
  srs_calculation/
    domain/
    application/
    infrastructure/
    interfaces/
```

## Boundary definitions

### `domain/`

Purpose:

- core business and mathematical concepts
- coalition models
- ranking rules
- axiom definitions

Rules:

- no CLI code
- no filesystem access
- no plotting concerns
- prefer deterministic, testable logic

### `application/`

Purpose:

- orchestrate use cases
- connect domain logic to external services
- define workflow-level operations such as import, rule application, and report generation

Rules:

- may depend on `domain/`
- should not contain direct CLI parsing
- should isolate workflow coordination from storage details

### `infrastructure/`

Purpose:

- CSV and YAML I/O
- configuration loading
- persistence adapters
- plotting and other external-library integrations

Rules:

- may depend on `domain/` and `application/`
- should keep external side effects contained
- should expose narrow interfaces to the rest of the codebase

### `interfaces/`

Purpose:

- CLI entry points
- command adapters
- future API or notebook-facing adapters if needed

Rules:

- should be thin
- should delegate business logic to `application/`
- should not duplicate validation or workflow logic already expressed elsewhere

## Dependency direction

The intended dependency direction is:

```text
interfaces -> application -> domain
infrastructure -> application -> domain
```

`domain/` should remain the most stable and least framework-dependent layer.

## Tests

The expected test shape is:

```text
tests/
  unit/
  integration/
  e2e/
```

- `unit/`: domain and small application services
- `integration/`: infrastructure adapters and CLI-to-service wiring
- `e2e/`: full workflows using realistic fixtures

## What should stay out of `src/`

- historical compatibility code that exists only to preserve `legacy/` behavior temporarily
- large generated outputs
- ad hoc research notes that belong in `docs/`
- raw external datasets

## Review rule

Any change that crosses these boundaries or introduces a new top-level architectural concept should be documented through an ADR in [`../adr/`](../adr/).
