# `rank_shapley`（Shapley 値による個人ランキング）

## 何をランキングするか

- 対象: **プレイヤー（個人）**
- 出力先:
  - ランキング CSV の `rank_shapley` 列（順位）
  - ランキング CSV の `score_shapley` 列（Shapley 値）
  - **単独連合（singleton）行**のみ値が入り、それ以外の連合行は空欄になります（`gamegen/ranking/registry.py`）。

## 入力（ゲームの表現）

- 連合 $S \subseteq N$ はビットマスク `mask`（`int`）で表す（bit0 = player1）。
- 値関数 $v(S)$ はゲーム CSV の `score` 列（`mask -> score`）として与える。
  - このルールは `rank`（等級）列ではなく **`score` を直接**使います。

## 計算方法（実装ベース）

本実装は Shapley 値の定義式に基づいて **厳密に計算**します（`gamegen/rules/shapley.py`）。

参考として、協力ゲームの Shapley 値の定義は次です:
$$
\phi_i(v)
=
\sum_{S \subseteq N \setminus \{i\}}
\frac{|S|!(n-|S|-1)!}{n!}\bigl(v(S\cup\{i\}) - v(S)\bigr).
$$

## ランク化（dense rank）

- $\phi_i$ の **降順**で並べ、同値は同順位の **dense rank** を付与します。
- タイブレーク（安定化）: インデックス昇順（player1, player2, ...）。

## 実装

- 主要実装: `gamegen/rules/shapley.py`
- ランキング列への反映（singleton 行のみ）: `gamegen/ranking/registry.py`
