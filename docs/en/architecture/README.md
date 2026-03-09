# Target Architecture Documents

This directory contains the architecture documents for the new implementation under [`../../../src/`](../../../src/).

## Role of this directory

- define the target package boundaries
- document migration decisions from `legacy/`
- give contributors a stable architectural reference during collaborative development

## Reading order

1. [`module-boundaries.md`](module-boundaries.md)
2. [`migration-from-legacy.md`](migration-from-legacy.md)
3. [`legacy-removal-runbook.md`](legacy-removal-runbook.md)
4. [`../../../src/README.md`](../../../src/README.md)

The runbook is kept to document how runtime decoupling from `legacy/` was achieved. It is no longer an active plan to delete the archive tree.

## Scope rule

These documents describe the target architecture for new code and the migration path toward it. They do not replace the historical snapshot in [`../architecture.md`](../architecture.md), which describes the archived `legacy/` codebase.
