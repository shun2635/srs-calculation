# CLAUDE.md

Guidance for Claude (and humans) working in this repository. Read this before
making changes — especially the **Fixed specifications** and **Working rule**
sections, which protect results the paper depends on.

## Project overview

This repository is the empirical implementation behind a paper on **group
evaluation over ordinal information** (cooperative-game / coalition-ranking
simulation). It supports **Chapter 5** of the paper (AAMAS submission, drafted in
the separate `paper_gsrs` repository). The headline analysis is the
**paper-simulation** workflow: it generates random coalition games and measures,
for several ranking rules, their consistency with axiomatic *lenses* (chiefly the
Reverse Axiom) and the rank correlation between the two focal rules.

The paper is the source of truth for the definitions. **The implementation
conforms to the paper, not the other way around.** When code and paper disagree,
the paper wins and the code is fixed.

## Paper correspondence

| Concept | Confirmed definition | Where in code |
|---|---|---|
| **Rank value** `r(C)` | `r(C) = |{C' : C' ≻ C}|` — number of coalitions strictly above `C`. Ties are **not** counted; smaller is more preferred; the top has `r = 0`. Counted over the whole non-empty coalition pool. | `domain/ranking/rules/rankdiff.py` (`better_count_by_rank`) |
| **Rankdiff** | `Rankdiff(S) = (1/|S|) · Σ_{i∈S} r({i}) − r(S)` (mean individual rank value − team rank value; larger = more synergy). Compare with `Rankdiff(S) ≥ Rankdiff(U)`. | `domain/ranking/rules/rankdiff.py` |
| **Reverse Axiom firing** | Same-size `S, T`: fires when (1) `T` individually dominates `S` (a bijection σ with `{σ(i)} ≽_ind {i}` for all members, at least one strict) **and** (2) the coalition ordering has `S` **strictly** above `T`. Required output: strict `S ≻^R T`. Group-rank ties do **not** fire. | `domain/lenses/reversal.py` |
| **Adequacy / consistency** | Of the firing cases, the fraction whose rule output matches the required strict `S ≻^R T`. A **tied** output (`S ∼^R T`) counts as **NOT satisfied**. Main-text value is the **macro** (per-game equal-weight) average; the **micro** (case-weighted) average is reported alongside. | `application/paper_simulation/metrics.py`, `lens_catalog.py` |
| **Group Lex-cel** | One of the two focal rules (lexicographic comparison over coalition levels). | `domain/ranking/rules/group_lexcel.py` |
| **Cardinal benchmarks** | Group Shapley Value, Shapley Interaction Index, Banzhaf Interaction Index — used to place the focal comparison in a broader rule space; not focal. | `domain/ranking/rules/` |

The declared, non-negotiable subset of these is mirrored as constants in
`application/paper_simulation/fixed_specs.py`.

## Architecture

Clean-ish layering under `src/srs_calculation/`:

