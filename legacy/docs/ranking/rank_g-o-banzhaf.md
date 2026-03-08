# `rank_g-o-banzhaf`（Group Ordinal Banzhaf による連合ランキング）

## 何をランキングするか

- 対象: **連合（coalition）**
- 出力先: ランキング CSV の `rank_g-o-banzhaf` 列
  - **非空連合**のみ値が入り、空集合は空欄になります（`gamegen/ranking/registry.py`）。

## 入力

- 連合の等級（弱順序）はゲーム CSV の `rank` 列（密順位、**1 が最上位**）。
  - `score` の大きさではなく **等級だけ**を使います。

## 計算方法

各非空連合 $T\neq\emptyset$ について、土台 $S$ を $N \setminus T$ の部分集合として動かし、
「$T$ を加えたときに等級が上がる/下がる/変わらない」を数え上げます（`gamegen/rules/group_ordinal_banzhaf.py`）。

- 改善（上位化）:
  $$
    u_T^+ := |\{\, S \subseteq N \setminus T \mid k(S\cup T) < k(S) \,\}|
  $$
- 悪化（下位化）:
  $$
    u_T^- := |\{\, S \subseteq N \setminus T \mid k(S\cup T) > k(S) \,\}|
  $$
- Group Ordinal Banzhaf スコア:
  $$
    s_T := u_T^+ - u_T^-
  $$

ここで $k(\cdot)$ は `rank` 列の値（小さいほど上位）です。

## ランク化（dense rank）

- $s_T$ の **降順**で並べ、同点は同順位の **dense rank**。
- タイブレーク（安定化）: `mask` 昇順（実装上の安定化）。

## 計算量（目安）

- 各 $T$ について $S \subseteq N \setminus T$ を列挙するため、理論上 $O(3^n)$。

## 実装

- 主要実装: `gamegen/rules/group_ordinal_banzhaf.py`
- ランキング列への反映（非空連合のみ）: `gamegen/ranking/registry.py`
