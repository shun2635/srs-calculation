# 実データ CSV（特徴量マスク精度テーブル）の取り込み設計

## 目的

仮想的に生成した `outputs/games/nN/game_*.csv`（全連合 `2^N` のゲーム表）だけでなく、
実データ由来の「特徴量をマスクした時の予測精度テーブル（feature-mask performance table）」に対しても、
本リポジトリのランキングルール（`rank_*` / `score_*`）を適用できるようにする。

## 前提（実データ CSV の特徴）

例:

```
category,subcategory_1,type_1,material_1,region,owner,age,years_since_major_rehab,deck_length_m,span_count,order,value,abs_value,metric,n_train,n_test,seed
1,0,0,0,0,0,0,0,0,0,1,0.6277,0.6277,accuracy,3744,1249,42
...
```

- `0/1` のフラグ列が「プレイヤー（意味的には特徴量）の存在」を表す。
- `value` 列がスコア（意味的には予測精度）に相当する。
- メタ情報列（例: `metric,n_train,n_test,seed`）が併存しうる。

## 方針：内部の game CSV 形式へ正規化してから既存の仕組みに流す

既存のルール適用・可視化・公理チェックは `gamegen/io/game_csv.py:read_game_csv()` を入口にしており、
入力は次の形式を要求する：

- 先頭が `player1..playerN` の列
- `score` 列（数値）
- `rank` 列（整数; 1 が最上位）
- `2^N` 個の全連合が揃っていること

そこで、実データ CSV はまず内部形式の game CSV に変換（正規化）し、
以降は **既存の `rank-game` / `apply-rules` / `pipeline` と同じ**フローに乗せる。

## ディレクトリ設計（入力）

実データ（元 CSV）は `inputs/feature_mask_tables/` 配下に置く。

```
inputs/
  feature_mask_tables/
    <dataset_id>/
      raw.csv
      schema.yaml
      README.md            (任意)
```

- `dataset_id`: 任意の識別子（例: `bridge_accuracy_seed42`）。
- `raw.csv`: 実データ CSV（元形式のまま）
- `schema.yaml`: 正規化設定（後述）

### `schema.yaml`（正規化設定）の案

最小限の指定で、変換が一意に決まるようにする。

```yaml
score_column: value
feature_columns:
  - category
  - subcategory_1
  - type_1
  - material_1
  - region
  - owner
  - age
  - years_since_major_rehab
  - deck_length_m
  - span_count
feature_descriptions:
  category: 構造物の大分類（例: Bridge / Culvert / Tunnel / Retaining Wall）
  subcategory_1: 主構造要素の分類（橋梁なら上部構造の主桁形式など）
  type_1: 主構造要素の詳細タイプ（subcategory_1 をより細かくした分類）
  material_1: 主構造（主要耐荷部材）の材料
  region: 管理主体（MTO）の地域区分
  owner: 所有者区分（例: Provincial / Municipal など）
  age: 築年数（inspection_year - year_built）
  years_since_major_rehab: 最終大規模補修からの経過年数（inspection_year - last_major_rehab）
  deck_length_m: デッキ（またはカルバート）長さ [m]
  span_count: スパン/セル数（NUMBER OF SPAN / CELLS から数値を抽出して数値化）
filters:
  metric: accuracy
  seed: 42
```

- `feature_columns`: 0/1 フラグ列の **順序**（この順序が `player1..playerN` の対応になる）
- `score_column`: `score` に対応させる列名
- `filters`（任意）: 特定の `metric`/`seed` のみ抽出したい場合のフィルタ条件
- `feature_descriptions`（任意）: 特徴量（列名）→説明の対応表（後の可視化ラベルに利用）

## ディレクトリ設計（出力）

正規化後の game CSV は、生成ゲームと混ぜずに `outputs/real/` 配下へ出す（衝突回避）。

```
outputs/
  real/
    <dataset_id>/
      games/
        game_<dataset_id>.csv
        game_<dataset_id>.features.yaml
      rankings/
        game_<dataset_id>.csv
        game_<dataset_id>.features.yaml
    figures/
      nN/
        <dataset_id>.png
    heatmaps/
      nN/
        ...
    axiom/
      nN/
        ...
```

## 正規化（raw.csv → game CSV）仕様

- `player1..playerN`: `schema.yaml:feature_columns` の順に 0/1 をそのまま採用
- `score`: `schema.yaml:score_column` の値（`float`）
- `rank`:
  - `score` の **降順**で dense rank（同値は同順位、次の順位は +1）
  - タイブレーク: `mask` 昇順（安定化）
- 完備性:
  - `2^N` の全連合が揃っていない場合はエラー（将来 `--allow-incomplete` 等を検討）

## 特徴量ラベル（対応表）の保存仕様

- `player1..playerN` と元の特徴量列の対応を `*.features.yaml` に保存する。
- `rankings` 側にも同名の `*.features.yaml` をコピーして、可視化が `rankings CSV` だけで完結できるようにする。

## 次の実装ステップ（別タスク）

- `real-gen import-game <dataset_id>` のような取り込みコマンド追加
- `schema.yaml` の読み込みとフィルタ適用、mask→rank の生成
- 取り込み後に `apply-rules` / `pipeline` を `outputs/real` に対して実行できるように配線
