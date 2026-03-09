# 仕様書: `srs-game-gen` のシミュレーション方法論

## Summary

この文書は、root CLI の `srs-game-gen` が現在サポートする synthetic-game workflow を、論文や研究メモで再利用できる粒度で明確化するための仕様書です。

対象は次です。

- シミュレーション設定
- ゲームスコアと基底順位の生成方法
- ランキング規則による順位列の生成方法
- ランダム化方法
- 順位相関の扱い

## Scope

この仕様は、root CLI 契約に含まれる次の command を対象にします。

- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen rank-game`
- `srs-game-gen make-figures`
- `srs-game-gen rank-heatmap`
- `srs-game-gen rule-corr-heatmap`

対象外:

- archive-only command である `game-gen check-axioms` などの周辺機能

## 1. シミュレーション設定

### 1.1 プレイヤー数

- CLI 引数 `--players` / `-p` で指定する
- 現行 CLI では `1 <= n <= 12`

### 1.2 ゲーム数

- CLI 引数 `--count` / `-c` で指定する
- 未指定時は `config.gen_games.count` を使い、さらに未指定なら `1`

### 1.3 スコア上限

- CLI 引数 `--max-score` で指定する
- 未指定時は `config.gen_games.max_score`
- さらに未指定時は `2^n - 1`

### 1.4 出力先

- CLI 引数 `--out`
- 未指定時は `config.output_base`
- さらに未指定時は `outputs`

### 1.5 config の優先順位

root CLI の config 解決順は次です。

1. 明示 CLI 引数
2. `--config <path>` で渡した YAML
3. `src` 側 built-in default

`legacy/config.yaml` や repository root の `./config.yaml` は暗黙には参照しません。

## 2. ゲーム生成の方法

### 2.1 ゲームの定義

各ゲームは、プレイヤー集合 `N = {1, ..., n}` に対する complete cooperative game として扱います。

- 各連合は bitmask で表現する
- `player1` が bit 0, `player2` が bit 1, ... に対応する
- 1 ゲームあたりの連合数は `2^n`

### 2.2 スコア生成

各連合 `S ⊆ N` に対して、独立に整数スコアを発生させます。

- 乱数生成器: `random.Random(seed)`
- 分布: 離散一様分布 `Uniform({0, 1, ..., M})`
- ここで `M = max_score`

実装上は、各 `mask` に対して `rng.randint(0, max_score)` を 1 回呼びます。

重要な注意:

- 空連合 `∅` も他の連合と同様にランダム生成される
- 現行 `srs-game-gen` は `v(∅)=0` を強制しない
- 単調性、超加法性、凸性などのゲーム理論的制約も impose しない

したがって、現行 root workflow の synthetic game は「制約なしの complete game table を離散一様乱数でサンプルする」設定です。

### 2.3 複数ゲーム生成時の乱数消費

`--count K` で複数ゲームを生成する場合:

- 1 つの `random.Random(seed)` を workflow 全体で共有する
- ゲーム 1, 2, ..., K を順番に生成する
- 各ゲームは同じ RNG の連続した状態から生成される

したがって、同じ `seed`, `n`, `count`, `max_score` を使えば、同じ列のゲーム CSV が再現されます。

### 2.4 ファイル名

出力先ディレクトリ内で `game_000001.csv`, `game_000002.csv`, ... のように保存します。

- 既存ファイルがある場合は、未使用の最小 index を順に採用する
- そのため filename は連番ですが、乱数系列自体は実行順に依存する

## 3. 基底順位 `rank` の生成方法

### 3.1 行順

game CSV への書き出し時、連合行は次で並べます。

1. `score` 降順
2. 同点時は bitmask 昇順

同点時の bitmask 昇順は、行順を決定的にするための tie-break です。

### 3.2 基底順位

game CSV の `rank` 列は、連合スコアに対する dense rank です。

- 最良スコアを rank `1`
- 同点は同じ rank
- スコア値が変わるたびに rank を `+1`

すなわち、

- `score = [10, 10, 8, 3, 3]`
- `rank = [1, 1, 2, 3, 3]`

となります。

この `rank` は「ゲーム自体の coalition score 順位」であり、各 ranking rule の出力順位とは別です。

## 4. ランキング規則の適用方法

### 4.1 現在の root サポート対象規則

`srs-game-gen apply-rules` で規則を明示しない場合、現在の default registry に入っている全 migrated rule を適用します。

現在の対象は次です。

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`

### 4.2 規則の意味

#### `shapley`

各プレイヤー `i` に対し、全ての `S ⊆ N \\ {i}` について

`v(S ∪ {i}) - v(S)`

を Shapley の係数

`|S|! (n-|S|-1)! / n!`

で重み付けして総和する。

#### `banzhaf`

各プレイヤー `i` に対し、全ての `S ⊆ N \\ {i}` について

`v(S ∪ {i}) - v(S)`

を単純に総和し、`2^(n-1)` で割る。

#### `lexcel`

連合スコアの distinct level を上位から `1, 2, ...` と振り、各プレイヤーについて

- level 1 の連合に何回含まれるか
- level 2 の連合に何回含まれるか
- ...

からなる `theta` ベクトルを作る。これを lexicographic descending に比較して順位を付ける。

#### `ordinal_banzhaf`

連合スコアの distinct level を上位から `1, 2, ...` と振る。各プレイヤー `i` と各 `S ⊆ N \\ {i}` について

- `i` を追加すると level が上がる回数を `u_plus(i)`
- `i` を追加すると level が下がる回数を `u_minus(i)`

とし、

`u_plus(i) - u_minus(i)`

