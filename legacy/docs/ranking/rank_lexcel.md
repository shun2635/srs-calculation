# `rank_lexcel`（Lex-cel による個人ランキング）

## 何をランキングするか

- 対象: **プレイヤー（個人）**
- 出力先: ランキング CSV の `rank_lexcel` 列
  - **単独連合（singleton）行**のみ値が入り、それ以外の連合行は空欄になります（`gamegen/ranking/registry.py`）。

## 入力

- 値関数 $v(S)$ はゲーム CSV の `score` 列（`mask -> score`）。
  - このルールは **`score` の大小**に基づいて計算します（`rank` 列は使いません）。

## 計算方法

1. 全連合を `score` 同値クラスで分割し、`score` 降順にレベル（等級）を割り当てる（1 が最上位）。
   - $\Sigma_k := \{\, S \subseteq N \mid \mathrm{level}(S)=k \,\}$
2. 各プレイヤー $i$ に対し、長さ $\ell$ のベクトル
   $$
     \theta(i)=(\theta_1(i),\dots,\theta_\ell(i))
   $$
   を作る。
   $$
     \theta_k(i) := |\{\, S \in \Sigma_k \mid i \in S \,\}|
   $$
   （空集合 $S=\emptyset$ は除外）
3. $\theta(i)$ を **辞書式降順**で比較して順位付けする。
   - $\theta_1$ が大きい方が上位、同値なら $\theta_2$、…の順に比較。

## ランク化（dense rank）

- $\theta(i)$ を辞書式降順に並べ、同一ベクトルは同順位の **dense rank**。
- タイブレーク（安定化）: インデックス昇順（player1, player2, ...）。

## 計算量（目安）

- レベル構築 $O(2^n \log 2^n)$、$\theta$ 構築 $O(n2^n)$。

## 実装

- 主要実装: `gamegen/rules/lexcel.py`
- ランキング列への反映（singleton 行のみ）: `gamegen/ranking/registry.py`

