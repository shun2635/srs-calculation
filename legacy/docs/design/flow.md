# 処理フロー設計（1〜5）

このドキュメントは、現行実装の主要な処理の流れを

1. ゲームスコア生成
2. ランキング変換
3. 貢献度指標割り当て（ルール）
4. 公理チェック（集計）
5. 可視化

の 5 段階として整理して説明します。

## 0. 前提（入出力とディレクトリ）

### 0.1 ファイルの基底ディレクトリ

- 出力基底は `--out` または `config.yaml:output_base`（既定 `outputs`）。
- パス規約は `gamegen/io/paths.py` の `OutputPaths` を基準にする。

### 0.2 CSV 形式（最低限）

**ゲーム CSV（入力/生成物）**

- パス例: `<out>/games/nN/game_000001.csv`
- カラム: `player1..playerN, score, rank`
- 行: 連合（`player*` の 0/1）を全列挙した **2^N 行**（`gamegen/io/game_csv.py:read_game_csv()` が検証）
- `rank` は `score` 降順の **dense rank**（1 が最上位）
- 同点時の安定化: `mask`（player1 を bit0）昇順（`gamegen/commands/games.py:generate_games_csvs()`）

**ランキング CSV（変換/追記後）**

- パス例: `<out>/rankings/nN/game_000001.csv`
- カラム: `player1..playerN, score, rank, score_<rule>..., rank_<rule>...`
- 列の更新・再整列: `gamegen/io/rankings_csv.py:write_rankings_with_rank_column()`

## 1. ゲームスコア生成（gen-games）

### 1.1 目的

全連合（2^N）に対して整数スコアを割り当て、ゲーム CSV を生成する。

### 1.2 処理

- 連合列挙: `gamegen/ordinal/enumerator.py:all_coalitions_sorted(n)`
  - `CoalitionEncoding` を使い、bitmask 昇順で安定化
- スコア生成: `random.Random(seed).randint(0, max_score)`
- 行順:
  - 第1キー: `score` 降順
  - 第2キー: 連合の bitmask 昇順
- `rank`（等級）付与:
  - `score` が変わったら `rank += 1`
  - 同点は同 `rank`（dense rank）

### 1.3 実装

- コマンド: `gamegen/commands/games.py:gen_games`
- 実処理: `gamegen/commands/games.py:generate_games_csvs`

## 2. ランキング変換（rank-game）

この段階は「ゲーム CSV →（正規化）→ ランキング CSV」の変換レイヤです。

### 2.1 入力の正規化

- 読み込み: `gamegen/io/game_csv.py:read_game_csv()`
  - `score` と `rank` を必須とし、2^N 行が揃っていることを検証
  - 内部表現は `mask -> score/level` の辞書に正規化
  - 行順（canonical order）を `(-score, mask)` で固定

### 2.2 ランキング CSV の書き込み/更新

- 新規作成:
  - `player*, score, rank, rank_<rule>` を出力
- 既存更新:
  - 既存 `rank_*` 列を読み込み、指定ルール列を追記（未存在の場合）
  - 既定順で `rank_*` 列を並べ替え（`gamegen/io/rankings_csv.py:CANONICAL_RANK_COLUMN_ORDER`）
  - 行順はゲーム側の canonical order に揃えて再構成

### 2.3 実装

- コマンド: `gamegen/commands/rankings.py:rank_game`
- 書き込み: `gamegen/io/rankings_csv.py:write_rankings_with_rank_column`

## 3. 貢献度指標割り当て（ルール）

この段階は「ルール（decision rule）を適用して `rank_<rule>` 列を埋める」処理です。

### 3.1 ルールの登録とインターフェース

- レジストリ: `gamegen/ranking/registry.py`
  - `RuleSpec(name, scope, ranker)` を登録
  - `scope` は
    - `PLAYER`: 個人（player index）に rank を返す
    - `COALITION`: 連合（mask）に rank を返す

### 3.2 `rank_<rule>` 列への書き込み規約

- `PLAYER` ルール:
  - **singleton（単独連合）行のみ**に値を入れる（それ以外は空欄）
- `COALITION` ルール:
  - **非空連合行**に値を入れる（空集合は空欄）

この規約は `gamegen/ranking/registry.py:compute_rank_column_values()` が実装する。

### 3.3 現行で提供するルール

ドキュメントは `docs/ranking/` にルール別に分割する（ロジック設計書）。

