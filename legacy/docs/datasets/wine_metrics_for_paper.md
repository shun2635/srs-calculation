# wine データセット：指標計算の仕様（論文用メモ）

本メモは、本リポジトリにおける wine（UCI Wine）データセットの指標計算（Shapley / Lex-cel）について、
論文記述に必要な「採用した定義」「計算法」「対象集合」を実装ベースで確定させるための整理です。

- データセット概要: `docs/datasets/wine.md`
- 取り込み設計（raw→game / apply-rules / 図生成）: `docs/design/wine.md`

## 前提：ゲームの定義（wine）

- プレイヤー集合: 特徴量 13 個（`N=13`）
  - 順序（bit の割当）: `inputs/feature_mask_tables/wine/schema.yaml:feature_columns`
  - 全提携: `2^N = 8192`（空集合を含む）
- 値関数: `v(S) := accuracy(S)`
  - raw 入力 `inputs/feature_mask_tables/wine/game_table.csv` の `value` 列（`metric=accuracy`）を
    `real-gen import-game wine` が canonical game CSV の `score` 列へ写像する。
  - 取り込み条件（固定する実験条件）: `inputs/feature_mask_tables/wine/schema.yaml:filters`
- 空集合 `S=∅`:
  - 入力 CSV に空集合行が無い場合のみ、`inputs/feature_mask_tables/wine/schema.yaml:empty_score` で補完する。
  - `allow_incomplete: false` のため、最終的に **全 2^N の `score` が揃っていることを要求**する（欠落があるとエラー）。

---

# D. Shapley Value の算出（基数）

## 16. Shapley の対象ゲーム

- 対象ゲーム: wine の特徴量ゲーム（プレイヤー=特徴量、提携=特徴量部分集合）
- 値関数: **`v(S)=score(S)` をそのまま使用**（`rank` 列は不使用）
  - 実装根拠: `src/gamegen/rules/shapley.py:read_value_function_csv` が `score` 列を読み、`mask -> v(S)` を構築する。

## 17. Shapley の計算法

- **全列挙による厳密計算（2^N）**
  - 実装は Shapley 値の定義式に基づき、各プレイヤー `i` について全 `S ⊆ N \\setminus {i}` を走査する。
  - 実装根拠: `src/gamegen/rules/shapley.py:player_shapley_values` が `s_mask in range(2^n)` を全走査。
- 近似（permutation サンプリング）は **未使用（実装されていない）**。

## 18. 近似の場合の条件（M, seed, 誤差）

- 本リポジトリの wine 計算では **近似を使わない**ため、`M/seed/推定誤差` は **N/A**。

---

# E. Lex-cel の算出（序数）

## 19. Lex-cel の定義の採用形（appearance vector）

- Lex-cel（`rank_lexcel`）は **appearance vector（出現ベクトル）**に基づく定義を採用している。
  - `score` 同値クラス（降順）で提携集合を層に分割: `Σ_k := { S | level(S)=k }`
  - 各プレイヤー `i` の出現ベクトル:
    - `θ_k(i) := |{ S ∈ Σ_k : i ∈ S }|`（空集合 `S=∅` は除外）
  - `θ(i)` を辞書式（降順）比較して順位付け（dense rank）
  - 実装根拠: `src/gamegen/rules/lexcel.py`
- 注意（同値判定）: `score` の同値クラス分割は **浮動小数の `==`**で行う（許容誤差による近似クラスタリングは行わない）。

## 20. 図の「ランク出現回数」の定義

本リポジトリの `lexcel_rank_counts.png` は、Lex-cel の `rank_lexcel` を可視化する図ではなく、
**`rank` 列で定義された「ランク層」ごとの出現回数**（appearance vector と同形式）を可視化する。

- ランク層: `Σ_k := { S ⊆ N : rank(S)=k }`（`rank` は入力/取り込み済みの提携ランク列）
- 表示する値: `i_k = |{ S ∈ Σ_k : i ∈ S }|` を **そのまま**（空集合 `S=∅` は除外）
- 上位クラスのみ集計、といったフィルタは **行わない**（`k=1..max(rank)` を全表示）
- 実装根拠:
  - 仕様: `docs/design/lexcel_rank_count_heatmap.md`
  - 実装: `src/realgen/figures_png.py:generate_lexcel_rank_count_heatmap`

補足: wine では `rank` は raw 側の `class_id` を **そのまま採用**する（`inputs/feature_mask_tables/wine/schema.yaml:rank_column`）。

## 21. 対象集合 X（全列挙か、観測集合か）

- Shapley / Lex-cel（`rank_lexcel`）の計算対象: **全 2^N 提携（空集合を含む）**
  - 根拠: `real-gen import-game` が `allow_incomplete: false` のもとで全提携の欠落を許さない。
- 図（`lexcel_rank_counts.png`）の対象: 入力される rankings CSV の提携集合
  - wine の標準パイプラインでは rankings CSV 自体が全提携を保持するため、結果として **全 2^N** が対象になる。
