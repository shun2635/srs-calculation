# `rank_o-banzhaf`（序数的 Banzhaf による個人ランキング）

## 何をランキングするか

- 対象: **プレイヤー（個人）**
- 出力先: ランキング CSV の `rank_o-banzhaf` 列
  - **単独連合（singleton）行**のみ値が入り、それ以外の連合行は空欄になります（`gamegen/ranking/registry.py`）。

## 入力

- 各連合 $S$ の等級（弱順序）はゲーム CSV の `rank` 列（密順位、**1 が最上位**）。
  - このルールは `score` の値そのものではなく、**等級（順位情報）だけ**を使います。

## 計算方法

各プレイヤー $i$ について、全ての $S \subseteq N\setminus\{i\}$ を走査し、
「$i$ を追加したときに等級が上がる/下がる/変わらない」を数え上げます（`gamegen/rules/ordinal_banzhaf.py`）。

- 改善（上位化）:
  $$
    u_i^+ := |\{\, S \subseteq N\setminus\{i\} \mid k(S\cup\{i\}) < k(S) \,\}|
  $$
- 悪化（下位化）:
  $$
    u_i^- := |\{\, S \subseteq N\setminus\{i\} \mid k(S\cup\{i\}) > k(S) \,\}|
  $$
- 序数的 Banzhaf スコア:
  $$
    s_i := u_i^+ - u_i^-
  $$

ここで $k(S)$ は `rank` 列の値（小さいほど上位）です。

## ランク化（dense rank）

- $s_i$ の **降順**で並べ、同点は同順位の **dense rank**。
- タイブレーク（安定化）: インデックス昇順（player1, player2, ...）。

## 計算量（目安）

- $S$ の列挙が $2^n$、各 $S$ で $n$ 人を確認するため $O(n2^n)$。

## 実装

- 主要実装: `gamegen/rules/ordinal_banzhaf.py`
- ランキング列への反映（singleton 行のみ）: `gamegen/ranking/registry.py`

