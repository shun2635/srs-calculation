# Chapter 5 extensions: n-sweep and divergence analysis

Material for the paper's Chapter 5. These are the two additive analyses from
issue #22, run on the protected codebase (the default single-n
`paper-simulation` output and the pinned baseline numbers are unchanged).

**Numbers are reported as-is; interpretation is deferred to the manuscript.**

All runs use `seed=42`. Reproduce with:

```bash
srs-game-gen paper-n-sweep --out outputs/paper/ch5_extensions
srs-game-gen paper-divergence --players 5 --count 1000 --out outputs/paper/ch5_extensions
```

Generated artifacts (regenerable, under the git-ignored `outputs/`):
`outputs/paper/ch5_extensions/results/*.csv`, `.../figures/*.pdf`,
and `.../results/*metadata*.json` (each records the git commit, all parameters,
and the per-n game counts).

Fixed specs unchanged (see `application/paper_simulation/fixed_specs.py`):
Reversal fires only on a strict coalition ordering; a tied rule output is
unsatisfied; the main-text adequacy value is the **macro** average; the n=5 row
reproduces the canonical baseline exactly (firing cases 43071, Rankdiff Reversal
macro/micro = 1.0, GL-vs-Rankdiff Spearman = 0.5568).

## Experiment settings

- n-sweep: n = 3..7, R = 1000 for n ≤ 6 and R = 500 for n = 7 (work grows as
  2^n; n = 8 is supported via `--count-for 8:R` but excluded from the default
  sweep). Correlation = Spearman, rank-tie = dense, empty-constraints = exclude.
- Divergence: n = 5, R = 1000 (3000 game×size records over k ∈ {2, 3, 4}).

## RQ1: Group Lex-cel vs Rankdiff correlation, and its n-sensitivity

Overall Spearman correlation (over valid game-size rows), by n:

| n | R | GL vs Rankdiff Spearman (overall) |
|---|---|---|
| 3 | 1000 | 0.8416 |
| 4 | 1000 | 0.6789 |
| 5 | 1000 | 0.5568 |
| 6 | 1000 | 0.4607 |
| 7 | 500 | 0.3796 |

The correlation decreases monotonically as n grows over the swept range.

## RQ2: Reversal adequacy, and its n-sensitivity

Rankdiff is fully Reversal-consistent at every n (macro = micro = 1.0). Firing
cases (total Reverse-Axiom constraints) grow with n:

| n | firing cases | Rankdiff Reversal (macro / micro) |
|---|---|---|
| 3 | 1209 | 1.0000 / 1.0000 |
| 4 | 8901 | 1.0000 / 1.0000 |
| 5 | 43071 | 1.0000 / 1.0000 |
| 6 | 172770 | 1.0000 / 1.0000 |
| 7 | 319631 | 1.0000 / 1.0000 |

Reversal consistency (macro) per rule across n:

| Rule | n=3 | n=4 | n=5 | n=6 | n=7 |
|---|---|---|---|---|---|
| Group Lex-cel | 1.0000 | 0.8072 | 0.7073 | 0.6437 | 0.5985 |
| Rankdiff | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Group Shapley Value | 0.4041 | 0.5515 | 0.5902 | 0.6141 | 0.6196 |
| Shapley Interaction Index | 1.0000 | 0.7424 | 0.6456 | 0.5979 | 0.5761 |
| Banzhaf Interaction Index | 1.0000 | 0.7376 | 0.6060 | 0.5553 | 0.5330 |

Group Lex-cel's adequacy (macro) decreases monotonically with n over the swept
range (micro tracks it: 1.0000 / 0.8210 / 0.7171 / 0.6481 / 0.6005). Group
Shapley Value increases with n; the interaction indices decrease.

## Divergence conditions (n = 5, R = 1000)

Divergence measure: per game and size k, the GL-vs-Rankdiff **disagreement rate**
= discordant coalition pairs / total pairs. Correlation of each structural
feature with the disagreement rate, pooled over all k and controlled per k:

Pooled over k (n = 3000):

| Feature | Pearson | Spearman |
|---|---|---|
| num_reversal_pairs (Reverse-Axiom firing pairs) | +0.588 | +0.596 |
| num_distinct_levels | +0.677 | +0.642 |
| max_level_class_size | +0.370 | +0.398 |
| score_range | +0.286 | +0.274 |
| score_variance | +0.022 | +0.038 |
| k | −0.749 | −0.770 |

`num_reversal_pairs` vs disagreement rate, per k (each n = 1000):

| k | Pearson | Spearman |
|---|---|---|
| 2 | −0.049 | −0.037 |
| 3 | −0.094 | −0.100 |
| 4 | −0.206 | −0.196 |

### Connection to the Chapter 4 prediction (numbers only)

The Chapter 4 prediction is that inputs with more synergy / individual-vs-group
reversal structure diverge more. Pooled over k, the number of Reverse-Axiom
firing pairs is positively correlated with the disagreement rate
(Pearson +0.588). Controlling for k, that correlation vanishes to weakly negative
(k=2: −0.049, k=3: −0.094, k=4: −0.206); k itself is strongly negatively
correlated with the disagreement rate (Pearson −0.749). No interpretation is
fixed here.
