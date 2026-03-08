# `rank_banzhaf`（Banzhaf Value による個人ランキング）

## 何をランキングするか

- 対象: **プレイヤー（個人）**
- 出力先:
  - ランキング CSV の `rank_banzhaf` 列（順位）
  - ランキング CSV の `score_banzhaf` 列（Banzhaf Value; 定義式の値）
  - **単独連合（singleton）行**のみ値が入り、それ以外の連合行は空欄になります（`gamegen/ranking/registry.py`）。

> 注意: `o-banzhaf` は「序数的（ordinal）Banzhaf」であり、`rank`（等級）のみを使う別ルールです。
> ここでの `banzhaf` は定義式に基づく **Banzhaf Value** で、`score`（特性関数値）を使います。

## 入力（ゲームの表現）

- 連合 $S \\subseteq N$ はビットマスク `mask`（`int`）で表す（bit0 = player1）。
- 特性関数 $v(S)$ はゲーム/ランキング CSV の `score` 列（`mask -> score`）として与える。

## 定義（Banzhaf Value）

プレイヤー $i\\in N$ の Banzhaf Value $\\phi_v(i)$ は次で定義されます：

$$
\\phi_v(i)
:= \\frac{1}{2^{n-1}}
   \\sum_{S \\subseteq N \\setminus \\{i\\}}
   \\bigl(v(S\\cup\\{i\\}) - v(S)\\bigr).
$$

## 計算方法（実装ベース）

実装では bitmask を用いて次を行います（`gamegen/rules/banzhaf.py`）。

- 各プレイヤー i（0..n-1）について、bit i が 0 の全 `mask` を列挙し、
  - `with_i = mask | (1<<i)`
  - 加算する差分 `v(with_i) - v(mask)`
- 合計を `2^(n-1)` で割って `score_banzhaf`（= Banzhaf Value）とする

## ランク化（dense rank）

- `score_banzhaf` の **降順**で並べ、同値は同順位の **dense rank** を付与します。
- タイブレーク（安定化）: インデックス昇順（player1, player2, ...）。

## 実装

- 主要実装: `gamegen/rules/banzhaf.py`
- ランキング列への反映（singleton 行のみ）: `gamegen/commands/rankings.py`
