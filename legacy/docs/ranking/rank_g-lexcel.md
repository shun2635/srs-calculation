# `rank_g-lexcel`（Group Lex-cel による連合ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先: ランキング CSV の `rank_g-lexcel` 列
  - **非空連合**のみ値が入り、空集合は空欄になります（`gamegen/ranking/registry.py`）。

## 入力

- 連合の等級（弱順序）はゲーム CSV の `rank` 列（密順位、**1 が最上位**）。
- 等級 $k(S)$ から層（layer）を作る:
  $$
    \Sigma_r := \{\, S \subseteq N \mid k(S)=r \,\}
  $$

## 計算方法

各非空連合 $T\neq\emptyset$ に対し、層ごとの上位包含数ベクトル $\Theta(T)$ を作って比較します（`gamegen/rules/group_lexcel.py`）。

1. $\Theta(T)$ を
   $$
     \Theta(T) := (\Theta_1(T),\dots,\Theta_\ell(T))
   $$
   と定義する（$\ell$ は層の数）。
2. 各成分は
   $$
     \Theta_r(T) := |\{\, S \in \Sigma_r \mid S \supseteq T \,\}|
   $$
   （層 $\Sigma_r$ の中で $T$ を含む連合の個数）。
3. $\Theta(T)$ を **辞書式降順**で比較して順位付けする。

実装では $\Theta_r(T)$ を各層の指示関数に対する **上向きゼータ変換（superset zeta transform）**で一括計算します。

## ランク化（dense rank）

- $\Theta(T)$ の辞書式降順で並べ、同一ベクトルは同順位の **dense rank**。

## 実装

- 主要実装: `gamegen/rules/group_lexcel.py`
- ゲーム `rank`→層 $\Sigma_r$ の構築: `gamegen/ranking/registry.py`

