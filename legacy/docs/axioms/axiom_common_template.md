# 公理チェック（共通テンプレ）

## 目的

ランキング CSV を入力として、公理（axiom）を満たす/破るを判定し、集計する。

## 入力

- 入力 CSV: `<out>/rankings/nN/game_*.csv`
- 必須列:
  - `rank`（土台の弱順序。1 が最上位）
  - 公理が参照する `rank_*` 列（例: `rank_g-lexcel`）

## 連合の表現

- CSV 行の `player1..playerN` を 0/1 として連合を表す
- 実装では `mask: int`（bit0=player1）に正規化するのが基本

## 欠損値（空欄）の扱い

- 公理で必要な連合サイズに対して `rank_*` が欠損するゲームは **skip** する
  - 例: 2人提携の公理なら、全ての |S|=2 の行が埋まっていない場合 skip

## 出力（案）

- 1ゲーム×1公理×1ルールごとの結果:
  - `satisfied / violated / skipped`
- 集計 CSV（案）:
  - `players, axiom, coalition_size, rule, satisfied_games, checked_games, total_games, violated_games, skipped_games`

## 実装配置（案）

- CLI: `gamegen/commands/axioms.py`（例）
- 判定ロジック: `gamegen/axioms/<axiom_name>.py`（例）

