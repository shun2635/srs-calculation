# 実データ処理を別パッケージへ切り出す設計（`realgen`）

## 目的

実データ（例: Ontario「Bridge conditions」特徴量マスク精度テーブル）に対する

- 前処理（raw CSV → game CSV 正規化）
- スコア/ルール適用（`rank_*` / `score_*`）
- 可視化（PNG 等）

を、既存の `gamegen` パッケージ（仮想ゲーム生成・評価用）と **干渉しない** 形で提供する。

ここでの「干渉しない」とは：

- `gamegen` の CLI/コマンド構成や既存の出力規約を変更しない
- `gamegen` 側に実データ専用の入出力やラベル処理を埋め込まない
- ただし、ランキングの定義（`gamegen/rules/*`, `gamegen/ranking/registry.py`）は **共通資産**として再利用する

## 方針

- 新しい Python パッケージ `realgen` をリポジトリ内に追加する
- `realgen` は `gamegen` を **ライブラリとして利用**し、ルール計算・CSV書き込みのロジックは可能な限り共通化する
- `gamegen` の CLI（`game-gen`）には実データ用コマンドを追加しない

## ディレクトリ設計

## リポジトリ実装レイアウト（src layout）

Python パッケージは `src/` 配下に配置する（いわゆる src layout）。

```
src/
  gamegen/
  realgen/
tests/
```

この構成により「未インストール状態でトップレベルを import してしまう」事故を避けつつ、
CLI は `pyproject.toml` の console script から起動する。

### 入力（実データ）

```
inputs/
  feature_mask_tables/
    ontario_bridge_conditions/
      ontario_bridge_conditions_feature_mask.csv
      schema.yaml
      README.md
```

`schema.yaml` は `realgen` が解釈する（`gamegen` は関与しない）。

### 出力（実データ）

`outputs/real/` 以下に閉じる（生成ゲームの `outputs/games/**` と混在させない）。

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
        game_<dataset_id>.png
```

## データモデル（共通化）

### game CSV（共通フォーマット）

`gamegen/io/game_csv.py:read_game_csv()` が読める形式を採用する：

- 先頭 `player1..playerN`（0/1）
- `score`（float）
- `rank`（int, 1 is best）
- `2^N` 行が揃っている

### features mapping（実データ専用）

`realgen` 独自に `*.features.yaml` を出力する。

```yaml
features:
  - player: player1
    column: category
    label: "（短い表示名; 任意）"
    description: "..."
  ...
