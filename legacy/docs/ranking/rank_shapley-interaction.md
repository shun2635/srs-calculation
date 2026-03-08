# `rank_shapley-interaction`（Shapley Interaction Index による連合ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先:
  - ランキング CSV の `rank_shapley-interaction` 列（順位）
  - ランキング CSV の `score_shapley-interaction` 列（Shapley Interaction Index）
  - **非空連合**のみ値が入り、空集合は空欄になります（`gamegen/commands/rankings.py`）。

> 補足: $|S|=1$ のとき、Shapley Interaction Index は通常の Shapley value と一致します。
> 本ルールは定義式に基づいて **厳密に計算**するため、`shapley` ルール（厳密計算）とは
> 単独連合（singleton）行で値が一致しない可能性があります。

## 入力（ゲームの表現）

- 連合 $S \\subseteq N$ はビットマスク `mask`（`int`）で表す（bit0 = player1）。
- 特性関数 $v(S)$ はゲーム/ランキング CSV の `score` 列（`mask -> score`）として与える。

## 定義（Shapley Interaction Index）

特性関数 $v:2^N\\to\\mathbb{R}$ に対して、提携 $S\\subseteq N$ の相互作用指標
Shapley Interaction Index $I^S_v(S)$ を次で定義する：

$$
I^S_v(S)
:=
\\sum_{T \\subseteq N \\setminus S}
\\frac{(n - t - s)! \\, t!}{(n - s + 1)!}
\\sum_{L \\subseteq S}
(-1)^{\\,s-l}\\, v(L \\cup T),
$$

ただし $n=|N|$, $s=|S|$, $t=|T|$, $l=|L|$ とする。

## 計算方法（実装ベース）

内部では

$$
\\Delta_S v(T) := \\sum_{L\\subseteq S} (-1)^{s-|L|} v(T\\cup L)
$$

（$S$ に関する離散微分）とおき、

$$
I^S_v(S) = \\sum_{T\\subseteq N\\setminus S} w(n,s,t)\\,\\Delta_S v(T),
\\quad
w(n,s,t)=\\frac{(n-t-s)!\\,t!}{(n-s+1)!}
$$

として計算する。

実装では全ての $T\\subseteq N$ について
「$N\\setminus T$ 上の部分集合Möbius変換（in-place）」を行い、
各 $(T,S)$ の $\\Delta_S v(T)$ を一括で得て加算する（`gamegen/rules/shapley_interaction.py`）。

- 時間計算量（目安）: 概ね $O(n\\,3^n)$
- 出力: 全ての非空 $S$ に対する `score_shapley-interaction`（実数）

## ランク化（dense rank）

- `score_shapley-interaction` の **降順**で並べ、同値は同順位の **dense rank** を付与します。
- タイブレーク（安定化）: `mask` 昇順。

## 実装

- 主要実装: `gamegen/rules/shapley_interaction.py`
- ランキング列への反映（非空連合のみ）: `gamegen/commands/rankings.py`
