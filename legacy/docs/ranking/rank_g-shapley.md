# `rank_g-shapley`（Shapley group value による連合ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先:
  - ランキング CSV の `rank_g-shapley` 列（順位）
  - ランキング CSV の `score_g-shapley` 列（Shapley group value）
  - **非空連合**のみ値が入り、空集合は空欄になります（`gamegen/ranking/registry.py`）。

## 入力（ゲームの表現）

- 連合 $S \\subseteq N$ はビットマスク `mask`（`int`）で表す（bit0 = player1）。
- 特性関数 $v(S)$ はゲーム/ランキング CSV の `score` 列（`mask -> score`）として与える。

## 定義（merging characteristic function と group value）

非空な提携 $C\\subseteq N$ に対し、代理プレイヤーを $c\\notin N$ とし
統合後のプレイヤー集合を
$$
N_C := (N\\setminus C)\\cup\\{c\\}
$$
で定義する。

このとき merging characteristic function $v_C:2^{N_C}\\to\\mathbb{R}$ を
$$
v_C(S)
:=
\\begin{cases}
v(S), & c\\notin S,\\\\
v\\bigl((S\\setminus\\{c\\})\\cup C\\bigr), & c\\in S,
\\end{cases}
\\qquad (\\forall S\\subseteq N_C)
$$
で定義する。

Shapley group value は
$$
\\phi^{g}_v(C) := \\phi_{v_C}(c)
$$
（代理プレイヤー $c$ の Shapley value）として定義し、空集合は $\\phi^g_v(\\emptyset):=0$ とする。

## 計算方法（実装ベース）

上の定義をそのまま用いると「各 $C$ ごとに $v_C$ を作って Shapley 値を計算」になりますが、
差分は次の形に簡約できます（`gamegen/rules/group_shapley.py`）。

プレイヤー数を $n=|N|$、$k=|C|$、$m=|N_C|=n-k+1$ とする。
$T\\subseteq N\\setminus C$（これは $N_C\\setminus\\{c\\}$ の部分集合に対応）とすると、

- $v_C(T)=v(T)$（$c\\notin T$）
- $v_C(T\\cup\\{c\\})=v(T\\cup C)$（$c$ を含むなら $C$ に置換）

よって
$$
\\phi^{g}_v(C)
=
\\sum_{T\\subseteq N\\setminus C}
\\frac{|T|!\\,(m-|T|-1)!}{m!}
\\bigl(v(T\\cup C)-v(T)\\bigr).
$$

この式を bitmask 上で評価することで、各非空連合 $C$ の `score_g-shapley` を得る。

## ランク化（dense rank）

- `score_g-shapley` の **降順**で並べ、同値は同順位の **dense rank** を付与します。
- タイブレーク（安定化）: `mask` 昇順。

## 実装

- 主要実装: `gamegen/rules/group_shapley.py`
- ランキング列への反映（非空連合のみ）: `gamegen/commands/rankings.py`

