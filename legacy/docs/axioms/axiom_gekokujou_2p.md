# 下剋上公理（2人版）

## 目的

「単独では弱い側が、組むことで逆転する」状況を、相互作用比較ルールが適切に評価できているかをチェックする。

## 入力

各 `outputs/rankings/nN/game_*.csv` に対して、次を用いる。

- 基本の弱順序: `rank` 列（1 が最上位）
  - $A \succsim B \iff \mathrm{rank}(A) \le \mathrm{rank}(B)$
  - $A \succ B \iff \mathrm{rank}(A) < \mathrm{rank}(B)$
- 相互作用比較ルール: `rank_<rule>` 列（例: `rank_rp-index`）
  - $T\,P^I\,S \iff \mathrm{rank}_{I}(T) < \mathrm{rank}_{I}(S)$

## 制約がかかる比較（count: constraints）

2人提携 $S,T \subseteq N$（$|S|=|T|=2$）について、

$$
\exists \pi \in S_2:\;
\Bigl(
   \{s_1\}\succsim \{t_{\pi(1)}\}
   \land
   \{s_2\}\succsim \{t_{\pi(2)}\}
   \land
   S\precsim T
\Bigr)
\land
\Bigl(
   \{s_1\}\succ \{t_{\pi(1)}\}
   \lor
   \{s_2\}\succ \{t_{\pi(2)}\}
   \lor
   S\prec T
\Bigr)
$$

が成り立つ **順序付き比較 $(S,T)$** を「制約がかかる比較」として数える。

実装では、単独連合の順位（`rank`）の多重集合の比較により、上の存在量化（$\exists\pi$）を判定する
（`gamegen/axioms/gekokujou.py`）。

## 要求を満たす比較（count: satisfied）

上の条件を満たす比較 $(S,T)$ について

$$
T\,P^I\,S
$$

が成立した個数を数える。

## 出力

`check-axioms` は、各ゲーム（CSV）について `constraints` と `satisfied` を出力する。

- 出力先: `outputs/axiom/nN/gekokujou-2p/<rule>.csv`
- 1行が 1ゲーム（1 CSV）
- 列: `game, constraints, satisfied, satisfied_rate`

## 実装

- CLI: `gamegen/commands/axioms.py`
- ロジック: `gamegen/axioms/gekokujou.py`
