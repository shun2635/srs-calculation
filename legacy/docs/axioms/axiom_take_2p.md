# Take 公理（2人版）

## 入力

各 `outputs/rankings/nN/game_*.csv` に対して、次を用いる。

- 基本の順序（弱順序）: `rank` 列（1 が最上位）
  - $A \succ B \iff \mathrm{rank}(A) < \mathrm{rank}(B)$
- 相互作用比較ルール: `rank_<rule>` 列（例: `rank_rp-index`）
  - $U\,P^I\,T \iff \mathrm{rank}_I(U) < \mathrm{rank}_I(T)$

## Take の定義（2人提携）

2人提携 $T$ に対し

$$
\\mathrm{take}(T) := \\bigl|\\{ i\\in T \\mid m_i^{T\\setminus\\{i\\}} = -1 \\}\\bigr|
$$

を用いる（実装: `gamegen/axioms/give_take.py`）。

## 制約がかかる比較（count: constraints）

任意の 2 人提携 $T,U$（$|T|=|U|=2$）について

$$
\\mathrm{take}(T) > \\mathrm{take}(U)
$$

が成り立つ **順序付き比較 $(T,U)$** を数える。

## 要求を満たす比較（count: satisfied）

上の条件を満たす比較 $(T,U)$ について

$$
U\,P^I\,T
$$

が成立した個数を数える。

## 出力

- 出力先: `outputs/axiom/nN/take-2p/<rule>.csv`
- 1行が 1ゲーム（1 CSV）
- 列: `game, constraints, satisfied, satisfied_rate`
