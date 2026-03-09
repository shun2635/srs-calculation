# 仕様書: `srs-game-gen` の synthetic-game methodology

## Summary

この文書は、root CLI の `srs-game-gen` が現在サポートする synthetic-game workflow を、論文・appendix・研究メモでそのまま参照できる粒度で固定するための仕様書です。

対象は次です。

- シミュレーション設定
- ゲーム生成とランダム化
- 基底順位 `rank` と各 rule の順位生成
- `rank-heatmap` と `rule-corr-heatmap` の計算方法
- 再現性のために記録すべき項目

この文書は日本語版です。内容は [English version](../../en/specs/synthetic-game-methodology.md) と同期対象です。どちらかを更新した場合は、もう一方も見直してください。

## Scope

この仕様は、root CLI 契約に含まれる次の synthetic command を対象にします。

- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen rank-game`
- `srs-game-gen make-figures`
- `srs-game-gen rank-heatmap`
- `srs-game-gen rule-corr-heatmap`

対象外:

- archive-only command である `game-gen check-axioms`
- archive-only command である `game-gen summarize-axioms`
- archive-only command である `game-gen axiom-summary-heatmap`
- archive-only command である `game-gen pipeline`
- archive-only command である `game-gen make-figures-png`

## 1. Workflow の全体像

現在の synthetic workflow は、標準的には次の 4 段で使います。

1. `srs-game-gen gen-games` で complete game CSV を生成する
2. `srs-game-gen apply-rules` で ranking rule を適用して rankings CSV を生成する
3. `srs-game-gen make-figures` で rankings CSV の table figure を生成する
4. 必要に応じて `srs-game-gen rank-heatmap` と `srs-game-gen rule-corr-heatmap` で順位比較を可視化する

生成物の既定配置は次です。

- games: `outputs/games/nN/game_*.csv`
- rankings: `outputs/rankings/nN/game_*.csv`
- figures: `outputs/figures/nN/game_*.png`
- heatmaps: `outputs/heatmaps/nN/*.png`

ここで `N` はプレイヤー数です。

## 2. シミュレーション設定

### 2.1 プレイヤー数

- CLI 引数 `--players` または `-p` で指定する
- 現行 CLI では `1 <= n <= 12`
- 各ゲームは `n` 人の complete cooperative game として扱う

### 2.2 ゲーム数

- `gen-games` では `--count` または `-c` で指定する
- 未指定時は `config.gen_games.count`
- config にも無ければ既定値は `1`

### 2.3 スコア上限

- `gen-games` では `--max-score` で指定する
- 未指定時は `config.gen_games.max_score`
- config にも無ければ既定値は `2^n - 1`

### 2.4 出力先

- `--out` で output base directory を指定する
- 未指定時は `config.output_base`
- config にも無ければ既定値は `outputs`

### 2.5 config 解決順

root CLI の config 解決順は次です。

1. 明示 CLI 引数
2. `--config <path>` で渡した YAML
3. `src` 側 built-in default

補足:

- `legacy/config.yaml` は暗黙には参照しない
- repository root の `./config.yaml` も自動探索しない
- 相対 `output_base` は、`--config` を使った場合はその config file からの相対パスとして解決する

## 3. ゲーム生成の方法

### 3.1 ゲームの定義

各 synthetic game は、プレイヤー集合 `N = {1, ..., n}` 上の complete cooperative game として表現します。

- 各連合は bitmask で表す
- `player1` が bit 0, `player2` が bit 1, ... に対応する
- 1 ゲームあたりの連合数は `2^n`

### 3.2 coalition score のランダム生成

各連合 `S ⊆ N` に対して、coalition score `v(S)` を独立にサンプルします。

- 乱数生成器: Python 標準ライブラリの `random.Random(seed)`
- 分布: 離散一様分布 `Uniform({0, 1, ..., M})`
- ここで `M = max_score`

実装上は、各 `mask` について `rng.randint(0, max_score)` を 1 回呼び、その値を `float` に変換して保存します。

重要な注意:

- 空連合 `∅` も他の連合と同様にランダム生成する
- 現行 workflow は `v(∅)=0` を強制しない
- 単調性、超加法性、凸性、単純ゲーム性などの構造制約は課さない

したがって、現在の root synthetic workflow は「制約なしの complete game table を iid な離散一様乱数から生成する設定」です。

### 3.3 複数ゲーム生成時の RNG 消費

`--count K` のとき:

- 1 つの `random.Random(seed)` を workflow 全体で共有する
- ゲーム 1, 2, ..., K を順に生成する
- 各ゲームは同じ RNG の連続した状態から生成される

したがって、`(n, count, max_score, seed)` が同じなら、理論上同じ乱数列が消費され、同じゲーム列が再現されます。

### 3.4 ファイル名と index の付け方

生成ファイル名は `game_000001.csv`, `game_000002.csv`, ... の形です。

- 既存ファイルがある場合は、未使用の最小 index を順に採用する
- index 自体は directory state に依存する
- 一方、乱数列の消費順は 1 回の実行内での生成順に依存する

したがって、再現性を論文で主張する場合は、directory の事前状態よりも「生成対象の空ディレクトリ」「seed」「count」「players」「max_score」を揃える方が重要です。

## 4. game CSV の書き出し規約

### 4.1 行順

game CSV の連合行は次の順序で並びます。

1. `score` 降順
2. 同点時は bitmask 昇順

この tie-break は、同点時の表示順を決定的にするためのものです。

### 4.2 基底列 `rank`

game CSV の `rank` 列は、coalition score に対する dense descending rank です。

- 最良 score を `rank = 1`
- 同点は同じ rank
- score 値が変わるたびに rank を `+1`

例:

- `score = [10, 10, 8, 3, 3]`
- `rank = [1, 1, 2, 3, 3]`

この `rank` は「生成されたゲームそのものの coalition score 順位」であり、rule 出力の順位とは別です。

### 4.3 game CSV の列

既定の game CSV header は次です。

- `player1`, `player2`, ..., `playerN`
- `score`
- `rank`

各 `playeri` 列は 0/1 membership を表します。

## 5. ランキング規則の適用方法

### 5.1 現在の root サポート対象規則

`apply-rules` で `--rule` を指定しない場合、current default registry の全 rule を適用します。

現在の対象は次です。

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`
- `group_shapley`
- `group_sum_shapley`
- `group_ordinal_banzhaf`
- `group_lexcel`
- `shapley_interaction`
- `banzhaf_interaction`
- `rp_index`
- `ud`
- `du`
- `red_index`

### 5.2 `shapley`

各プレイヤー `i` に対し、すべての `S ⊆ N \ {i}` について marginal contribution

`v(S ∪ {i}) - v(S)`

を計算し、Shapley 係数

`|S|! (n-|S|-1)! / n!`

で重み付けして総和した値を score とします。

その後、player score の降順 dense rank を内部 rank とします。

### 5.3 `banzhaf`

各プレイヤー `i` に対し、すべての `S ⊆ N \ {i}` について

`v(S ∪ {i}) - v(S)`

を総和し、`2^(n-1)` で割った値を score とします。

その後、player score の降順 dense rank を内部 rank とします。

### 5.4 `lexcel`

まず coalition score の distinct value を高い順に `level = 1, 2, ...` と割り当てます。

各プレイヤーについて、各 level に属する連合のうちそのプレイヤーを含むものの数を数え、`theta` ベクトル

`theta_i = (c_{i,1}, c_{i,2}, ..., c_{i,L})`

を作ります。

プレイヤー順位は、この `theta` を lexicographic descending に比較して決めます。`lexcel` は現行の compatibility CSV には score 列を書かず、rank 列のみを書きます。

### 5.5 `ordinal_banzhaf`

まず coalition score の distinct value を高い順に `level = 1, 2, ...` と割り当てます。

各プレイヤー `i` と各 `S ⊆ N \ {i}` について:

- `i` を追加して level が改善する場合を `u_plus(i)` に数える
- `i` を追加して level が悪化する場合を `u_minus(i)` に数える

score は

`u_plus(i) - u_minus(i)`

で定義します。

その後、score の降順 dense rank を内部 rank とします。

### 5.6 complete game 要件

`apply-rules` と `rank-game` は既定では complete game を要求します。

- 既定: `--require-complete`
- 例外: `--allow-incomplete` を付けた場合だけ incomplete table を許容する

通常の論文用 synthetic workflow では complete game を前提にするべきです。

### 5.7 base `rank` に依存する coalition rule

移行済み rule は、同じ入力を使っているわけではありません。

- `shapley`, `banzhaf`, `group_shapley`, `group_sum_shapley`, `shapley_interaction`, `banzhaf_interaction` は coalition score に依存する cardinal rule です
- `ordinal_banzhaf`, `group_ordinal_banzhaf`, `group_lexcel`, `rp_index`, `ud`, `du`, `red_index` は serialzed base `rank` の level 構造に依存します

synthetic game では base `rank` は生成 score から導かれるので両者は整合しますが、import 済み real-data game ではこの違いが重要です。

## 6. rankings CSV の書き出し規約

### 6.1 base 列

rankings CSV には、元の game CSV と同じ base 列

- `score`
- `rank`

が残ります。これらは coalition score に対する base 情報です。

### 6.2 rule 列

現行実装の compatibility-format では、各 rule は次の列名に serialize されます。

- `shapley` -> `score_shapley`, `rank_shapley`
- `banzhaf` -> `score_banzhaf`, `rank_banzhaf`
- `lexcel` -> `rank_lexcel`
- `ordinal_banzhaf` -> `rank_o-banzhaf`
- `group_shapley` -> `score_g-shapley`, `rank_g-shapley`
- `group_sum_shapley` -> `score_g-sum-shapley`, `rank_g-sum-shapley`
- `group_ordinal_banzhaf` -> `rank_g-o-banzhaf`
- `group_lexcel` -> `rank_g-lexcel`
- `shapley_interaction` -> `score_shapley-interaction`, `rank_shapley-interaction`
- `banzhaf_interaction` -> `score_banzhaf-interaction`, `rank_banzhaf-interaction`
- `rp_index` -> `score_rp-index`, `rank_rp-index`
- `ud` -> `score_ud_up`, `score_ud_down`, `rank_ud`
- `du` -> `score_du_up`, `score_du_down`, `rank_du`
- `red_index` -> `score_red-index`, `rank_red-index`

補足:

- `ordinal_banzhaf` は内部的には score を持つが、現行 compatibility CSV には `score_o-banzhaf` を書かない
- 列順は canonical compatibility order に従って固定する

### 6.3 player-scope と coalition-scope の serialize

移行済み synthetic rule 群には、player-scope と coalition-scope の両方があります。

- player-scope rule は singleton coalition 行にのみ `score_*` / `rank_*` を書く
- coalition-scope rule は非空 coalition 行すべてに `score_*` / `rank_*` を書く
- empty coalition 行は coalition-scope の派生列でも空欄にする

この設計は、historical CSV との互換性維持のためです。

### 6.4 `rank_style`

内部 rank は dense rank ですが、CSV に書く `rank_*` は `--rank-style` に従います。

- 既定値: `competition`
- 代替: `dense`

`competition` の例:

- dense: `1, 1, 2, 3`
- competition: `1, 1, 3, 4`

論文では、serialized rank を使う場合に `competition` か `dense` かを明示すべきです。root CLI の既定は `competition` です。

## 7. `make-figures` の意味

`srs-game-gen make-figures` は、rankings CSV を読みやすい PNG table figure に変換する command です。

- 入力: `outputs/rankings/**/game_*.csv`
- 出力: `outputs/figures/**/game_*.png`

この command 自体は新しい rank statistic や correlation statistic を計算しません。既存の CSV に入っている:

- base の `score`, `rank`
- 各 `rank_*` 列

を可視化するだけです。

## 8. 順位相関と順位比較の計算方法

### 8.1 effective rank の定義

`rank-heatmap` と `rule-corr-heatmap` は、serialized rank label をそのまま比較しません。まず各 `rank_*` 列を effective rank に変換します。

定義は次です。

`effective_rank(A) = 1 + |{B : rank(B) < rank(A)}|`

これは「自分より strictly better な要素数 + 1」であり、competition-style の tie block 開始位置に対応します。

この前処理により:

- dense rank と competition rank の表記差を吸収できる
- tie の比較を block 単位で安定化できる

### 8.2 scope の扱い

heatmap 系 command は rank column ごとに scope を判定します。

- singleton 以外にも値が現れる列は coalition-scope
- singleton 行にしか値が現れない列は player-scope

現行の migrated rule 群には両 scope があるので、player / coalition の両方の heatmap が生成され得ます。

### 8.3 `rank-heatmap`

`rank-heatmap` は、2 つの `rank_*` 列 `x_col`, `y_col` を選び、各 file ごとに次を行います。

1. 対象 scope の行に制限する
2. `x_col` と `y_col` の両方が non-null な行だけを残す
3. その file 内・その有効行集合内で、`x_col` と `y_col` をそれぞれ effective rank に変換する
4. effective rank の組 `(r_x, r_y)` の出現回数を数える
5. file 間で頻度を合算する

結果は frequency matrix として描画します。

現行実装の既定は次です。

- 既定ペア: `rank_lexcel` vs `rank_shapley`
- 出力先: `outputs/heatmaps/nN/<x_col>_vs_<y_col>.png`
- 既定 DPI: `150`

config `rank_heatmap.pairs` に次を与えることもできます。

- 明示 list: 描画する pair を固定
- `all` または `auto`: 同じ scope 内の全 pair を描画

### 8.4 `rule-corr-heatmap`

`rule-corr-heatmap` は、複数の rankings CSV を縦に連結して rule 間相関を計算します。

計算手順は次です。

1. 各 file について、各 `rank_*` 列を scope 内の有効行に対して effective rank に変換する
2. player-scope rule は singleton 行、coalition-scope rule は非空 coalition 行に制限する
3. file ごとに得られた effective-rank table を縦に連結する
4. `pandas.DataFrame.corr(method=..., min_periods=1)` を適用して rule×rule 相関行列を計算する

相関 method:

- 既定値: `spearman`
- 上書き: CLI `--method`
- さらに config `rule_corr_heatmap.method` でも指定可能

出力は scope ごとに分かれます。

- player-scope があれば `rule_corr_player.png`
- coalition-scope があれば `rule_corr_coalition.png`

現行の migrated synthetic rules では、`rule_corr_player.png` と `rule_corr_coalition.png` の両方が生成され得ます。

### 8.5 historical method との関係

この rank-correlation method は historical archive の `legacy/src/gamegen/rank_heatmap.py` にあった考え方を `src/` 側へ移植したものです。

したがって、論文では:

- 現在の root-supported workflow の method
- historical archive 由来だが `src/` 側で明示的に再実装された method

のどちらとして説明してもよいですが、現時点では「現行 root workflow の method」として記述して差し支えありません。

## 9. CLI 上の重要な既定値

論文や appendix で再現性を重視するなら、次の CLI 既定値を暗黙にせず記録するべきです。

- `apply-rules --rank-style` の既定値は `competition`
- `rank-heatmap --dpi` の既定値は `150` または `config.figures.png_dpi`
- `rule-corr-heatmap --method` の既定値は `spearman`
- `make-figures --dpi` の既定値は `150` または `config.figures.png_dpi`

## 10. 論文で最低限記録すべき項目

次は最低限残してください。

- repository commit hash
- 実行した CLI command 全体
- `players`
- `count`
- `max_score`
- `seed`
- `rank_style`
- 適用 rule 一覧
- `--config` を使った場合はその YAML 内容
- 生成された output directory の保存先

## 11. 論文用の簡潔な method 文

例えば本文では、次のように要約できます。

> We generated complete cooperative games with `2^n` coalitions for `n` players. Each coalition score was sampled independently and uniformly from `{0, ..., M}` using Python's `random.Random(seed)` without imposing structural game constraints such as monotonicity or convexity. Coalition rows were ordered by descending score with a bitmask-based deterministic tie-break, and the base coalition-rank column was assigned as a dense descending rank. We then applied player-level ranking rules and serialized their output ranks in competition-rank format unless otherwise stated. For rank-comparison analyses, we transformed each serialized `rank_*` column into an effective rank defined by `1 + |{B : rank(B) < rank(A)}|`, and computed pairwise heatmaps or rule-correlation matrices from those effective ranks.

## Related documents

- [`../../README.md`](../../README.md)
- [`../../src/README.md`](../../src/README.md)
- [`../research-workflow.md`](../research-workflow.md)
- [`../adr/0002-retire-legacy-only-synthetic-commands.md`](../adr/0002-retire-legacy-only-synthetic-commands.md)
- [`../adr/0003-reintroduce-synthetic-rank-correlation-commands.md`](../adr/0003-reintroduce-synthetic-rank-correlation-commands.md)
- [`../../legacy/docs/design/heatmaps.md`](../../legacy/docs/design/heatmaps.md)