```

この対応表は可視化で `player` 表記（{1,3}）の代わりに列名（{category,type_1}）を出すために使う。
`label` があれば表示では `label` を優先し、無ければ `column`（または `description`）を使う。

## CLI 設計（`real-gen`）

`realgen/cli.py` に Click ベースで CLI を提供し、`pyproject.toml` で console script を登録する。

### 共通：dataset_id と入出力の解決

各データセットは `dataset_id`（例: `ontario_bridge_conditions`）で識別し、CLI には基本的に **dataset_id のみ**を渡す。

- 入力（既定）: `inputs/feature_mask_tables/<dataset_id>/`
- 出力（既定）: `outputs/real/<dataset_id>/`

これにより、特徴量数 `N` を引数として渡す必要がなくなり（`schema.yaml` から推定）、
複数データセットの出力も衝突しない。

### `real-gen import-game <dataset_id>`

- 入力: `inputs/feature_mask_tables/<dataset_id>/schema.yaml`（必須、raw CSV は schema の `raw_csv` で指定）
- 出力: `outputs/real/<dataset_id>/games/game_<dataset_id>.csv` と `*.features.yaml`
- 仕様:
  - 特徴量列（player）は次の優先順で決める
    - `schema.yaml:feature_columns` があればその順序を使用
    - 無ければ raw CSV から 0/1 列を自動検出（`feature_exclude` を除外、列順は CSV の順）
  - `score` は `score_column`（既定 `value`）
    - `schema.yaml:score_transform`（任意）で変換できる
      - `identity`（既定）: そのまま
      - `negate`: `score=-x`（「小さいほど良い」指標を「大きいほど良い」へ反転）
  - `rank` は `score` の **最大〜最小レンジを等間隔に分割**して決める（階級的 rank）
    - `schema.yaml:rank_method`（任意）で変更できる
      - `binned`（既定）: 等間隔ビン（下記）
      - `dense`: `score` 降順の dense rank（同点は同順位）
    - 分割数 `B`（既定 5）で幅 `w=(max-min)/B` を作り、上位区間から `rank=1..B` を割り当てる
    - 例: `B=5` のとき、スコアが `[max-w, max]` に入れば `rank=1`
    - 同一ランク内のタイブレークは不要（rank のみを保持）
    - `max==min` のときは全行 `rank=1`
    - レンジ算出（max/min）は **空集合（mask=0）を除外**して行う
    - 分割数は `config.yaml` の `realgen.import_rank_bins` で設定できる
  - 空集合行が無い場合は `empty_score`（schema or option）で補完
  - 代替: raw CSV 側で順位（ordinal rank）を **事前付与**している場合は、
    `schema.yaml:rank_column`（例: `class_id`）を指定し、その列を `rank` として **そのまま採用**する
    - この場合 `import_rank_bins` による分割は行わない
    - 空集合行を `empty_score` で補完する場合は、あわせて `empty_rank` の指定が必要
  - 取り込み時に `outputs/real/<dataset_id>/schema.yaml` へ schema をコピーする（トレーサビリティ/既定設定用）

### `real-gen apply-rules <dataset_id>`

- 入力: `outputs/real/<dataset_id>/games/game_<dataset_id>.csv`
- 出力: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv`
- 実装方針:
  - `gamegen/ranking/registry.py` を利用し `rank_<rule>` の mask→値を計算
  - `gamegen/io/rankings_csv.py` を利用し `score_*` / `rank_*` 列を書き込む
  - `*.features.yaml` を `games` → `rankings` にコピー
  - 注意: 一部ルール（interaction 系や group Shapley など）は計算量が大きく、特徴量数が大きい場合は自動的にスキップする
  - `--rules` を省略した場合は、`outputs/real/<dataset_id>/schema.yaml:rules` を優先して使用する（無ければ `config.yaml:pipeline.rules`）

### `real-gen make-figures <dataset_id>`

