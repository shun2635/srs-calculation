# COVID-19（政策バンドル × Rt）取り込み・前処理設計（real-gen）

## 目的

`inputs/feature_mask_tables/covid19/covid19_policy__ranked.csv`（政策バンドル × 次月 Rt 平均）を、
`real-gen` が扱える **game CSV**（`player1..N,score,rank`）へ正規化し、
以降の `real-gen apply-rules` / 可視化に流せるようにする。

本データは 6 施策の 0/1 組合せからなる **全提携集合（2^6=64 行）** を含む。

## 入力データ（`covid19_policy__ranked.csv`）

### 施策（player）列（0/1）

| 政策名 | OxCGRTキー | 説明 |
|--------|-----------|------|
| 学校閉鎖 | `C1M_on` | School closing |
| 職場閉鎖 | `C2M_on` | Workplace closing |
| 集会制限 | `C4M_on` | Restrictions on gatherings |
| 外出制限（自宅待機要求） | `C6M_on` | Stay at home requirements |
| 所得支援 | `E1_on` | Income support |
| ワクチン費用支援 | `V3_on` | Vaccine Financial Support (summary) |

### スコア列（目的変数）

- `metric` が `rt_mean_next_mean` の行を使用する
- `value`（= `rt_mean_next_mean`）:
  - 月次（国×月）で計算した `rt_mean_next`（同一国で 1 ヶ月先に shift した Rt の平均）を、
    同じ政策組合せ（bundle）ごとに平均した値

## 正規化方針（raw CSV → game CSV）

### 1) 特徴量（player）列

- 上の 6 列を player（施策）として扱う
- `schema.yaml:feature_columns` の順序で `player1..player6` に対応づける

### 2) `score`（大きいほど良い値）

`rt_mean_next_mean` は「次月の Rt 平均」であり **小さいほど良い**。
本リポジトリの多くのルール（Shapley/Banzhaf 等）は **大きいほど良い** を前提に実装されているため、
取り込み時に次の変換を行う：

- `score = -rt_mean_next_mean`（= `-value`）

（定数加算は Shapley 等の限界寄与に影響しないため、符号反転のみで目的を満たす）

### 3) `rank`（1 が最上位）

- `score` の降順（同点は同順位）で **dense rank** を付与する
- タイブレークは mask 昇順（安定化）

### 4) 完全テーブル（full 2^N）

- 6 施策の全組合せ（64 行）を含むため、`allow_incomplete: false` のまま取り込む

## 入力ディレクトリ構成

```
inputs/feature_mask_tables/covid19/
  covid19_policy__ranked.csv
  schema.yaml
```

## `schema.yaml` 仕様（covid19 用）

- `raw_csv: covid19_policy__ranked.csv`
- `filters.metric: rt_mean_next_mean`
- `score_column: value`（= `rt_mean_next_mean`）
- `score_transform: negate`（`score=-x`）
- `rank_method: dense`
- `allow_incomplete: false`
- `feature_columns: [...]`（上記 6 施策列）
- `feature_labels` / `feature_descriptions` に施策名（日本語）と OxCGRT 列名を記載

## 実行手順

```bash
# 1) 正規化（raw -> game CSV）
poetry run real-gen import-game covid19

# 2) ルール適用（既定 rules）
poetry run real-gen apply-rules covid19
```
