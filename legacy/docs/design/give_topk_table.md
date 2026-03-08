# Give（引き上げ）上位提携表（real-gen）

## 目的

Give 公理で使う `give(T)`（「提携 T がメンバーをどれだけ引き上げるか」）を、
提携ごとに数値化して上位提携を一覧できるようにする。

## 入力

- 入力ランキング CSV: `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv`
  - 必須列:
    - `player1..playerN`（0/1）
    - `rank`（1 が最上位）

## 定義（Give / 引き上げ数）

非空提携 `T` について

- `give(T) := |{ i ∈ T | rank(T) < rank({i}) }|`

（同順位は引き上げに数えない）

## 出力

- 出力先: `outputs/real/<dataset_id>/figures/give_top10.png`

## 表仕様

- 対象: `|T|>=2` の提携（singleton は常に give=0 のため除外）
- 並び順: `give(T)` 降順、同値は提携 bitmask 昇順で安定化
- 列:
  - `予測因子の組`
  - `引き上げ数(give)`
  - `提携サイズ`

## pipeline への組み込み

- `real-gen make-figures <dataset_id>` 実行時に best-effort で生成する

