# Specification: `srs-game-gen` Synthetic-Game Methodology

## Summary

This document specifies the current synthetic-game workflow exposed through the root `srs-game-gen` CLI at a level suitable for papers, appendices, and research notes.

It covers:

- simulation settings
- game-score and base-rank generation
- ranking-rule output generation
- randomization
- rank-correlation handling

## Scope

This specification covers the root-supported commands:

- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen rank-game`
- `srs-game-gen make-figures`
- `srs-game-gen rank-heatmap`
- `srs-game-gen rule-corr-heatmap`

Out of scope:

- archive-only axiom-checking and related historical commands

## 1. Simulation settings

### 1.1 Number of players

- specified by `--players` / `-p`
- current CLI range: `1 <= n <= 12`

### 1.2 Number of games

- specified by `--count` / `-c`
- default: `config.gen_games.count`
- fallback default: `1`

### 1.3 Maximum score

- specified by `--max-score`
- default: `config.gen_games.max_score`
- fallback default: `2^n - 1`

### 1.4 Output base

- specified by `--out`
- default: `config.output_base`
- fallback default: `outputs`

### 1.5 Config precedence

The root CLI resolves configuration in this order:

1. explicit CLI arguments
2. explicit YAML passed with `--config <path>`
3. built-in defaults from `src`

The root CLI does not implicitly read `legacy/config.yaml` or repository-level `./config.yaml`.

## 2. Game generation

### 2.1 Game definition

Each generated game is treated as a complete cooperative game over `N = {1, ..., n}`.

- coalitions are represented by bitmasks
- `player1` corresponds to bit 0, `player2` to bit 1, and so on
- each game contains all `2^n` coalitions

### 2.2 Score generation

For each coalition `S ⊆ N`, the workflow independently samples an integer coalition score.

- RNG: `random.Random(seed)`
- distribution: discrete uniform on `{0, 1, ..., M}`
- `M = max_score`

Implementation-wise, the workflow calls `rng.randint(0, max_score)` once per coalition mask.

Important note:

- the empty coalition is randomized in the same way as other coalitions
- the current root workflow does not enforce `v(∅)=0`
- no monotonicity, superadditivity, convexity, or similar structural game constraints are imposed

So the current root synthetic workflow samples unconstrained complete game tables from an iid discrete-uniform coalition-score model.

### 2.3 Multiple games and RNG consumption

When `--count K` is used:

- one `random.Random(seed)` instance is created for the whole workflow
- games are generated sequentially
- each game consumes the next segment of the same RNG stream

Therefore, the tuple `(n, count, max_score, seed)` determines a reproducible sequence of game CSV files.

### 2.4 File naming

Generated files are written as `game_000001.csv`, `game_000002.csv`, and so on.

- if files already exist, the workflow fills the lowest unused indices
- filenames are therefore stable, but the RNG stream still depends on execution order

## 3. Base-rank generation

### 3.1 Row order

Rows in the game CSV are written in the following order:

1. descending coalition score
2. ascending coalition bitmask as a deterministic tie-break

### 3.2 Base `rank` column

The base `rank` column in the game CSV is a dense descending rank over coalition scores.

- best score gets rank `1`
- ties share the same rank
- the rank increases by `1` when the score value changes

Example:

- `score = [10, 10, 8, 3, 3]`
- `rank = [1, 1, 2, 3, 3]`

This base `rank` column is the coalition-score rank of the generated game itself, not a rule-specific ranking output.

## 4. Ranking-rule output generation

### 4.1 Current root-supported rules

If `srs-game-gen apply-rules` is called without explicit `--rule` arguments, it applies all rules in the current default registry:

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`

### 4.2 Rule meanings

#### `shapley`

For each player `i`, sum the marginal contributions

`v(S ∪ {i}) - v(S)`

over all `S ⊆ N \\ {i}`, weighted by the Shapley coefficient

`|S|! (n-|S|-1)! / n!`.

#### `banzhaf`

For each player `i`, sum

`v(S ∪ {i}) - v(S)`

over all `S ⊆ N \\ {i}` and divide by `2^(n-1)`.

#### `lexcel`

Assign score levels `1, 2, ...` to distinct coalition scores from best to worst. For each player, build a `theta` vector counting how many coalitions containing that player appear at each level. Rank players by lexicographic descending comparison of these vectors.

#### `ordinal_banzhaf`

Assign score levels `1, 2, ...` to distinct coalition scores from best to worst. For each player `i`, count:

- `u_plus(i)`: cases where adding `i` improves the coalition level
- `u_minus(i)`: cases where adding `i` worsens the coalition level

and define the score as

`u_plus(i) - u_minus(i)`.

### 4.3 Internal ranks vs serialized CSV ranks

The rule implementations internally produce dense player ranks:

- `shapley`, `banzhaf`, `ordinal_banzhaf`: dense descending rank of player scores
- `lexcel`: dense lexicographic descending rank of the `theta` vectors

