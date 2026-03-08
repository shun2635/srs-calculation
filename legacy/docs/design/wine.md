# wine データセット取り込み・貢献度計算（real-gen）

## 目的

`inputs/feature_mask_tables/wine/game_table.csv`（特徴量マスク精度テーブル）を、
既存実装の `realgen` / `gamegen` を用いて

- game CSV への正規化（`player1..playerN, score, rank`）
- 貢献度指標（`score_*` / `rank_*`）の計算
- 図・ヒートマップ出力

まで一貫して生成できるようにする。

## 前提：入力データの形式

- 入力: `inputs/feature_mask_tables/wine/game_table.csv`
- 特徴量列（0/1 フラグ）: `class` 以外の 13 列
- スコア列: `value`（`accuracy`）
- 順位列: `class_id`（1 が最上位）
- メタ列: `order, abs_value, metric, n_train, n_test, seed` など

この CSV は空集合（全ゼロ行）を含む **全提携**（`2^13 = 8192` 行）を含む。

## 設計方針（既存モジュールの再利用）

- 取り込み（raw → game CSV）: `real-gen import-game wine`
  - `src/realgen/commands/import_game.py` を使用する（新規実装しない）
  - `schema.yaml` により
    - `raw_csv`（入力 CSV 名）
    - `score_column`（既定 `value`）
    - `rank_column`（事前付与 rank の列; wine は `class_id`）
    - `feature_columns`（プレイヤー順序）
    - `filters`（実験条件固定）
    - `empty_score`（空集合の補完値）
    を指定する
  - wine は `rank_column` を指定し、raw 側の `class_id` を `rank` として **そのまま採用**する（このリポジトリでの分割は行わない）

- 貢献度計算（ルール適用）: `real-gen apply-rules wine`
  - `src/realgen/commands/apply_rules.py` が `gamegen` のルール実装を呼び出し、
    `score_shapley` / `rank_shapley` 等の列を `rankings` CSV に追記する
  - ルールの既定セットは `config.yaml:pipeline.rules`

- 可視化:
  - `real-gen make-figures wine`（`outputs/real/wine/figures/`）
  - `real-gen feature-rule-heatmap wine`（`outputs/real/wine/heatmaps/feature_rule_rank.png`）

## 空集合（全ゼロ連合）の扱い

wine は raw CSV に `class_id`（rank）を含む。
空集合行が欠ける場合のみ `schema.yaml:empty_score` で補完する。

- 本タスクでは無情報（特徴量無し）スコアとして `empty_score: 0.4` を用いる。
- もし「特徴量無しモデル」の実測精度（例: 多数派クラス精度）がある場合は、将来的に `empty_score` をその値へ更新する。

## 生成物（出力）

コマンド実行により、次を生成する。

- `outputs/real/wine/games/game_wine.csv`
- `outputs/real/wine/games/game_wine.features.yaml`
- `outputs/real/wine/rankings/game_wine.csv`
- `outputs/real/wine/rankings/game_wine.features.yaml`
- `outputs/real/wine/figures/game_wine.png`
- `outputs/real/wine/figures/interaction_index.png`
- `outputs/real/wine/figures/red_index_top01_k10.png`（〜 `red_index_top13_k10.png`）
- `outputs/real/wine/figures/red_index_scatter.png`
- `outputs/real/wine/figures/shapley_values.png`
- `outputs/real/wine/figures/lexcel_rank_counts.png`
- `outputs/real/wine/heatmaps/feature_rule_rank.png`
