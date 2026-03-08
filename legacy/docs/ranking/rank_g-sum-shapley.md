# `rank_g-sum-shapley`（各メンバーの Shapley 値合算による連合ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先:
  - ランキング CSV の `rank_g-sum-shapley` 列（順位）
  - ランキング CSV の `score_g-sum-shapley` 列（合算 Shapley 値）
  - **非空連合**のみ値が入り、空集合は空欄になります（`gamegen/ranking/registry.py`）。

## 入力（ゲームの表現）

- 連合 $S \\subseteq N$ はビットマスク `mask`（`int`）で表す（bit0 = player1）。
- 特性関数 $v(S)$ はゲーム/ランキング CSV の `score` 列（`mask -> score`）として与える。

## 定義（sum of member Shapley values）

まず、元のゲーム $v$ に対する各プレイヤー $i\\in N$ の Shapley 値 $\\phi_v(i)$ を
標準定義（`rank_shapley` と同一）で計算する。

非空連合 $C\\subseteq N$ に対し、合算 Shapley 値を
$$
\\phi^{\\mathrm{sum}}_v(C) := \\sum_{i\\in C} \\phi_v(i)
$$
で定義し、空集合は $\\phi^{\\mathrm{sum}}_v(\\emptyset):=0$ とする。

## 計算方法（実装ベース）

1. `gamegen/rules/shapley.py` の `player_shapley_values()` で $\\phi_v(i)$ を計算する。
2. 各連合 `mask`（`1..2^n-1`）について、立っているビットに対応するプレイヤーの $\\phi_v(i)$ を合計し
   `score_g-sum-shapley[mask]` とする。

## ランク化（dense rank）

- `score_g-sum-shapley` の **降順**で並べ、同値は同順位の **dense rank** を付与します。
- タイブレーク（安定化）: `mask` 昇順。

## 実装

- 主要実装: `gamegen/rules/group_sum_shapley.py`
- ランキング列への反映（非空連合のみ）: `gamegen/commands/rankings.py`

