# 公理チェック（`docs/axioms/`）

## 現状

現行コードには **公理チェック（制約数/満足数の集計）機能**があります。

- CLI: `poetry run game-gen check-axioms -p N`
- 入力: `outputs/rankings/nN/game_*.csv`
- 出力: `outputs/axiom/nN/`
  - `outputs/axiom/nN/<axiom_id>/<rule>.csv`（各ゲーム1行の `satisfied_rate` 付き）
  - `outputs/axiom/nN/<axiom_id>/examples/<rule>/*.png`（違反例、最大3）
  - `outputs/axiom/nN/summary.csv`（ルール×公理の合計）

さらに、集計済み CSV（`outputs/axiom/nN/*.csv`）を入力として、サイズごとの summary を作成できます。

- CLI: `poetry run game-gen summarize-axioms -p N`
- 入力: `outputs/axiom/nN/<axiom_id>/<rule>.csv`
- 出力: `outputs/axiom/nN/summary.csv`（列: `rule, axiom, constraints, satisfied, satisfied_rate`）

※ `check-axioms` 実行時にも `summary.csv` を自動生成します（既存の counts CSV を集計）。

※ `pipeline` は最後に `check-axioms` 相当の処理を実行します（適用済みのルールのうち、公理チェック対象に該当するものだけ）。

## 可視化（summary heatmap）

`outputs/axiom/nN/summary.csv` を「縦=ルール、横=公理、値=適合率」としてヒートマップ化できます。

- CLI: `poetry run game-gen axiom-summary-heatmap -p N`
- 出力: `outputs/axiom/nN/summary_heatmap.png`

そのためこのフォルダは、将来「公理チェック」を復活・追加するときに、
**公理（ルール）ごとにロジック設計書を分割**して管理するための置き場として用意します。

## 設計書の分割方針

- 公理ごとに 1 ファイル（例: `axiom_swimmy_2p.md`）
- すべての公理に共通する I/O・欠損値方針は `axiom_common.md` にまとめる

## 実装済みの公理

- [axiom_gekokujou_2p.md](axiom_gekokujou_2p.md): 下剋上公理（2人版）
- [axiom_gekokujou_weak_n.md](axiom_gekokujou_weak_n.md): 下剋上公理（弱い n 人版拡張）
- [axiom_give_2p.md](axiom_give_2p.md): Give 公理（2人版）
- [axiom_take_2p.md](axiom_take_2p.md): Take 公理（2人版）
- [axiom_give_weak_n.md](axiom_give_weak_n.md): Give 公理（弱い n 人版拡張）
- [axiom_take_weak_n.md](axiom_take_weak_n.md): Take 公理（弱い n 人版拡張）
- [axiom_redundancy.md](axiom_redundancy.md): 冗長性公理（Redundancy）

## テンプレ

- [axiom_common_template.md](axiom_common_template.md): 公理チェック共通テンプレ
- [axiom_rule_template.md](axiom_rule_template.md): 公理（ルール）別テンプレ
