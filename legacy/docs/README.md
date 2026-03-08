# Docs

## 設計（`design/`）

- [README.md](design/README.md): 設計の目次
- [flow.md](design/flow.md): 処理フロー設計（1〜5）

## ランキング列（`rank_*`）の計算方法（`ranking/`）

個人ルールは **単独連合（singleton）行のみ**、グループ/連合ルールは **非空連合行** のみに値が入ります。

- [rank_shapley.md](ranking/rank_shapley.md): `rank_shapley`（Shapley）
- [rank_banzhaf.md](ranking/rank_banzhaf.md): `score_banzhaf` / `rank_banzhaf`（Banzhaf Value）
- [rank_lexcel.md](ranking/rank_lexcel.md): `rank_lexcel`（Lex-cel）
- [rank_o-banzhaf.md](ranking/rank_o-banzhaf.md): `rank_o-banzhaf`（序数的 Banzhaf）
- [rank_g-shapley.md](ranking/rank_g-shapley.md): `score_g-shapley` / `rank_g-shapley`（Shapley group value）
- [rank_g-sum-shapley.md](ranking/rank_g-sum-shapley.md): `score_g-sum-shapley` / `rank_g-sum-shapley`（Sum of member Shapley values）
- [rank_shapley-interaction.md](ranking/rank_shapley-interaction.md): `score_shapley-interaction` / `rank_shapley-interaction`（Shapley Interaction Index）
- [rank_banzhaf-interaction.md](ranking/rank_banzhaf-interaction.md): `score_banzhaf-interaction` / `rank_banzhaf-interaction`（Banzhaf Interaction Index）
- [rank_rp-index.md](ranking/rank_rp-index.md): `score_rp-index` / `rank_rp-index`（RP Index Rule）
- [rank_ud.md](ranking/rank_ud.md): `score_ud_up` / `score_ud_down` / `rank_ud`（UD Rule）
- [rank_du.md](ranking/rank_du.md): `score_du_up` / `score_du_down` / `rank_du`（DU Rule）
- [rank_red-index.md](ranking/rank_red-index.md): `score_red-index` / `rank_red-index`（Red Index Rule）
- [rank_g-lexcel.md](ranking/rank_g-lexcel.md): `rank_g-lexcel`（Group Lex-cel）
- [rank_g-o-banzhaf.md](ranking/rank_g-o-banzhaf.md): `rank_g-o-banzhaf`（Group Ordinal Banzhaf）

## 公理チェック（`axioms/`）

- [README.md](axioms/README.md): 公理チェック（制約数/満足数の集計）とテンプレ