- 入力: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv` と隣接する `*.features.yaml`
  - 出力:
    - `outputs/real/<dataset_id>/figures/game_<dataset_id>.png`
  - 追加（best-effort; columns が存在する場合）:
    - `outputs/real/<dataset_id>/figures/interaction_index.png`
    - `outputs/real/<dataset_id>/figures/red_index_topXX_k10.png`（`XX=01..N`）
    - `outputs/real/<dataset_id>/figures/red_index_scatter.png`
    - `outputs/real/<dataset_id>/figures/shapley_values.png`
    - `outputs/real/<dataset_id>/figures/ordinal_banzhaf_values.png`
    - `outputs/real/<dataset_id>/figures/lexcel_rank_counts.png`
    - `outputs/real/<dataset_id>/figures/give_top10.png`
- 実装方針:
  - `gamegen/figures_png.py` は依存が重い（`japanize_matplotlib`）ため `realgen` 側に軽量版を持つ
  - `{1,3}` のような表示を `{category,type_1}` のように置換できるようにする
  - 解釈性のため、可視化では表示対象の提携サイズを既定で最大 3 に制限する（ランキング計算自体は全提携のまま）
  - 表の見切れ対策として、列数・行数・ラベル長に応じて PNG の横幅/縦幅を自動調整する（改行はしない）

#### `interaction_index.png`（全提携・上位 30 表）

全提携（空集合を除く）を対象に、次の提携ルールについて **上位 30 提携**の表を 1 枚の PNG にまとめて出力する。

- `rank_shapley-interaction`（`score_shapley-interaction` があれば併記）
- `rank_banzhaf-interaction`（`score_banzhaf-interaction` があれば併記）
- `rank_rp-index`（`score_rp-index` があれば併記）

順位（`rank_*`）の昇順（1 が最上位）で並べ、同順位は mask（player ビット列）で安定化する。

#### `red_index_topXX_k10.png`（提携サイズ別・上位 10 表）

全提携（空集合を除く）を対象に、`score_red-index` を提携サイズ `|S|` ごとに分けて
各サイズで **上位 10 提携**（降順）を表として出力する。

- 前提: `score_red-index` 列が rankings CSV に存在する（= red-index を apply-rules 済み）
- 列: `予測因子の組`, `Red Index`, `正解率`（= rankings の `score` を表示）
- ファイル名: `red_index_top01_k10.png`, `red_index_top02_k10.png`, ... `red_index_topNN_k10.png`

#### `red_index_scatter.png`（提携サイズ × Redundancy Index）

全提携（空集合を除く）を対象に、横軸=提携サイズ `|S|`、縦軸=`score_red-index` の散布図を出力する。

- 前提: `score_red-index` 列が rankings CSV に存在する（= red-index を apply-rules 済み）

#### `shapley_values.png`（特徴量 × Shapley 値）

singleton 提携（`|S|=1`）行の `score_shapley` を用いて、特徴量（player）ごとの Shapley 値を棒グラフで出力する。

- 前提: `score_shapley` 列が rankings CSV に存在する（= shapley を apply-rules 済み）

#### `ordinal_banzhaf_values.png`（特徴量 × 序数的Banzhafスコア）

提携の ordinal level（`rank`）を用いて、特徴量（player）ごとの序数的Banzhafスコアを棒グラフで出力する。

- 前提: `rank` 列が rankings CSV に存在し、全提携の rank が揃っている（`0..(2^N-1)`）
  - `rank` の tie は `mask`（playerビット列）でタイブレークして level を一意化する

#### `lexcel_rank_counts.png`（特徴量 × Lexcel ランク出現回数）

Lexcel の定義に基づく θ 出現ベクトルを、縦軸=ランク層（上が 1）、横軸=特徴量のヒートマップとして出力する。

- 前提: `rank` 列が rankings CSV に存在する（1 が最上位）

#### `give_top10.png`（Give/引き上げ 上位提携）

Give 公理で使う `give(T)=|{i∈T | rank(T)<rank({i})}|` を提携ごとに計算し、
上位 10 提携を表として出力する（`|T|>=2` のみ対象）。

### `real-gen feature-rule-heatmap <dataset_id>`

- 目的: **縦軸=特徴量セット、横軸=ルール** とし、セルに「提携の順位」を入れたヒートマップを出力する
- 入力:
  - `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv`
  - `outputs/real/<dataset_id>/rankings/game_<dataset_id>.features.yaml`（特徴量表示名）
- 出力: `outputs/real/<dataset_id>/heatmaps/feature_rule_rank.png`
- 表示対象:
  - 解釈性のため、提携サイズは既定で **最大 2**（サイズ 1 と 2 を全て表示）
- 色（セル背景）:
  - ルール（列）ごとに、その列で観測される rank の **min..max に合わせて正規化**して色付けする
  - これにより、同じ「5位」でも 1..10 のルールと 1..1000 のルールで色が変わる
- 表示名（特徴量）:
  - `*.features.yaml` の `label` を優先
  - 無ければ `description` を簡約（先頭の短い要約）して使用
  - それでも無ければ `column`（原カラム名）

## 移行（既存実装の扱い）

既に `gamegen` 側に入っている実データ用の実装（import コマンド、features.yaml など）は削除/ロールバックし、
同等機能を `realgen` に移す。