- **domain/** — pure model and algorithms, no IO.
  - `games/coalition_game.py` — immutable coalition game (bitmask coalitions, base levels).
  - `ranking/` — `rule.py` (`RankingRule` ABC), `rules/*.py`, `registry.py` (rule registry), `result.py`.
  - `lenses/reversal.py` — Reverse Axiom constraint generation.
  - `axioms/` — weak-N axiom evaluators (Up/Down/Redundancy) + registry.
- **application/** — workflows.
  - `paper_simulation/` — the main workflow. See its sub-modules below.
- **infrastructure/** — `persistence/` (CSV repos), `plotting/` (figures/heatmaps).
- **interfaces/cli/** — Click CLIs (`game_gen.py` hosts `paper-simulation`).

### paper_simulation modules (the extension points)

- `config.py` — `PaperSimulationConfig`, all defaults (`DEFAULT_*`) and choices (single source).
- `rule_catalog.py` — the **rule catalog**: one entry per paper rule (label, roles, instance-from-registry).
- `lens_catalog.py` — the **lens catalog**: `PaperLens` ABC + `ReversalLens`/`AxiomLens`, one registry.
- `aggregation.py` — the **aggregation axis** (`group_by_k_with_overall`), decoupled from the metric calc.
- `metrics.py` — focal metric calculations + per-group reducers (macro/micro, correlation).
- `full_comparison.py` — full rule×lens heatmap observations and matrix summaries.
- `schema.py` — single source for CSV column schemas.
- `fixed_specs.py` — immutable, non-configurable specs (see below).
- `run.py` — orchestrator: generate → evaluate → aggregate → write CSV/figures/markdown/metadata.

### How to extend (before → after)

- **Add a ranking rule to the paper analyses.** Register the algorithm once in
  `domain/ranking/registry.py`, then add **one** `PaperRuleSpec` entry to
  `PAPER_RULE_CATALOG` in `rule_catalog.py` (label + roles); if it appears in a
  heatmap, also list its id in that heatmap's display-order tuple. It then flows
  automatically into evaluation, both heatmaps, focal selection.
  *Before this refactor: ~5–6 edit sites (two hard-coded spec tuples, etc.).*
- **Add a lens.** Implement `PaperLens.counts(...)` and register **one** object
  in `PAPER_LENS_CATALOG` in `lens_catalog.py`. It flows into consistency
  measurement and the heatmap automatically.
  *Before: a `reversal` special-case branch plus a separate axiom dict.*
- **Add an aggregation axis (e.g. an n-sweep).** Add a new grouping function in
  `aggregation.py` (like `group_by_k_with_overall`); the reducers and metric
  calculations are untouched. (No n-axis exists yet — that is issue #22.)

## Fixed specifications (DO NOT make configurable)

Declared in `application/paper_simulation/fixed_specs.py`. These encode the
paper's correctness and must never be turned into config fields / CLI flags:

- `REVERSAL_STRICT_GROUP_ORDERING = True` — Reverse Axiom fires only on a
  **strict** coalition ordering `S ≻ T` (group-rank ties do not fire).
- `OUTPUT_TIES_COUNT_AS_UNSATISFIED = True` — a tied rule output is **not**
  satisfied; only a strict `S ≻^R T` counts.
- `RANK_VALUE_TIES_NOT_COUNTED = True` — `r(C)` counts strictly-better
  coalitions only.
- `RANKDIFF_DEFINITION` — the Rankdiff formula above.
- `MAIN_TEXT_ADEQUACY_AVERAGE = "macro"` — the headline adequacy value is the
  macro average (micro reported alongside).
- The default **seed is fixed at 42** for reproducibility.

`test_fixed_specs.py` asserts these values and that none leak into
`PaperSimulationConfig`.

## Reproducibility

Run the main simulation (defaults already match the paper run):

```bash
.venv/bin/python -m srs_calculation.interfaces.cli.game_gen paper-simulation --out outputs/paper/main
# or, if installed: srs-game-gen paper-simulation --out outputs/paper/main
```

Default parameters: `players=5`, `count=1000`, `seed=42`,
`max_score=2^players−1=31`, `target_sizes=2..players`,
`correlation_method=spearman`, `rank_tie_method=dense`,
`empty_constraints=exclude`.

**Confirmed baseline numbers (seed=42, n=5, R=1000):**

| Metric | Value |
|---|---|
| Rankdiff Reversal consistency — macro | **1.0000** (exact) |
| Rankdiff Reversal consistency — micro | **1.0000** (exact) |
| Reversal firing cases (total constraints) | **43071** (exact) |
| Group Lex-cel Reversal — macro | **0.7073** |
| Group Lex-cel Reversal — micro | **0.7171** |
| Group Lex-cel vs Rankdiff Spearman (overall) | **0.5568** |

Each run writes `results/experiment_metadata.json` containing the `git_commit`,
the full `config`, and the `command_options` used — check it to confirm which
code/parameters produced a given output directory.

## Testing

```bash
.venv/bin/pytest -q          # full suite (includes the slow baseline pin)
.venv/bin/pytest -q -m "not slow"   # skip the ~9s paper-simulation pin
.venv/bin/ruff check src tests
.venv/bin/mypy src
```

- The regression safety net is
  `tests/unit/application/paper_simulation/test_paper_baseline_numbers.py`
  (marker: `slow`). It runs the real `run_paper_simulation` at the canonical
  settings and pins the numbers above (exact for the theorem value 1.0 and the
  firing count; `abs=1e-4` for the rest).

## Working rule (most important hand-off)

When refactoring or adding features here:

1. **Keep `test_paper_baseline_numbers.py` green.** Run it (i.e. the full
   `pytest`) before and after every change.
2. **If a baseline number moves, STOP and report.** Do not edit the expected
   numbers to make a refactor pass, and do not silently continue — investigate
   what changed. The numbers are the source of truth.
3. Behaviour-preserving refactors only, unless the task explicitly changes
   behaviour and the paper definition that justifies it.
4. Commit in logical units; do not push unless asked.

## Known baseline issues (out of scope)

The repository has **pre-existing** `ruff` (~141) and `mypy` (~60) findings,
largely missing third-party stubs (`pandas`, `yaml`) and long lines in legacy /
plotting / CLI modules. These predate the current work and are **out of scope**.
The rule for new work: do not add new findings, and leave any file you touch
clean. The `legacy/` tree is a retained archive and is not maintained.
