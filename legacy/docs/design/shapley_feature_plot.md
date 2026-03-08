# 特徴量 × Shapley 値プロット（real-gen）

## 目的

特徴量（プレイヤー）ごとの Shapley 値（`score_shapley`）を可視化し、
どの特徴量が寄与しているかを直感的に確認できるようにする。

## 入力

- 入力ランキング CSV: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv`
  - 必須列:
    - `player1..playerN`（0/1）
    - `score_shapley`（Shapley 値; singleton 行にのみ値が入る）
- 特徴量名: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.features.yaml`
  - `label` があれば表示名は `label` を優先する

## 出力

- 出力先: `outputs/real/<dataset_id>/figures/shapley_values.png`

## 仕様

- 対象行: singleton 提携（`|S|=1`）のみ
- 横軸: 特徴量名（`features.yaml` の順＝`player1..playerN` の順）
- 縦軸: Shapley 値（`score_shapley`）
- 描画: 棒グラフ（bar plot）
  - 特徴量名が長い場合は回転して表示し、図の横幅も特徴量数に応じて自動調整する

## pipeline への組み込み

- `real-gen make-figures <dataset_id>` 実行時に best-effort で生成する
  - `score_shapley` 列が無い場合、または singleton 行に値が無い場合はスキップする

