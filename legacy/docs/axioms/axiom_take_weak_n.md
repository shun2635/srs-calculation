# Take 公理（弱い n 人版拡張）

## 入力

各 `outputs/rankings/nN/game_*.csv` に対して、次を用いる。

- 基本の順序（弱順序）: `rank` 列（1 が最上位）
  - $A \succ B \iff \mathrm{rank}(A) < \mathrm{rank}(B)$
- 相互作用比較ルール: `rank_<rule>` 列（例: `rank_ud`）
  - $T\\,P^I\\,S \iff \mathrm{rank}_I(T) < \mathrm{rank}_I(S)$

## Give/Take Count（弱い n 人版）

任意の非空な提携 $T\\subseteq N$ に対して

$$
\\mathrm{take}(T) := |\\{ i\\in T \\mid \\{i\\} \\succ T \\}|
$$

を用いる（同順位は除外）。

## 制約がかかる比較（count: constraints）

同じ人数の提携 $S,T$（$|S|=|T|$）について

$$
\\mathrm{take}(S) > \\mathrm{take}(T)
$$

が成り立つ **順序付き比較 $(S,T)$** を数える。

実装では `--min-coalition-size` 以上のすべての提携サイズについて合算する。

## 要求を満たす比較（count: satisfied）

上の条件を満たす比較 $(S,T)$ について

$$
T\\,P^I\\,S
$$

が成立した個数を数える。

## 出力

- 出力先: `outputs/axiom/nN/take-weak-n/<rule>.csv`
- 1行が 1ゲーム（1 CSV）
- 列: `game, constraints, satisfied, satisfied_rate`