を score とする。

### 4.3 内部順位と CSV への書き出し順位

各 rule の内部計算は、次の dense rank を返します。

- `shapley`, `banzhaf`, `ordinal_banzhaf`:
  player score の降順 dense rank
- `lexcel`:
  `theta` ベクトルの lexicographic descending dense rank

ただし、CSV 出力時の `rank_*` 列は CLI option `--rank-style` に従います。

- 既定: `competition`
- 代替: `dense`

`competition` の場合、同順位の人数を飛ばすので

- dense: `1, 1, 2, 3`
- competition: `1, 1, 3, 4`

となります。

### 4.4 `rank_*` / `score_*` 列の埋め方

現在の migrated rule はすべて player-scope rule です。そのため rankings CSV では:

- singleton 行にのみ `score_*` / `rank_*` を書く
- それ以外の連合行は空欄にする

互換列名は次です。

- `score_shapley`, `rank_shapley`
- `score_banzhaf`, `rank_banzhaf`
- `rank_lexcel`
- `rank_o-banzhaf`

現行実装では `ordinal_banzhaf` は score を内部で持ちますが、互換 CSV への serialize では score 列を書かず、`rank_o-banzhaf` のみを出力します。

## 5. `make-figures` の意味

`srs-game-gen make-figures` は、rankings CSV から PNG table figure を生成します。

- 入力: `outputs/rankings/**/game_*.csv`
- 出力: `outputs/figures/**/game_*.png`

図は、既存の CSV に入っている

- 基底 `rank`, `score`
- 各 `rank_*` 列

を読みやすく並べ直して描画するものであり、新しい統計量や相関係数を追加計算する command ではありません。

## 6. 順位相関の計算方法

### 6.1 現在の root `srs-game-gen`

現在の root CLI 契約には、次の順位比較 command が含まれます。

- `srs-game-gen rank-heatmap`
- `srs-game-gen rule-corr-heatmap`

どちらも、historical な `rank_*` 列をそのまま比較するのではなく、まず effective rank に変換してから扱います。

effective rank は competition-style に次で定義します。

`effective_rank(A) = 1 + |{B : rank(B) < rank(A)}|`

これは dense rank や serialized competition rank の違いを吸収し、同順位群の開始位置で比較するための前処理です。

### 6.2 `rank-heatmap`

`rank-heatmap` は 2 つの `rank_*` 列の組について、effective rank の組 `(r_x, r_y)` の出現頻度を集計し、2 次元 heatmap として描画します。

現行実装では:

- player-scope rule は singleton 行だけを集計対象にする
- coalition-scope rule は空連合を除く coalition 行を集計対象にする
- 既定のペアは `rank_lexcel` と `rank_shapley`
- `rank_heatmap.pairs: all` または `auto` が config にある場合は、同じ scope 内の全 pair を描画する

出力先は既定で `outputs/heatmaps/nN/` です。

### 6.3 `rule-corr-heatmap`

`rule-corr-heatmap` は複数の rankings CSV を縦に連結し、rule ごとの effective rank 列の相関行列を計算して heatmap を描画します。

計算手順は次です。

1. 各 `rank_*` 列を file ごとに effective rank へ変換する
2. player-scope rule は singleton 行、coalition-scope rule は空連合を除く coalition 行に制限する
3. 対象行を files 間で縦に連結する
4. `pandas.DataFrame.corr(method=...)` で rule×rule 相関行列を計算する

既定の method は `spearman` です。CLI の `--method` または config の `rule_corr_heatmap.method` で上書きできます。

### 6.4 historical archive との関係

historical archive の `legacy game-gen rule-corr-heatmap` では、順位相関を次のように定義していました。

1. 各 `rank_*` 列を file ごと・列ごとに competition-style の effective rank に変換する  
   `effective_rank(A) = 1 + |{B : rank(B) < rank(A)}|`
2. player rule なら singleton 行、coalition rule なら非空連合行だけを使う
3. 全 ranking CSV の対象行を縦に連結する
4. `pandas.DataFrame.corr(method=...)` を適用する
5. 既定 method は `spearman`

現行 root 実装は、この historical method を `src/` 側へ明示的に移植したものです。論文では current root workflow の method として記述して構いません。

## 7. Reproducibility に関する推奨記録項目

論文や appendix には、少なくとも次を固定または明記することを推奨します。

- commit hash
- command line
- `n`（players）
- `count`
- `max_score`
- `seed`
- `rank_style`
- 適用 rule の一覧
- `--config` を使った場合はその YAML 内容

## 8. Recommended paper wording

現在の root workflow をそのまま記述するなら、次のように書けます。

> We generated complete cooperative games with `2^n` coalitions. For each coalition, we sampled an integer score independently and uniformly from `{0, ..., M}` using Python's `random.Random(seed)`. Coalition rows were ordered by descending score with bitmask-based tie-breaking, and the base coalition rank column was assigned as a dense descending rank. Player-level ranking rules were then applied to each generated game, and their serialized output ranks were reported in competition-rank format unless otherwise specified.

## Related documents

- [`../../README.md`](../../README.md)
- [`../../src/README.md`](../../src/README.md)
- [`../research-workflow.md`](../research-workflow.md)
- [`../adr/0002-retire-legacy-only-synthetic-commands.md`](../adr/0002-retire-legacy-only-synthetic-commands.md)
- [`../adr/0003-reintroduce-synthetic-rank-correlation-commands.md`](../adr/0003-reintroduce-synthetic-rank-correlation-commands.md)
- [`../../legacy/docs/design/heatmaps.md`](../../legacy/docs/design/heatmaps.md)
