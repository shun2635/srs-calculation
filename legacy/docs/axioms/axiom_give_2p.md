# Give 公理（2人版）

## 入力

各 `outputs/rankings/nN/game_*.csv` に対して、次を用いる。

- 基本の順序（弱順序）: `rank` 列（1 が最上位）
  - $A \succ B \iff \mathrm{rank}(A) < \mathrm{rank}(B)$
- 相互作用比較ルール: `rank_<rule>` 列（例: `rank_rp-index`）
  - $T\,P^I\,U \iff \mathrm{rank}_I(T) < \mathrm{rank}_I(U)$

## Ordinal marginal contribution（実装上の扱い）

プレイヤー $i\notin S$ に対し、$S\cup\{i\}$ と $S$ の順位比較から

$$
m_i^S :=
\begin{cases}
1 & \text{if } S\cup\{i\} \succ S \\
-1 & \text{if } S \succ S\cup\{i\} \\
0 & \text{otherwise}
\end{cases}
$$

を定義する（同順位は 0）。

2人提携 $T=\{a,b\}$ については $S=T\\setminus\\{i\\}$ は単独連合になるため、
`rank` 列だけで各メンバーの $m_i^{T\\setminus\\{i\\}}$ が決まる。

## Give の定義（2人提携）

2人提携 $T$ に対し

$$
\\mathrm{give}(T) := \\bigl|\\{ i\\in T \\mid m_i^{T\\setminus\\{i\\}} = 1 \\}\\bigr|
$$

を用いる（実装: `gamegen/axioms/give_take.py`）。

## 制約がかかる比較（count: constraints）

任意の 2 人提携 $T,U$（$|T|=|U|=2$）について

$$
\\mathrm{give}(T) > \\mathrm{give}(U)
$$

が成り立つ **順序付き比較 $(T,U)$** を数える。

## 要求を満たす比較（count: satisfied）

上の条件を満たす比較 $(T,U)$ について

$$
T\,P^I\,U
$$

が成立した個数を数える。

## 出力

- 出力先: `outputs/axiom/nN/give-2p/<rule>.csv`
- 1行が 1ゲーム（1 CSV）
- 列: `game, constraints, satisfied, satisfied_rate`
