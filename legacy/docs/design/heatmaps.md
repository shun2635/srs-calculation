# ヒートマップ設計

このドキュメントは、現行実装のヒートマップ出力の仕様（入力/変換/出力）をまとめる。

## 共通

### 入力

- 入力ディレクトリ: `<out>/rankings/nN/game_*.csv`
- `rank_*` 列はルール適用済みであること（`apply-rules` / `pipeline` が生成）

### 有効順位（tie 対策）

同順位が多いルール間では dense rank のままだと相関が歪みやすいため、ヒートマップ集計では各列を

```
effective_rank(A) = 1 + |{ B : rank(B) < rank(A) }|
```

（「対象より上位にいる数 + 1」）に変換して用いる。

- これは dense rank を competition rank（`1,1,3,4,...`）へ変換することに等しい。
- 変換は **ゲームCSVごと・列ごと**に行い、比較対象集合（個人: singleton / グループ: 非空提携）内で数える。

## 1) rank-heatmap（ペア別の頻度ヒートマップ）

### 目的

2つの順位列（`rank_x`, `rank_y`）の組み合わせ頻度を、ゲーム群を横断して集計して可視化する。

### 比較対象集合

- 個人ルール同士: singleton 行のみ
- グループ/提携ルール同士: 非空提携行のみ
- 混在（個人×グループ）はスキップ

### 出力

- 出力ディレクトリ: `<out>/heatmaps/nN/`
- ファイル: `<x_col>_vs_<y_col>.png`

### 設定

- `config.yaml:rank_heatmap.pairs`
  - `all`/`auto`: 個人ルール同士・グループルール同士の全組み合わせを自動生成
  - `[[col_x, col_y], ...]`: 指定ペアのみ生成
- `config.yaml:pipeline.rank_heatmaps`
  - `pipeline` / `apply-rules` 実行時に rank-heatmap を自動生成するか（既定: false）

### 実装

- CLI: `gamegen/commands/heatmaps.py:rank_heatmap`
- 集計: `gamegen/rank_heatmap.py:collect_rank_pairs` / `collect_group_rank_pairs`

## 2) rule-corr-heatmap（ルール×ルールの相関ヒートマップ）

### 目的

ルール同士の相関係数（相関の強さ）を、ルール×ルールの行列として可視化する。

### 比較対象集合

- 個人ルール同士（`RuleScope.PLAYER`）: singleton 行
- グループ/提携ルール同士（`RuleScope.COALITION`）: 非空提携行

### 相関

- 相関係数は `pandas.DataFrame.corr(method=...)` で計算
- 既定: Spearman（順位相関）

### 出力

- `<out>/heatmaps/nN/rule_corr_player.png`
- `<out>/heatmaps/nN/rule_corr_coalition.png`

### 設定

- `config.yaml:rule_corr_heatmap.method`（例: `spearman`, `pearson`）

### 実装

- CLI: `gamegen/commands/heatmaps.py:rule_corr_heatmap`
- 集計: `gamegen/rank_heatmap.py:collect_rule_correlation_matrix`
- 描画: `gamegen/rank_heatmap.py:render_correlation_heatmap`

## 3) axiom-summary-heatmap（公理 summary の適合率ヒートマップ）

### 目的

`outputs/axiom/nN/summary.csv`（ルール×公理の集計）を、行=ルール・列=公理・値=適合率で可視化する。

### 入力

- `outputs/axiom/nN/summary.csv`
  - 列: `rule, axiom, constraints, satisfied, satisfied_rate`

### 出力

- `outputs/axiom/nN/summary_heatmap.png`

### 実装

- CLI: `gamegen/commands/axioms.py:axiom_summary_heatmap`
- 描画: `gamegen/axioms/summary_heatmap.py:render_axiom_summary_heatmap`
