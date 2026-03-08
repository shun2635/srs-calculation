# Legacy CLI Reference

For project overview and collaboration-oriented documentation, start with:

- [`../README.md`](../README.md)
- [`../docs/ja/README.md`](../docs/ja/README.md)
- [`../docs/en/README.md`](../docs/en/README.md)

This file remains the CLI-focused reference for the current `legacy/` implementation.

# game-gen

ゲーム（全連合 `2^N`）を CSV 生成し、ルール適用と公理チェックを行う CLI です。

初回は依存関係と CLI をセットアップします。

```bash
poetry install
```

## ゲーム生成

```bash
poetry run game-gen gen-games -p N -c K --out outputs
```

- 出力: `outputs/games/nN/game_*.csv`
- 仕様: 全連合に整数 `score` を付与し、`rank`（1=最上位）も含めて保存

## ルール適用

```bash
poetry run game-gen apply-rules -p N --out outputs
```

- 入力: `outputs/games/nN/game_*.csv`
- 出力: `outputs/rankings/nN/game_*.csv`（`rank_*` / `score_*` 列を追記）

## 公理チェック

```bash
poetry run game-gen check-axioms -p N --out outputs
```

- 入力: `outputs/rankings/nN/game_*.csv`
- 出力:
  - `outputs/axiom/nN/<axiom>/<rule>.csv`（1行=1ゲーム; `constraints` / `satisfied` / `satisfied_rate`）
  - `outputs/axiom/nN/summary.csv`（`rule, axiom, constraints, satisfied, satisfied_rate`）

## パイプライン

```bash
poetry run game-gen pipeline -p N -c K --out outputs
```

 - 仕様: ゲーム生成 → ランキング生成 → 公理チェック（`summary.csv` まで）を一括実行

## ヒートマップ出力

```bash
# ルール列どうしの順位相関ヒートマップ（個人ルール/提携ルール別）
poetry run game-gen rule-corr-heatmap -p N --out outputs

# 指定ペアの順位ヒートマップ（config.yaml の rank_heatmap.pairs を使用）
poetry run game-gen rank-heatmap -p N --out outputs
```

- 出力: `outputs/heatmaps/nN/`

# real-gen

実データ（feature-mask performance table）の前処理/ルール適用/可視化を行う CLI です。
`real-gen` は `gamegen` のランキングルール（`rank_*` / `score_*`）をライブラリとして再利用します。

## データセット一覧（dataset_id）

- `ontario_bridge_conditions`: Ontario「Bridge conditions」データセットの特徴量マスク精度テーブル（`value` をスコアとして協力ゲーム化）
- `credit_g`: German Credit（信用リスク）データセットの特徴量サブセット評価テーブル（不完全な提携集合）

## 使い方

`inputs/feature_mask_tables/<dataset_id>/` に `schema.yaml` と raw CSV を置いた上で実行します。

```bash
# 1) raw CSV + schema.yaml を game CSV に正規化
poetry run real-gen import-game <dataset_id>

# 2) 既存ルール（rank_* / score_*）を適用して rankings を生成（グループ系含む）
poetry run real-gen apply-rules <dataset_id>

# 3) 可視化（既定: 提携サイズ <= 3 のみ表示）
poetry run real-gen make-figures <dataset_id>

# 4) ヒートマップ（縦=特徴量セット、横=ルール、セル=rank）
poetry run real-gen feature-rule-heatmap <dataset_id>
```

- 出力: `outputs/real/<dataset_id>/` 配下（例: `outputs/real/<dataset_id>/rankings/`）
