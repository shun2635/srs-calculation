# `rank_rp-index`（RP Index Rule による相互作用ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先:
  - ランキング CSV の `rank_rp-index` 列（順位）
  - ランキング CSV の `score_rp-index` 列（RP Index）
  - 定義上 $|S|\\ge 2$ なので、**|S|>=2 の連合行のみ**値が入り、singleton/空集合は空欄になります（`gamegen/commands/rankings.py`）。

## 入力（ranking 情報のみ）

このルールは **基数スコア（`score`）を使わず**、ランキング CSV の土台順位 `rank`（弱順序）だけを用います。

- 比較対象の提携集合: $X := 2^N \\setminus \\{\\emptyset\\}$（非空連合全体）
- 弱順序: `rank` 列（1 が最上位）
  - $S \\succ T \\iff \\mathrm{rank}(S) < \\mathrm{rank}(T)$

## 定義（Rank Point / RP Index）

### Rank Point（符号付き Borda 得点）

$$
\\mathrm{RP}_{\\succsim}(S)
:=
\\bigl|\\{\\,T\\in X \\mid S\\succ T\\,\\}\\bigr|
\\;-\;
\\bigl|\\{\\,T\\in X \\mid T\\succ S\\,\\}\\bigr|
$$

（$S$ より下位にある提携数 − $S$ より上位にある提携数）

### RP Index（Rank Point 差分指標）

$|S|\\ge 2$ のとき

$$
\\Delta^{\\mathrm{RP}}_{\\succsim}(S)
:=
\\mathrm{RP}_{\\succsim}(S)
\\;-\;
\\frac{1}{|S|}\\sum_{i\\in S}\\mathrm{RP}_{\\succsim}(\\{i\\})
$$

## ルール（相互作用比較）

$$
S\\;R^{I\\text{-}\\mathrm{RP}}_{\\succsim}\\;T
\\ \\Longleftrightarrow\\
\\Delta^{\\mathrm{RP}}_{\\succsim}(S)\\ \\ge\\ \\Delta^{\\mathrm{RP}}_{\\succsim}(T)
$$

## 計算方法（実装ベース）

1. `rank` 列から、非空連合 $X$ 上の strict 比較数を数える
   - `rank` ごとのサイズから、
     - 上位個数（strictly better の数）
     - 下位個数（strictly worse の数）
     を prefix/suffix で求め、`RP(S)=worse-better` を得る
2. singleton `{i}` の RP を用意し、$|S|\\ge2$ の連合について
   - `score_rp-index(S) = Δ^RP(S)` を計算する
3. `score_rp-index` の降順で dense rank を付与し `rank_rp-index` を得る

## 実装

- 主要実装: `gamegen/rules/rp_index.py`
- ランキング列への反映: `gamegen/commands/rankings.py`

