# wine（UCI Wine）

UCI Wine データセット（3 クラス分類）。
化学分析値（13 特徴量）からワインの `class`（`C1` / `C2` / `C3`）を予測する。

本リポジトリでは、特徴量部分集合（連合）ごとにモデルを学習・評価して得た
`accuracy` を「連合のスコア `v(S)`」として扱い、協力ゲームの貢献度指標（Shapley/Banzhaf 等）を計算する。

## 入力（特徴量マスク精度テーブル）

- パス: `inputs/feature_mask_tables/wine/game_table.csv`
- スコア列: `value`（`metric=accuracy`）
- 特徴量列（0/1）:
  - `Alcohol`: アルコール
  - `Malicacid`: リンゴ酸
  - `Ash`: 灰分
  - `Alcalinity_of_ash`: 灰分アルカリ度
  - `Magnesium`: マグネシウム
  - `Total_phenols`: 総フェノール
  - `Flavanoids`: フラボノイド
  - `Nonflavanoid_phenols`: 非フラボノイドフェノール
  - `Proanthocyanins`: プロアントシアニン
  - `Color_intensity`: 色の強度
  - `Hue`: 色相
  - `0D280_0D315_of_diluted_wines`: 希釈ワインの OD280/OD315
  - `Proline`: プロリン

## 取り込み・計算

設計は `docs/design/wine.md` を参照（`real-gen import-game/apply-rules` を使用）。

論文用の指標計算仕様メモは `docs/datasets/wine_metrics_for_paper.md` を参照。
