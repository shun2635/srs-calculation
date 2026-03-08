# `rank_du`（(down,up) 辞書順にもとづく相互作用比較ルール）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先:
  - ランキング CSV の `rank_du` 列（順位）
  - ランキング CSV の `score_du_up` / `score_du_down` 列（Up/Down Count）
  - 定義上 $|S|\ge 2$ なので、**|S|>=2 の連合行のみ**値が入り、singleton/空集合は空欄になります。

## 入力（ranking 情報のみ）

このルールは **基数スコア（`score`）を使わず**、ランキング CSV の土台順位 `rank`（弱順序）だけを用います。

- 比較対象の提携集合: $X := 2^N \setminus \{\emptyset\}$（非空連合全体）
- 弱順序: `rank` 列（1 が最上位）
  - $A \succ B \iff \mathrm{rank}(A) < \mathrm{rank}(B)$

## 定義（Up/Down Count）

任意の非空提携 $T\subseteq N$ について

$$
\mathrm{up}_{\succsim}(T)
:=\bigl|\{\,i\in T \mid T\succ \{i\}\,\}\bigr|,
\quad
\mathrm{down}_{\succsim}(T)
:=\bigl|\{\,i\in T \mid \{i\}\succ T\,\}\bigr|.
$$

## ルール（DU / (down,up) 辞書順）

$|S|,|T|\ge 2$ のとき

$$
S\,R^{I\text{-}\mathrm{DU}}_{\succsim}\,T
\ \Longleftrightarrow\
\Bigl(\mathrm{down}(S)<\mathrm{down}(T)\Bigr)
\ \lor\
\Bigl(\mathrm{down}(S)=\mathrm{down}(T)\land \mathrm{up}(S)\ge \mathrm{up}(T)\Bigr).
$$

## 計算方法（実装ベース）

`rank` 列（弱順序）から、各プレイヤーの singleton `rank({i})` を取り出し、各 $|S|\ge2$ について

- `up(S)` = `rank(S) < rank({i})` を満たす `i∈S` の個数
- `down(S)` = `rank({i}) < rank(S)` を満たす `i∈S` の個数

を計算します。

出力では `score_du_up(S)=up(S)` と `score_du_down(S)=down(S)` の **(up,down) ベクトル**を併記します。

## 実装

- 主要実装: `src/gamegen/rules/updown.py`
- ランキング列への反映: `src/gamegen/commands/rankings.py`
