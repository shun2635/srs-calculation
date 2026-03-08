# `rank_red-index`（Red Index Rule による冗長性ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先:
  - ランキング CSV の `rank_red-index` 列（順位）
  - ランキング CSV の `score_red-index` 列（Redundancy Index）
  - **非空連合**のみ値が入り、空集合は空欄になります（`gamegen/commands/rankings.py`）。

## 入力（ranking 情報のみ）

このルールは **基数スコア（`score`）を使わず**、ランキング CSV の土台順位 `rank`（弱順序）だけを用います。

- 比較対象の提携集合: $X := 2^N \\setminus \\{\\emptyset\\}$（非空連合全体）
- 弱順序: `rank` 列（1 が最上位）
  - $A \\succsim B \\iff \\mathrm{rank}(A) \\le \\mathrm{rank}(B)$

## 定義（Redundancy Index）

任意の $S\\in X$ に対し

$$
\\mathrm{Red}_{\\succsim}(S)
:=
\\bigl|\\{\\, T\\in X \\mid S\\subset T \\ \\land\\ S\\succsim T \\,\\}\\bigr|
$$

を Redundancy Index と呼ぶ。

これは「$S$ を真に含む提携のうち、$S$ と同じかそれより劣っているもの」の個数である。

## ルール（相互作用比較）

$$
S\\;R^{I\\text{-}\\mathrm{Red}}_{\\succsim}\\;T
\\ \\Longleftrightarrow\\
\\mathrm{Red}_{\\succsim}(S)\\ \\ge\\ \\mathrm{Red}_{\\succsim}(T)
$$

## 計算方法（実装ベース）

`rank` 列（弱順序）から、各非空連合 $S$ について

- 全ての真上位包含 `T ⊃ S` を列挙し、
- 条件 `rank(S) <= rank(T)` を満たす個数を数える

ことで `score_red-index(S)` を得る（`gamegen/rules/red_index.py`）。

- 時間計算量（目安）: 概ね $O(3^n)$

## 実装

- 主要実装: `gamegen/rules/red_index.py`
- ランキング列への反映: `gamegen/commands/rankings.py`

