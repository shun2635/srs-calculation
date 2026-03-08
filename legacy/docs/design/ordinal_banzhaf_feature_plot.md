# 特徴量 × 序数的Banzhafスコアプロット（real-gen）

## 目的

特徴量（プレイヤー）ごとの「序数的Banzhafスコア」を可視化し、
どの特徴量が序数（順位）構造に対して強く効いているかを直感的に確認できるようにする。

## 入力

- 入力ランキング CSV: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv`
  - 必須列:
    - `player1..playerN`（0/1）
    - `rank`（提携の ordinal rank / level; 1 が最上位）
  - 注意:
    - 計算に `rank` を使うため、スコア（`score`）は不要
    - `rank` に tie がある場合は、同 rank 内を `mask`（playerビット列）でタイブレークして level を一意化する
    - `rank` は 0..(2^N-1) の全提携に対して存在する必要がある（欠落がある場合はスキップする）
- 特徴量名: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.features.yaml`
  - `label` があれば表示名は `label` を優先する

## 出力

- 出力先: `outputs/real/<dataset_id>/figures/ordinal_banzhaf_values.png`

## 仕様

- 横軸: 特徴量名（`features.yaml` の順＝`player1..playerN` の順）
- 縦軸: 序数的Banzhafスコア `s_i = u_i^+ - u_i^-`
  - `u_i^+`: `i` を追加したときに level が改善（小さくなる）する回数
  - `u_i^-`: `i` を追加したときに level が悪化（大きくなる）する回数
- 描画: 棒グラフ（bar plot）
  - 特徴量名が長い場合は回転して表示し、図の横幅も特徴量数に応じて自動調整する

## pipeline への組み込み

- `real-gen make-figures <dataset_id>` 実行時に best-effort で生成する
  - `rank` 列が無い場合、または全提携の `rank` が揃っていない場合はスキップする