- `rank_shapley`（Shapley）: `docs/ranking/rank_shapley.md`
- `rank_banzhaf`（Banzhaf Value）: `docs/ranking/rank_banzhaf.md`
- `rank_lexcel`（Lex-cel）: `docs/ranking/rank_lexcel.md`
- `rank_o-banzhaf`（Ordinal Banzhaf）: `docs/ranking/rank_o-banzhaf.md`
- `rank_g-shapley`（Shapley group value）: `docs/ranking/rank_g-shapley.md`
- `rank_g-sum-shapley`（Sum of member Shapley values）: `docs/ranking/rank_g-sum-shapley.md`
- `rank_shapley-interaction`（Shapley Interaction Index）: `docs/ranking/rank_shapley-interaction.md`
- `rank_banzhaf-interaction`（Banzhaf Interaction Index）: `docs/ranking/rank_banzhaf-interaction.md`
- `rank_rp-index`（RP Index Rule）: `docs/ranking/rank_rp-index.md`
- `rank_ud`（UD Rule）: `docs/ranking/rank_ud.md`
- `rank_du`（DU Rule）: `docs/ranking/rank_du.md`
- `rank_red-index`（Red Index Rule）: `docs/ranking/rank_red-index.md`
- `rank_g-lexcel`（Group Lex-cel）: `docs/ranking/rank_g-lexcel.md`
- `rank_g-o-banzhaf`（Group Ordinal Banzhaf）: `docs/ranking/rank_g-o-banzhaf.md`

## 4. 公理チェック（集計）

現行コードには、ランキング結果（`outputs/rankings/nN/game_*.csv`）に対して
公理の「制約がかかる比較数 / 要求を満たす比較数」を集計する機構があります。

- 入力: `outputs/rankings/nN/game_*.csv`
- 出力: `outputs/axiom/nN/*.csv`（1行=1ゲーム）
- CLI: `poetry run game-gen check-axioms -p N`
- `pipeline` 実行時にも、最後に公理チェックを行う（対象ルールが存在する場合のみ）。

- 目次・ルール別設計書: `docs/axioms/README.md`

## 5. 可視化

### 5.1 PNG 図（make-figures / make-figures-png）

- 入力: `<out>/rankings/**.csv`
- 出力: `<out>/figures/nN/<stem>.png`
- 処理:
  - 左: team ranking（`rank` と `score`）
  - 右: 存在する `rank_*` 列（5ルールのみ）を表として横に並べる
- 実装:
  - コマンド: `gamegen/commands/figures.py:make_figures`（PNG生成）
  - コマンド: `gamegen/commands/figures.py:make_figures_png`
  - 描画: `gamegen/figures_png.py:generate_team_ranking_figure`

### 5.3 ランク相関ヒートマップ（rank-heatmap）

- 入力: `<out>/rankings/nN/game_*.csv`
- 出力: `<out>/heatmaps/nN/<x>_vs_<y>.png`
- 仕様:
  - 相関用の「有効順位」は `rank_*` 列から次で定義する（tie の影響を抑える目的）:
    - `effective_rank(A) = 1 + |{ B : rank(B) < rank(A) }|`
    - これは dense rank を competition rank（`1,1,3,4,...`）へ変換することに相当
    - 各ゲーム CSV ごとに、比較対象（個人: singleton 行 / グループ: 非空提携行）内で列ごとに変換する
  - 個人ルール同士／グループルール同士のペアのみを集計対象とする（混在はスキップ）。
  - ペアの指定:
    - `config.yaml:rank_heatmap.pairs` が `all` の場合、対象スコープ内の全組み合わせを自動生成
    - リスト指定の場合はそのペアだけ作成
- 実装:
  - 集計・描画: `gamegen/rank_heatmap.py`
  - CLI: `gamegen/commands/heatmaps.py:rank_heatmap`
  - 詳細仕様: `docs/design/heatmaps.md`
  - `pipeline` / `apply-rules` 実行時の自動生成は `config.yaml:pipeline.rank_heatmaps` が true のときのみ（既定: false）

### 5.4 ルール×ルールの順位相関ヒートマップ（rule-corr-heatmap）

- 目的: ルール同士の「順位相関の程度」（相関係数）を、ルールを縦軸/横軸に並べた行列として可視化する。
- 入力: `<out>/rankings/nN/game_*.csv`
- 出力:
  - `<out>/heatmaps/nN/rule_corr_player.png`（個人ルール同士）
  - `<out>/heatmaps/nN/rule_corr_coalition.png`（グループ/提携ルール同士）
- 仕様:
  - 各列は 5.3 と同じ `effective_rank`（strictly-better count + 1）に変換してから集計する
  - 相関係数は `pandas.DataFrame.corr(method=...)` で計算（既定: Spearman）
  - 設定: `config.yaml:rule_corr_heatmap.method`
- 実装:
  - 集計: `gamegen/rank_heatmap.py:collect_rule_correlation_matrix`
  - 描画: `gamegen/rank_heatmap.py:render_correlation_heatmap`
  - CLI: `gamegen/commands/heatmaps.py:rule_corr_heatmap`
  - `pipeline` 実行時にも best-effort で生成する
  - 詳細仕様: `docs/design/heatmaps.md`
