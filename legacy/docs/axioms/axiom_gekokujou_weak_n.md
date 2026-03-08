# 下剋上公理（弱い n 人版拡張）

## 目的

2人版を一般化し、同じ人数の提携同士の比較において
「個は弱いが、組むことで逆転する」状況を相互作用比較ルールが適切に反映するかをチェックする。

## 入力

各 `outputs/rankings/nN/game_*.csv` に対して、次を用いる。

- 基本の弱順序: `rank` 列（1 が最上位）
- 相互作用比較ルール: `rank_<rule>` 列（例: `rank_ud`）

## 制約がかかる比較（count: constraints）

任意の $S,T \subseteq N$（$|S|=|T|=n$）について

$$
\exists\,\pi\in S_n:\;
\Bigl(
   \forall i:\;
   \{s_i\}\succsim \{t_{\pi(i)}\}
   \land
   S\precsim T
\Bigr)
\land
\Bigl(
   \exists i:\;
   \{s_i\}\succ \{t_{\pi(i)}\}
   \lor
   S\prec T
\Bigr)
$$

が成り立つ **順序付き比較 $(S,T)$** を「制約がかかる比較」として数える。

実装では、比較対象の提携サイズを固定せず、
`--min-coalition-size` 以上のすべてのサイズについて **合算**する（`check-axioms` の仕様）。

## 要求を満たす比較（count: satisfied）

上の条件を満たす比較 $(S,T)$ について

$$
T\,P^I\,S
$$

が成立した個数を数える。

## 出力

- 出力先: `outputs/axiom/nN/gekokujou-weak-n/<rule>.csv`
- 1行が 1ゲーム（1 CSV）
- 列: `game, constraints, satisfied, satisfied_rate`

## 実装

- CLI: `gamegen/commands/axioms.py`
- ロジック: `gamegen/axioms/gekokujou.py`
