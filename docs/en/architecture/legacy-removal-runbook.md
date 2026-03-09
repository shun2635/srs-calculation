# Legacy Removal Runbook

This document defines the concrete order for reaching a state where the root CLI continues to work even if `legacy/` is removed from the repository.

It is more operational than [`migration-from-legacy.md`](migration-from-legacy.md). Use this document when planning or reviewing actual removal work.

## Target state

The repository reaches the target state only when all of the following are true:

- the root Poetry project is the only supported runtime entry point
- all supported researcher workflows run through `src/` only
- root tests pass without adding `legacy/src` to `sys.path`
- removing the `legacy/` directory does not break `real-gen`, `srs-game-gen`, or `srs-test`
- collaborator-facing docs no longer require `legacy/` for normal operation

## Current blockers

As of now, the main blockers are:

- parity tests still import `legacy` modules directly
- test bootstrap still injects `legacy/src` into `sys.path`
- `src/` still exposes historical file formats and naming at the compatibility boundary
- some collaborator docs still treat `legacy/` as the practical CLI reference
- the root CLI surface is still intentionally partial for synthetic workflows

These blockers should be removed in order, not all at once.

## Removal sequence

### Step 1. Freeze the public root CLI contract

Goal:

- decide which commands must remain supported after `legacy/` disappears

Required work:

- list the supported root commands in `README.md` and `src/README.md`
- explicitly mark unsupported or deferred `legacy` commands
- keep the root script names stable during the migration

Exit criteria:

- there is one authoritative list of supported root commands
- no open ambiguity remains about whether users should call root or `legacy` first

### Step 2. Remove `legacy` from collaborator-facing primary docs

Goal:

- make `docs/` and the root README sufficient for normal use

Required work:

- rewrite quick-start sections so they do not require `cd legacy`
- move command examples needed for current workflows into root docs
- keep `legacy` links only for archive or mathematical appendix purposes

Exit criteria:

- a collaborator can install dependencies, run the supported root CLI, and run tests without opening `legacy/README.md`

### Step 3. Replace direct `legacy` test imports with frozen fixtures

Goal:

- remove code-level test dependence on `legacy/src`

Required work:

- replace parity tests that import `gamegen.*` with checked-in fixture data
- store expected rule outputs as CSV, YAML, or Python fixtures under `tests/fixtures/`
- keep the parity intent, but compare against frozen expected outputs instead of live `legacy` execution

Files to retire from the dependency path:

- `tests/conftest.py` path injection for `legacy/src`
- parity tests that import `gamegen.rules.*`

Exit criteria:

- `tests/` no longer imports from `legacy`
- `poetry run srs-test` passes with only `src/` on the test path

### Step 4. Isolate compatibility-format I/O as an explicit compatibility layer

Goal:

- keep backward-compatible file handling without requiring the `legacy` project

Required work:

- keep compatibility code inside `src/srs_calculation/infrastructure/persistence/`
- document that historical CSV support is a compatibility format, not a package dependency
- avoid spreading compatibility-format assumptions further into `domain/` or `application/`

Exit criteria:

- all remaining uses of the word `legacy` inside `src/` refer only to compatibility formats or migration notes
- no `src/` runtime path requires files from the `legacy/` directory

### Step 5. Close the synthetic CLI gap

Goal:

- make the root-published CLI surface sufficient for supported synthetic workflows

Required work:

- either migrate the remaining required `game-gen` commands into `src/`
- or explicitly retire them and remove them from supported workflow docs
- add integration and e2e coverage for every retained root CLI workflow

Current decision:

- `check-axioms`, `summarize-axioms`, `axiom-summary-heatmap`, `rank-heatmap`, `rule-corr-heatmap`, `pipeline`, and `make-figures-png` are retired from the root contract and treated as archive-only under `legacy/`

Exit criteria:

- every command advertised in the root README runs through the root Poetry project only
- no supported workflow requires `legacy/pyproject.toml`

### Step 6. Remove config fallbacks that imply `legacy/` as the default runtime home

Goal:

- ensure runtime configuration is resolved from the root project and explicit CLI arguments only

Required work:

- audit docs and code for wording or defaults that point users to `legacy/config.yaml`
- move any still-needed defaults into root config conventions or built-in defaults
- document the supported root config lookup order

Exit criteria:

- normal root CLI usage does not rely on files under `legacy/`

Current implementation note:

- the supported root config lookup order is: explicit CLI arguments -> explicit `--config <path>` -> built-in defaults
- there is no implicit lookup of `legacy/config.yaml`
- there is no implicit lookup of repository-level `./config.yaml`

### Step 7. Prove removability in CI and local verification

Goal:

- verify that `legacy/` is no longer required in practice

Required work:

- add a verification job or script that temporarily hides or renames `legacy/`
- run `poetry run real-gen --help`
- run `poetry run srs-game-gen --help`
- run `poetry run srs-test`
- run the e2e suite

Recommended verification command shape:

```bash
poetry run srs-test
poetry run srs-test tests/e2e -q
poetry run real-gen --help
poetry run srs-game-gen --help
```

Exit criteria:

- the verification passes with `legacy/` absent from the runtime path

### Step 8. Remove published `legacy` entry points and archive the tree

Goal:

- finish the transition without breaking the supported root path

Required work:

- stop documenting `legacy/pyproject.toml` as a runnable entry point
- move `legacy/` to archive status or remove it from the repo
- update migration docs to reflect that `src/` is now authoritative

Exit criteria:

- the repository no longer presents `legacy` as a normal execution surface
- all authoritative docs describe `src/` as the implementation of record

## Recommended batching

Do not try to do this in one PR.

Recommended PR order:

1. docs and CLI contract clarification
2. parity-fixture migration and test bootstrap cleanup
3. remaining synthetic CLI migration or retirement
4. removability verification in CI
5. final archival or deletion of `legacy/`

## Review checklist

Reviewers should reject a removal PR if any of the following is still true:

- root tests still import from `legacy`
- supported root commands are still documented only in `legacy/README.md`
- a root CLI command still fails when `legacy/` is hidden
- the change mixes compatibility-format cleanup with unrelated refactors

## Non-goal

This runbook does not require the repository to abandon compatibility-format CSV column names immediately.

Those compatibility names may remain in `src/` after `legacy/` is removed, as long as they are treated as a compatibility format owned by the new implementation.
