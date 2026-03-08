# Redundancy Index 散布図（提携サイズ × Redundancy Index）

## 目的

Redundancy Index（`score_red-index`）の値分布が提携サイズ `|S|` に対してどのように変化しているかを視覚的に確認できるように、
散布図 PNG を出力する（実装修正のデバッグ・比較用途）。

## 入力

- 入力ランキング CSV: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv`
  - 必須列:
    - `player1..playerN`（0/1）
    - `score_red-index`（Redundancy Index のスコア; 整数相当）

## 出力

- 出力先: `outputs/real/<dataset_id>/figures/red_index_scatter.png`

## プロット仕様

- 対象提携: 非空提携（`mask != 0`）
- 横軸: 提携サイズ `|S|`（`player*` の 1 の個数）
- 縦軸: `score_red-index`
- 描画:
  - `matplotlib` の散布図
  - 透明度（alpha）を下げ、重なりの密度が分かるようにする
  - タイトルに dataset_id と件数を含める

## pipeline への組み込み

- `real-gen make-figures <dataset_id>` 実行時に best-effort で生成する
  - `score_red-index` 列が無い場合はスキップ