However, the serialized `rank_*` columns in the rankings CSV depend on `--rank-style`:

- default: `competition`
- alternative: `dense`

Under `competition`, ties leave gaps:

- dense: `1, 1, 2, 3`
- competition: `1, 1, 3, 4`

### 4.4 How `rank_*` and `score_*` columns are filled

All currently migrated synthetic rules are player-scope rules. Therefore, in the rankings CSV:

- `score_*` and `rank_*` values are written only on singleton rows
- all non-singleton coalition rows are left blank for those rule columns

Current compatibility column names are:

- `score_shapley`, `rank_shapley`
- `score_banzhaf`, `rank_banzhaf`
- `rank_lexcel`
- `rank_o-banzhaf`

`ordinal_banzhaf` internally computes a score, but the current compatibility CSV serialization does not write a `score_o-banzhaf` column.

## 5. Meaning of `make-figures`

`srs-game-gen make-figures` renders PNG table figures from rankings CSV files.

- input: `outputs/rankings/**/game_*.csv`
- output: `outputs/figures/**/game_*.png`

The command reorganizes and renders:

- the base coalition `rank` and `score`
- the available `rank_*` columns

It does not compute new correlation statistics or additional ranking summaries.

## 6. Rank-correlation handling

### 6.1 Current root `srs-game-gen`

The current root-supported `srs-game-gen` surface includes:

- `srs-game-gen rank-heatmap`
- `srs-game-gen rule-corr-heatmap`

Both commands first convert historical `rank_*` columns into effective ranks instead of comparing the serialized rank labels directly.

The effective rank uses the competition-style definition:

`effective_rank(A) = 1 + |{B : rank(B) < rank(A)}|`

This absorbs differences between dense and serialized competition ranks and compares tied items by the start position of each tie block.

### 6.2 `rank-heatmap`

`rank-heatmap` takes one pair of `rank_*` columns and counts the frequency of effective-rank pairs `(r_x, r_y)`, then renders the result as a 2D heatmap.

In the current implementation:

- player-scope rules use singleton rows only
- coalition-scope rules use non-empty coalition rows
- the default pair is `rank_lexcel` versus `rank_shapley`
- if config sets `rank_heatmap.pairs: all` or `auto`, all within-scope pairs are rendered

The default output directory is `outputs/heatmaps/nN/`.

### 6.3 `rule-corr-heatmap`

`rule-corr-heatmap` vertically concatenates rankings CSV files and computes a rule-by-rule correlation matrix over effective-rank columns.

The computation is:

1. convert each `rank_*` column, per file, into effective ranks
2. restrict player-scope rules to singleton rows and coalition-scope rules to non-empty coalition rows
3. concatenate the selected rows across files
4. compute the rule-by-rule matrix with `pandas.DataFrame.corr(method=...)`

The default method is `spearman`. It can be overridden by CLI `--method` or by config `rule_corr_heatmap.method`.

### 6.4 Relationship to the historical archive

The historical archive command `legacy game-gen rule-corr-heatmap` used the following method:

1. convert each `rank_*` column, per file and per column, into an effective competition-style rank  
   `effective_rank(A) = 1 + |{B : rank(B) < rank(A)}|`
2. restrict to singleton rows for player rules, or non-empty coalition rows for coalition rules
3. concatenate the selected rows across all ranking CSV files
4. apply `pandas.DataFrame.corr(method=...)`
5. use `spearman` by default

The current root implementation is an explicit migration of this historical method into `src/`. In papers, it can now be described as part of the current root-supported workflow.

## 7. Reproducibility checklist

For papers and appendices, record at least:

- commit hash
- command line
- `n`
- `count`
- `max_score`
- `seed`
- `rank_style`
- applied rule list
- YAML contents when `--config` is used

## 8. Recommended paper wording

One concise description of the current root workflow is:

> We generated complete cooperative games with `2^n` coalitions. For each coalition, we sampled an integer score independently and uniformly from `{0, ..., M}` using Python's `random.Random(seed)`. Coalition rows were ordered by descending score with bitmask-based tie-breaking, and the base coalition rank column was assigned as a dense descending rank. Player-level ranking rules were then applied to each generated game, and their serialized output ranks were reported in competition-rank format unless otherwise specified.

## Related documents

- [`../../README.md`](../../README.md)
- [`../../src/README.md`](../../src/README.md)
- [`../research-workflow.md`](../research-workflow.md)
- [`../adr/0002-retire-legacy-only-synthetic-commands.md`](../adr/0002-retire-legacy-only-synthetic-commands.md)
- [`../adr/0003-reintroduce-synthetic-rank-correlation-commands.md`](../adr/0003-reintroduce-synthetic-rank-correlation-commands.md)
- [`../../legacy/docs/design/heatmaps.md`](../../legacy/docs/design/heatmaps.md)
