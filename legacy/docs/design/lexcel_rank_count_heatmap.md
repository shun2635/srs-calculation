# Lexcel 出現ベクトル（θ）ヒートマップ（特徴量 × ランク層）

## 目的

「出現ベクトル」θ を可視化する。
各特徴量（player）`j` に対して、入力の `rank` 列で定義されるランク層 `i` ごとに
その層に属する提携集合の中で特徴量 `j` が **何回出現するか**（θ の要素）をヒートマップとして出力する。

## 入力

- 入力ランキング CSV: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv`
  - 必須列:
    - `player1..playerN`（0/1）
    - `rank`（int; 1 が最上位）

## 集計仕様

ランク層と θ ベクトルは次で定義する。

- ランク層: 入力の `rank` 列で定義される層（1 が最上位）
  - `Σ_i := { S ⊆ N | rank(S)=i }`
- 出現ベクトル: 各特徴量（player）`j` について
  - `θ_i(j) := |{ S ∈ Σ_i | j ∈ S }|`（空集合 `S=∅` は除外）
- ヒートマップのセル:
  - `(i, j)` セルは `j` 番目の特徴量の出現ベクトル `θ(j)` の `i` 番目要素 `θ_i(j)`

## 出力

- 出力先: `outputs/real/<dataset_id>/figures/lexcel_rank_counts.png`

## 表示仕様

- 横軸: 特徴量（`features.yaml` の順＝`player1..playerN` の順）
- 縦軸: ランク層 `i`（上が 1）
- セル: 出現回数 `θ_i(j)`（整数; 小さい場合は図中に数値として注記）

## pipeline への組み込み

- `real-gen make-figures <dataset_id>` 実行時に best-effort で生成する
  - `rank` 列が無い場合はスキップ
