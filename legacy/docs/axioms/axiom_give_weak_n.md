# Give 公理（弱い n 人版拡張）

## 入力

各 `outputs/rankings/nN/game_*.csv` に対して、次を用いる。

- 基本の順序（弱順序）: `rank` 列（1 が最上位）
  - $A \succ B \iff \mathrm{rank}(A) < \mathrm{rank}(B)$
- 相互作用比較ルール: `rank_<rule>` 列（例: `rank_rp-index`）
  - $S\,P^I\,T \iff \mathrm{rank}_I(S) < \mathrm{rank}_I(T)$

## Give/Take Count（弱い n 人版）

任意の非空な提携 $T\\subseteq N$ に対して

$$
\\mathrm{give}(T) := |\\{ i\\in T \\mid T \\succ \\{i\\} \\}|
$$

を用いる（同順位は除外）。

## 制約がかかる比較（count: constraints）

同じ人数の提携 $S,T$（$|S|=|T|$）について

$$
\\mathrm{give}(S) > \\mathrm{give}(T)
$$

が成り立つ **順序付き比較 $(S,T)$** を数える。

実装では `--min-coalition-size` 以上のすべての提携サイズについて合算する
（`gamegen/axioms/give_take.py`）。

## 要求を満たす比較（count: satisfied）

上の条件を満たす比較 $(S,T)$ について

$$
S\\,P^I\\,T
$$

が成立した個数を数える。

## 出力

- 出力先: `outputs/axiom/nN/give-weak-n/<rule>.csv`
- 1行が 1ゲーム（1 CSV）
- 列: `game, constraints, satisfied, satisfied_rate`

