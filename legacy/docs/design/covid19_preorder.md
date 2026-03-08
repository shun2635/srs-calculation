# COVID-19（観測バンドル・不完全テーブル）取り込み・前処理設計（real-gen）

## 目的

`inputs/feature_mask_tables/covid19_preorder/observed__ranked.csv` を、
`real-gen` が扱える **game CSV**（`player1..N,score,rank`）へ正規化し、
弱順序（preorder/total order; 観測された範囲のみ）の貢献度指標を計算できるようにする。

本データは「観測された政策組合せ（bundle）のみ」を含むため、一般の協力ゲームが要求する **全提携集合（2^N 行）** は存在せず、
**不完全（observed subset）** として取り込む。

## 入力データ（`observed__ranked.csv`）

### 列

- 施策（player）列（0/1）: `*_on`
- スコア列: `value`（`metric=rt_mean_next_mean` の行を使用; 値は政策組合せごとの次月 Rt 平均）
- ランク列: `class_id`（クラスタリング処理で付与済み; 1 が最上位）
- 観測数: `n_train`（集計に使った国×月の件数）

### 施策（player）として扱う列（13施策）

`schema.yaml:feature_columns` で順序を固定する：

- `C1M_on`（学校閉鎖）
- `C2M_on`（職場閉鎖）
- `C3M_on`（公共イベント中止）
- `C4M_on`（集会制限）
- `C5M_on`（公共交通機関の停止）
- `C6M_on`（外出制限（自宅待機要求））
- `C7M_on`（国内移動制限）
- `C8EV_on`（国際渡航制限）
- `E1_on`（所得支援）
- `H3_on`（接触追跡）
- `H6M_on`（マスク着用）
- `V3_on`（ワクチン費用支援）
- `V4_on`（ワクチン義務化）

## 正規化方針（raw CSV → game CSV）

### 1) `player1..playerN`

- `schema.yaml:feature_columns` の順序で `player1..player13` に対応づける
- `_n_obs` は player には含めない（0/1 でないため）

### 2) `score`（大きいほど良い値）

数値スコアは raw CSV の `value` をそのまま `score` として格納する。
（順位は `class_id` を使うため、弱順序ベースの指標計算では `score` は参照しない）

### 3) `rank`（1 が最上位）

- `class_id` を `rank` として **そのまま採用**する（クラスタリングで付与済み）

### 4) 不完全テーブル（observed subset）

- `allow_incomplete: true` として取り込み、観測された政策バンドルのみを game CSV に出力する

## ルール適用方針（弱順序・不完全テーブル）

弱順序（preorder）かつ不完全なテーブルに対しては、全提携の列挙を必要とする指標（Shapley 等）は適用しない。
本データセットでは、弱順序（順位）に基づき、かつ観測集合のみで定義できる貢献度指標のみを計算する。

- 計算対象（観測集合 variant）:
  - `o-banzhaf`, `g-o-banzhaf`
  - `rp-index`
  - `ud`, `du`
  - `red-index`

これらは `real-gen apply-rules` 側で「不完全テーブル」を検出した場合に観測集合向け実装を使用する。

## 入力ディレクトリ構成

```
inputs/feature_mask_tables/covid19_preorder/
  observed__ranked.csv
  schema.yaml
```

## `schema.yaml` 仕様（covid19_preorder 用）

- `raw_csv: observed__ranked.csv`
- `filters.metric: rt_mean_next_mean`
- `score_column: value`
- `score_transform: identity`
- `rank_column: class_id`
- `allow_incomplete: true`
- `feature_columns: [...]`（上記 13 施策列）
- `rules: [...]`（弱順序・不完全テーブル向け指標のみ）
- `feature_labels` / `feature_descriptions` に施策名（日本語）と OxCGRT 列名を記載

## 実行手順

```bash
# 1) 正規化（raw -> game CSV; 不完全テーブル）
poetry run real-gen import-game covid19_preorder

# 2) ルール適用（schema.yaml の rules が既定）
poetry run real-gen apply-rules covid19_preorder
```

## PNG 出力要件（covid19_preorder）

`real-gen make-figures covid19_preorder` の追加出力は次を満たす：

1. red-index の表（`red_index_topXX_k10.png`）は出力しない
   - 本データセットでは `red_index_*.png`（例: `red_index_scatter.png` を含む）を出力しない
2. ランク出現表は「出現分布（規格化した割合）」をヒートマップ化して出力する
3. サイズ 2 提携（観測された範囲）に限定した出現分布ヒートマップも出力する
   - 観測されていない（カウント 0）行/列は出力しない
   - 出力ファイルは `lexcel_rank_counts.png` / `lexcel_rank_counts_size2.png` とする（見た目互換のため）
   - `lexcel_rank_counts_size2.png` は「|S|=2 の提携（ペア）」を特徴量軸に並べる（例: `{学校閉鎖,職場閉鎖}`）
     - 各ペアについて「観測された提携（任意サイズ）の中で、そのペアを含む提携が各ランク層に何回出現したか」のベクトルを作る
     - ベクトルをペアごとに規格化（合計=1）してヒートマップ表示する
4. `interaction_index.png` に加えて、`interaction_index_size2.png`（提携サイズ |S|=2 のみ）も出力する
5. `interaction_index_size3.png`（提携サイズ |S|=3 のみ）も出力する
6. `feature_rule_rank.png` は `|S|<=3` までの提携を対象にする

### `lexcel_rank_counts.png` の表示仕様（covid19_preorder）

- 横軸: 政策名
- 縦軸: 効果ランク（上が 1）
- タイトル: 当該政策を含む政策パッケージの効果ランクの分布
- カラーバー: 出現割合

### `lexcel_rank_counts_size2.png` の表示仕様（covid19_preorder）

- `lexcel_rank_counts.png` と同じ「縦軸/タイトル/カラーバー」を用いる
- 横軸: 政策ペア
- 表示対象: 注目政策（`マスク着用, ワクチン費用支援, ワクチン義務化, 国際渡航制限, 所得支援`）のいずれかを含むペアのみ
- 表示対象（更新）: 上記 5 政策のみから生成される `5C2=10` ペアのみ（ペアの両要素が注目政策）
