# `rank_banzhaf-interaction`（Banzhaf Interaction Index による連合ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先:
  - ランキング CSV の `rank_banzhaf-interaction` 列（順位）
  - ランキング CSV の `score_banzhaf-interaction` 列（Banzhaf Interaction Index）
  - **非空連合**のみ値が入り、空集合は空欄になります（`gamegen/commands/rankings.py`）。

## 入力（ゲームの表現）

- 連合 $S \\subseteq N$ はビットマスク `mask`（`int`）で表す（bit0 = player1）。
- 特性関数 $v(S)$ はゲーム/ランキング CSV の `score` 列（`mask -> score`）として与える。

## 定義（Banzhaf Interaction Index）

特性関数 $v:2^N\\to\\mathbb{R}$ に対して、提携 $S\\subseteq N$ の相互作用指標
Banzhaf Interaction Index $I_v^{B}(S)$ を次で定義する：

$$
I_v^{B}(S)
:=
\\frac{1}{2^{\\,n-s}}
\\sum_{T \\subseteq N \\setminus S}
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
I_v^{B}(S) = \\frac{1}{2^{n-s}} \\sum_{T\\subseteq N\\setminus S} \\Delta_S v(T)
$$

として計算する。

実装では、全ての $T$ に対して
「$N\\setminus T$ 上の部分集合Möbius変換（in-place）」で $\\Delta_S v(T)$ を一括計算し、
定義どおりに加算する（`gamegen/rules/banzhaf_interaction.py`）。

- 時間計算量（目安）: 概ね $O(n\\,3^n)$

## 補足（|S|=1）

$|S|=1$ のとき、上の定義は Banzhaf value と一致します（`score_banzhaf` と同じ値）。

## ランク化（dense rank）

- `score_banzhaf-interaction` の **降順**で並べ、同値は同順位の **dense rank** を付与します。
- タイブレーク（安定化）: `mask` 昇順。

## 実装

- 主要実装: `gamegen/rules/banzhaf_interaction.py`
- ランキング列への反映（非空連合のみ）: `gamegen/commands/rankings.py`

