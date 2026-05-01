# Paper Simulation Implementation Plan

## 0. 目的

AAMAS論文のSimulation Analysisに使う、Group Lex-cel / RP-Difference / Reversal lens を中心とした主分析を実装・実行する。

## 1. 論文定義

- Group Lex-cel: 各 group `G` について、ordinal coalition ranking の rank class ごとに `G` を含む coalition 数を数え、その appearance vector を辞書式降順で比較する。
- RP-Difference: 各 coalition の Rank Point `RP(S)` から、構成 singleton の平均 Rank Point を引いた `Delta^RP(G)` で group formation value を測る。
- Reversal lens: 個人としては `G` 側が `H` 側を弱く上回り、少なくとも1つの singleton 比較で厳密に上回る一方、group としては `H` が `G` に劣らないとき、formation value ranking は `H` を `G` より厳密に上位へ置くことを要求する。
- Reversal consistency rate: RP-Difference が Reversal constraint `(H,G)` のうち `H` を `G` より厳密に上位へ置く割合を測る。空 constraint は標準では平均から除外する。
- GL vs RP rank correlation: 各 game と group size `k` について、`X_k` 上の Group Lex-cel rank vector と RP-Difference rank vector の相関を測る。標準は Spearman、tie method は dense。

## 2. 実装方針

- 旧命名 `gekokujou` ではなく、新命名 `reversal` を正式名にする。
- 旧命名との互換は不要。
- 設定値は変更しやすくする。
- rule / lens / metric / figure generation を分離する。
- defaultは論文定義にする。
- optional parameter として変更可能なものはCLI/configで変更しやすくする。
- `legacy/` は歴史archiveとして残し、active surfaceである `src/`, `tests/`, root `docs/` を中心に更新する。

## 3. 実装タスク

1. Reversal lens 実装
2. Reversal consistency metric 実装
3. GL vs RP rank correlation metric 実装
4. paper simulation CLI / entrypoint 実装
5. CSV出力
6. figure出力
7. summary markdown出力
8. test / small run
9. 論文リポジトリへ渡す成果物整理

## 4. 出力仕様

今回の標準出力先は以下とする。

```text
outputs/paper/main/
  results/
  figures/
  docs/
```

標準成果物:

- `results/lens_consistency.csv`
- `results/lens_consistency_summary.csv`
- `results/rank_correlation.csv`
- `results/rank_correlation_summary.csv`
- `results/simulation_summary.csv`
- `results/experiment_metadata.json`
- `figures/reversal_consistency.pdf`
- `figures/reversal_consistency.png`
- `figures/rank_correlation_glc_rp.pdf`
- `figures/rank_correlation_glc_rp.png`
- `docs/simulation_result_summary.md`

## 5. 実験設定

標準設定は以下とする。

- `n = 5`
- `R = 1000`
- `seed = 42`
- `max_score = 2^n - 1`
- coalition values are generated independently as integers
- no monotonicity with respect to coalition size
- `X = 2^N \ {emptyset}`
- singletons are included

## 6. 後で変更しやすくする項目

以下はCLI/configで変更しやすくする。

- `n`
- `R`
- `seed`
- `max_score`
- target group sizes `k`
- correlation method
- rank tie method
- empty-constraint handling

## 7. 実行コマンド

標準実行:

```bash
poetry run srs-game-gen paper-simulation \
  --players 5 \
  --count 1000 \
  --seed 42 \
  --out outputs/paper/main
```

smoke run:

```bash
poetry run srs-game-gen paper-simulation \
  --players 4 \
  --count 10 \
  --seed 1 \
  --out outputs/paper/smoke
```
