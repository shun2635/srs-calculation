# 冗長性公理（Redundancy）

## 入力

各 `outputs/rankings/nN/game_*.csv` に対して、次を用いる。

- 基本の弱順序: `rank` 列（1 が最上位）
  - $A \succsim B \iff \mathrm{rank}(A) \le \mathrm{rank}(B)$
- 相互作用比較ルール: `rank_<rule>` 列（例: `rank_red-index`）
  - $A \,R^I\, B \iff \mathrm{rank}_I(A) \le \mathrm{rank}_I(B)$

## 公理（定義）

任意の $S\subseteq N$ と $i\in N\setminus S$ について

$$
S\succsim S\cup\{i\}
\ \Longrightarrow\
S\;R^{I}_{\succsim}\;(S\cup\{i\}).
$$

## 制約がかかる比較（count: constraints）

比較ペアを $(S,\,S\cup\{i\})$ とし、前提

$$
\mathrm{rank}(S) \le \mathrm{rank}(S\cup\{i\})
$$

が成り立つものの個数を数える。

※ 実装では、`rank_<rule>` が **両方の提携で定義されている場合のみ**この比較を数える
（ルールの定義域外の比較はカウントしない）。

## 要求を満たす比較（count: satisfied）

上の前提が成り立つ比較について

$$
\mathrm{rank}_I(S) \le \mathrm{rank}_I(S\cup\{i\})
$$

が成立した個数を数える。

## 出力

- 出力先: `outputs/axiom/nN/redundancy/<rule>.csv`
- 1行が 1ゲーム（1 CSV）
- 列: `game, constraints, satisfied, satisfied_rate`
- 違反例: `outputs/axiom/nN/redundancy/examples/<rule>/*.png`（最大3）

