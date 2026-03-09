# Specification: `srs-game-gen` Synthetic-Game Methodology

## Summary

This document fixes the current `srs-game-gen` synthetic-game workflow at a level suitable for papers, appendices, and research notes.

It covers:

- simulation settings
- game generation and randomization
- base-rank and rule-specific rank generation
- the calculation methods behind `rank-heatmap` and `rule-corr-heatmap`
- the minimum information required for reproducibility

This is the English version. Its content is intended to stay synchronized with the [Japanese version](../../ja/specs/synthetic-game-methodology.md). When one changes, the other should be reviewed.

## Scope

This specification covers the root-supported synthetic commands:

- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen rank-game`
- `srs-game-gen make-figures`
- `srs-game-gen rank-heatmap`
- `srs-game-gen rule-corr-heatmap`

Out of scope:

- archive-only `game-gen check-axioms`
- archive-only `game-gen summarize-axioms`
- archive-only `game-gen axiom-summary-heatmap`
- archive-only `game-gen pipeline`
- archive-only `game-gen make-figures-png`

## 1. Workflow overview

The current synthetic workflow is normally used in four stages:

1. generate complete game CSV files with `srs-game-gen gen-games`
2. apply ranking rules with `srs-game-gen apply-rules`
3. render table figures with `srs-game-gen make-figures`
4. when needed, visualize rank comparisons with `srs-game-gen rank-heatmap` and `srs-game-gen rule-corr-heatmap`

The default output layout is:

- games: `outputs/games/nN/game_*.csv`
- rankings: `outputs/rankings/nN/game_*.csv`
- figures: `outputs/figures/nN/game_*.png`
- heatmaps: `outputs/heatmaps/nN/*.png`

Here `N` is the number of players.

## 2. Simulation settings

### 2.1 Number of players

- specified by `--players` or `-p`
- current CLI range: `1 <= n <= 12`
- each generated game is treated as a complete cooperative game with `n` players

### 2.2 Number of games

- specified by `--count` or `-c` in `gen-games`
- default: `config.gen_games.count`
- fallback default: `1`

### 2.3 Maximum score

- specified by `--max-score` in `gen-games`
- default: `config.gen_games.max_score`
- fallback default: `2^n - 1`

### 2.4 Output base

- specified by `--out`
- default: `config.output_base`
- fallback default: `outputs`

### 2.5 Config precedence

The root CLI resolves configuration in this order:

1. explicit CLI arguments
2. explicit YAML passed with `--config <path>`
3. built-in defaults from `src`

Notes:

- the root CLI does not implicitly read `legacy/config.yaml`
- it does not auto-discover repository-level `./config.yaml`
- when `output_base` is relative and `--config` is used, it is resolved relative to the config file location

## 3. Game generation

### 3.1 Game definition

Each synthetic game is represented as a complete cooperative game over `N = {1, ..., n}`.

- coalitions are encoded as bitmasks
- `player1` corresponds to bit 0, `player2` to bit 1, and so on
- each game contains all `2^n` coalitions

### 3.2 Random coalition-score generation

For each coalition `S ⊆ N`, the workflow independently samples a coalition score `v(S)`.

- RNG: Python standard-library `random.Random(seed)`
- distribution: discrete uniform on `{0, 1, ..., M}`
- where `M = max_score`

Implementation-wise, the workflow calls `rng.randint(0, max_score)` once per coalition mask and stores the result as `float`.

Important notes:

- the empty coalition is randomized in the same way as every other coalition
- the current workflow does not enforce `v(∅)=0`
- no monotonicity, superadditivity, convexity, simplicity, or similar structural game constraints are imposed

So the current root synthetic workflow samples unconstrained complete game tables from an iid discrete-uniform coalition-score model.

### 3.3 RNG consumption for multiple games

When `--count K` is used:

- one `random.Random(seed)` instance is created for the whole workflow
- games are generated sequentially
- each game consumes the next segment of the same RNG stream

Therefore, the tuple `(n, count, max_score, seed)` determines the reproducible random stream.

### 3.4 File naming and indexing

Generated files are named `game_000001.csv`, `game_000002.csv`, and so on.

- when files already exist, the workflow fills the smallest unused indices
- the numeric indices therefore depend on the existing directory state
- the RNG stream itself still depends on the execution order within the run

For paper-grade reproducibility, it is therefore more important to control the seed and generation parameters on a clean target directory than to rely only on filenames.

## 4. Game-CSV serialization rules

### 4.1 Row order

Coalition rows in the game CSV are written in the following order:

1. descending `score`
2. ascending coalition bitmask as a deterministic tie-break

This tie-break exists only to make equal-score ordering deterministic.

### 4.2 Base `rank` column

The game CSV `rank` column is the dense descending rank of coalition scores.

- best score gets rank `1`
- ties share the same rank
- the rank increases by `1` whenever the score value changes

Example:

- `score = [10, 10, 8, 3, 3]`
- `rank = [1, 1, 2, 3, 3]`

This base `rank` is the coalition-score rank of the generated game itself, not a rule-specific output.

### 4.3 Game-CSV columns

The default game-CSV header is:

- `player1`, `player2`, ..., `playerN`
- `score`
- `rank`

Each `playeri` column is a 0/1 coalition-membership indicator.

## 5. Ranking-rule application

### 5.1 Current root-supported rules

If `apply-rules` is called without explicit `--rule` arguments, it applies all rules in the current default registry:

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`
- `group_shapley`
- `group_sum_shapley`
- `group_ordinal_banzhaf`
- `group_lexcel`
- `shapley_interaction`
- `banzhaf_interaction`
- `rp_index`
- `ud`
- `du`
- `red_index`

### 5.2 `shapley`

For each player `i`, the workflow evaluates the marginal contribution

`v(S ∪ {i}) - v(S)`

over all `S ⊆ N \ {i}` and weights it by the Shapley coefficient

`|S|! (n-|S|-1)! / n!`.

The resulting player scores are then ranked by dense descending order.

### 5.3 `banzhaf`

For each player `i`, the workflow sums

`v(S ∪ {i}) - v(S)`

over all `S ⊆ N \ {i}` and divides by `2^(n-1)`.

The resulting player scores are then ranked by dense descending order.

### 5.4 `lexcel`

The workflow first assigns score levels `1, 2, ...` to distinct coalition-score values from best to worst.

For each player, it constructs a `theta` vector

`theta_i = (c_{i,1}, c_{i,2}, ..., c_{i,L})`

where `c_{i,l}` counts coalitions at level `l` that include player `i`.

Players are ranked by lexicographic descending comparison of these `theta` vectors. In the current compatibility CSV, `lexcel` writes only a rank column and no score column.

### 5.5 `ordinal_banzhaf`

The workflow first assigns score levels `1, 2, ...` to distinct coalition-score values from best to worst.

For each player `i` and each `S ⊆ N \ {i}`:

- count one `u_plus(i)` when adding `i` improves the level
- count one `u_minus(i)` when adding `i` worsens the level

The score is then defined as

`u_plus(i) - u_minus(i)`.

The resulting player scores are ranked by dense descending order.

### 5.6 Complete-game requirement

By default, `apply-rules` and `rank-game` require a complete game table.

- default behavior: `--require-complete`
- exception: incomplete tables are allowed only with `--allow-incomplete`

For normal synthetic-paper workflows, complete games should be assumed.

### 5.7 Coalition-scoped rules that depend on base `rank`

Not all migrated rules depend on the same input signal.

- `shapley`, `banzhaf`, `group_shapley`, `group_sum_shapley`, `shapley_interaction`, and `banzhaf_interaction` are cardinal and depend on coalition scores
- `ordinal_banzhaf`, `group_ordinal_banzhaf`, `group_lexcel`, `rp_index`, `ud`, `du`, and `red_index` depend on the serialized base `rank` / level structure

For synthetic games, the base `rank` column is derived from the generated scores, so these two views coincide. For imported real-data games, this distinction matters.

## 6. Rankings-CSV serialization rules

### 6.1 Base columns

The rankings CSV preserves the base game columns:

- `score`
- `rank`

These remain coalition-score columns, not rule-output columns.

### 6.2 Rule-output columns

Under the current compatibility format, rules are serialized as:

- `shapley` -> `score_shapley`, `rank_shapley`
- `banzhaf` -> `score_banzhaf`, `rank_banzhaf`
- `lexcel` -> `rank_lexcel`
- `ordinal_banzhaf` -> `rank_o-banzhaf`
- `group_shapley` -> `score_g-shapley`, `rank_g-shapley`
- `group_sum_shapley` -> `score_g-sum-shapley`, `rank_g-sum-shapley`
- `group_ordinal_banzhaf` -> `rank_g-o-banzhaf`
- `group_lexcel` -> `rank_g-lexcel`
- `shapley_interaction` -> `score_shapley-interaction`, `rank_shapley-interaction`
- `banzhaf_interaction` -> `score_banzhaf-interaction`, `rank_banzhaf-interaction`
- `rp_index` -> `score_rp-index`, `rank_rp-index`
- `ud` -> `score_ud_up`, `score_ud_down`, `rank_ud`
- `du` -> `score_du_up`, `score_du_down`, `rank_du`
- `red_index` -> `score_red-index`, `rank_red-index`

Notes:

- `ordinal_banzhaf` internally has a score, but the current compatibility CSV does not write `score_o-banzhaf`
- derived-column order is fixed by the canonical compatibility order

### 6.3 Player-scope vs coalition-scope serialization

The migrated synthetic rule family now contains both player-scope and coalition-scope rules.

- player-scope rules write `score_*` / `rank_*` only on singleton coalition rows
- coalition-scope rules write `score_*` / `rank_*` on all non-empty coalition rows
- the empty coalition row is left blank for coalition-scoped derived columns

This is a deliberate compatibility decision inherited from the historical CSV surface.

### 6.4 `rank_style`

The internal rule ranks are dense ranks, but serialized `rank_*` columns depend on `--rank-style`.

- default: `competition`
- alternative: `dense`

Example:

- dense: `1, 1, 2, 3`
- competition: `1, 1, 3, 4`

When papers refer to serialized rule ranks, they should state whether `competition` or `dense` formatting was used. The root default is `competition`.

## 7. Meaning of `make-figures`

`srs-game-gen make-figures` converts rankings CSV files into PNG table figures.

- input: `outputs/rankings/**/game_*.csv`
- output: `outputs/figures/**/game_*.png`

This command does not compute additional rank statistics or correlation statistics. It only renders:

- the base `score` and `rank`
- the available `rank_*` columns

## 8. Rank-correlation and rank-comparison methods

### 8.1 Effective-rank definition

`rank-heatmap` and `rule-corr-heatmap` do not compare serialized rank labels directly. They first convert each `rank_*` column into an effective rank.

The definition is:

`effective_rank(A) = 1 + |{B : rank(B) < rank(A)}|`

This is the number of strictly better items plus one, corresponding to the start position of the competition-style tie block.

This preprocessing:

- absorbs representation differences between dense and competition ranks
- stabilizes comparisons in the presence of ties

### 8.2 Scope handling

The plotting code infers a scope for each rank column.

- if a rank column has values outside singleton rows, it is treated as coalition-scope
- if values appear only on singleton rows, it is treated as player-scope

The current migrated rule family contains both scopes, so player and coalition heatmaps may both exist depending on which columns are present.

### 8.3 `rank-heatmap`

For a selected pair of rank columns `x_col` and `y_col`, `rank-heatmap` performs the following, file by file:

1. restrict rows to the target scope
2. keep only rows where both `x_col` and `y_col` are non-null
3. convert `x_col` and `y_col` separately into effective ranks within that file and valid row subset
4. count the frequency of each effective-rank pair `(r_x, r_y)`
5. sum those frequencies across files

The result is rendered as a frequency matrix heatmap.

Current defaults:

- default pair: `rank_lexcel` vs `rank_shapley`
- default output: `outputs/heatmaps/nN/<x_col>_vs_<y_col>.png`
- default DPI: `150`

Config `rank_heatmap.pairs` can also be used:

- explicit list: fixes the pairs to render
- `all` or `auto`: renders every within-scope pair

### 8.4 `rule-corr-heatmap`

`rule-corr-heatmap` computes rule-by-rule correlation matrices by vertically concatenating rankings CSV files.

The computation is:

1. for each file, convert each `rank_*` column into effective ranks on the valid rows for its scope
2. restrict player-scope rules to singleton rows and coalition-scope rules to non-empty coalition rows
3. concatenate the resulting effective-rank tables across files
4. compute the rule-by-rule matrix with `pandas.DataFrame.corr(method=..., min_periods=1)`

Correlation method:

- default: `spearman`
- override via CLI `--method`
- also configurable through `rule_corr_heatmap.method`

Outputs are scope-specific:

- `rule_corr_player.png` if player-scope columns exist
- `rule_corr_coalition.png` if coalition-scope columns exist

With the current migrated synthetic rules, both `rule_corr_player.png` and `rule_corr_coalition.png` may be produced.

### 8.5 Relation to the historical method

This rank-correlation method is an explicit migration into `src/` of the approach historically implemented in `legacy/src/gamegen/rank_heatmap.py`.

Therefore, papers may describe it either as:

- the current root-supported workflow method
- a historically derived method that has been explicitly reimplemented in `src/`

At the current repository state, it is accurate to describe it as part of the present root-supported workflow.

## 9. Important CLI defaults

For paper-grade reproducibility, the following defaults should not be left implicit.

- `apply-rules --rank-style` defaults to `competition`
- `rank-heatmap --dpi` defaults to `150` or `config.figures.png_dpi`
- `rule-corr-heatmap --method` defaults to `spearman`
- `make-figures --dpi` defaults to `150` or `config.figures.png_dpi`

## 10. Minimum reproducibility record

At minimum, keep:

- repository commit hash
- full CLI commands
- `players`
- `count`
- `max_score`
- `seed`
- `rank_style`
- applied rule list
- YAML contents when `--config` is used
- preserved output directory

## 11. Concise paper-ready method paragraph

One compact formulation is:

> We generated complete cooperative games with `2^n` coalitions for `n` players. Each coalition score was sampled independently and uniformly from `{0, ..., M}` using Python's `random.Random(seed)` without imposing structural game constraints such as monotonicity or convexity. Coalition rows were ordered by descending score with a bitmask-based deterministic tie-break, and the base coalition-rank column was assigned as a dense descending rank. We then applied player-level ranking rules and serialized their output ranks in competition-rank format unless otherwise stated. For rank-comparison analyses, we transformed each serialized `rank_*` column into an effective rank defined by `1 + |{B : rank(B) < rank(A)}|`, and computed pairwise heatmaps or rule-correlation matrices from those effective ranks.

## Related documents

- [`../../README.md`](../../README.md)
- [`../../src/README.md`](../../src/README.md)
- [`../research-workflow.md`](../research-workflow.md)
- [`../adr/0002-retire-legacy-only-synthetic-commands.md`](../adr/0002-retire-legacy-only-synthetic-commands.md)
- [`../adr/0003-reintroduce-synthetic-rank-correlation-commands.md`](../adr/0003-reintroduce-synthetic-rank-correlation-commands.md)
- [`../../legacy/docs/design/heatmaps.md`](../../legacy/docs/design/heatmaps.md)
