# Paper Simulation Repository Audit

調査日: 2026-05-01  
対象 commit: `82264e6`

## 0. この文書の目的

この文書は、AAMAS向け論文の Simulation Analysis に用いるために、現在のsimulationリポジトリの構成、実装済み機能、未実装機能、出力物、論文側定義との対応を整理するものである。

## 1. リポジトリ概要

| パス | 種別 | 役割 | 現在の状態 | 論文Simulationとの関係 | 備考 |
| --- | --- | --- | --- | --- | --- |
| `README.md` | ドキュメント | root CLI、`src/` と `legacy/` の位置付け、実行例を説明 | 存在する | 実験実行導線の入口 | 一部の出力パス説明は現在のテスト期待値とずれがある。現行コードは `outputs/synthetic/<constraint>/...` を使う |
| `docs/` | ドキュメント | 研究ワークフロー、architecture、spec、ADR | 存在する | methodology と再現性の説明に利用可能 | `docs/ja/specs/synthetic-game-methodology.md` に旧 flat path の記述が残る |
| `scripts/` | スクリプト | 補助スクリプト置き場想定 | 存在しない | 直接関係なし | 実験実行は Poetry CLI 経由 |
| `src/` | 実装 | 現行サポート対象の実装本体 | 存在する | 主に使うべき実装 | `srs_calculation` パッケージ |
| `notebooks/` | notebook | 分析 notebook 置き場想定 | 存在しない | 現状は論文図表作成には使われていない | `.ipynb` も見つからない |
| `data/` | データ | データ置き場想定 | 存在しない | 直接関係なし | 実データ入力は `legacy/inputs/feature_mask_tables/` |
| `figures/` | 図表 | 論文用図表置き場想定 | 存在しない | 必要な最終図表置き場としては未整備 | 生成図は `outputs/` または `legacy/outputs/` 配下 |
| `results/` | 結果 | 論文用CSV置き場想定 | 存在しない | 必要な summary CSV 置き場としては未整備 | 現行 canonical layout では `outputs/synthetic/.../analysis/` |
| `outputs/` | 生成物 | root/過去実行の synthetic 出力 | 存在するが `.gitignore` 対象 | 既存CSV/PNGの参考 | `games/n3,n4,n5,n8`、`rankings/n3,n4`、`heatmaps/n3,n4` がある。現行 canonical path ではない |
| `legacy/` | archive | 旧 `gamegen` / `realgen` 実装、詳細数理docs、旧出力 | 存在する | 数理定義・旧出力確認に有用 | 通常の実行面では archive 扱い |
| `legacy/outputs/` | 生成物 | 旧 workflow の CSV/PNG/axiom summary | 存在するが `.gitignore` 対象 | 既存結果の参考 | 論文主分析に使うには実行条件・seed・現行定義との差分確認が必要 |
| `tests/` | テスト | unit/integration/e2e/parity | 存在する | 実装確認に重要 | rule registry、axiom registry、synthetic workflow、CSV出力をテスト |
| `config` | 設定 | root config 置き場想定 | root には存在しない | 再現性設定は未整備 | `legacy/config.yaml` と `legacy/config/labels.yaml` は存在するが root CLI は暗黙に読まない |
| `Makefile` / task runner | task runner | 実験・テストの短縮コマンド | 存在しない | 実行手順の標準化は未整備 | Poetry scripts を使う |
| `pyproject.toml` | dependency / CLI | Python依存、Poetry scripts | 存在する | 実行環境の正本 | 依存は `click`, `pyyaml`, `pandas`, `matplotlib`。dev は `pytest`, `ruff`, `mypy` |
| `poetry.lock` | dependency lock | 依存バージョン固定 | 存在する | 再現性に必要 | root 用 |
| `requirements.txt` | dependency | pip形式依存 | 存在しない | 直接関係なし | Poetry 使用 |
| `environment.yml` | dependency | conda環境 | 存在しない | 直接関係なし | Poetry 使用 |

## 2. 実装済みrule

| rule | 実装ファイル | 関数名 / クラス名 | 入力形式 | 出力形式 | 論文定義との一致度 | 差異・要確認点 | テストの有無 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Group Lex-cel | `src/srs_calculation/domain/ranking/rules/group_lexcel.py` | `GroupLexcelRule.evaluate` | complete `CoalitionGame`、`base_ranks_by_mask` | `RankingResult.rank_set`、coalition scope、`rank_g-lexcel` | 高い | 全非空coalitionに rank を出す。論文主分析で同サイズ `X_k` に制限する集計は別途必要 | registry/integrationあり。旧 `legacy/tests/test_group_lexcel.py` に詳細あり |
| RP-Difference | `src/srs_calculation/domain/ranking/rules/rp_index.py` | `RpIndexRule.evaluate` | complete `CoalitionGame`、`base_ranks_by_mask` | `score_rp-index`, `rank_rp-index`、`|S|>=2` の coalitionのみ | 高い | 実装名は `rp_index` / `RP Index`。論文名は RP-Difference に寄せる必要あり。singleton rank は出力しない | integrationあり。旧 docs と実装あり |
| UD | `src/srs_calculation/domain/ranking/rules/updown.py` | `UdRule.evaluate` | complete `CoalitionGame` | `score_ud_up`, `score_ud_down`, `rank_ud` | 論文主分析外 | singleton比較に基づく up/down count | registry/integrationあり |
| DU | `src/srs_calculation/domain/ranking/rules/updown.py` | `DuRule.evaluate` | complete `CoalitionGame` | `score_du_up`, `score_du_down`, `rank_du` | 論文主分析外 | UDと同じ count を別スコア化 | registry/integrationあり |
| Red | `src/srs_calculation/domain/ranking/rules/red_index.py` | `RedIndexRule.evaluate` | complete `CoalitionGame` | `score_red-index`, `rank_red-index` | 論文主分析外 | `coalition_rank <= superset_rank` を数える | registry/integrationあり |
| Group Ordinal Banzhaf | `src/srs_calculation/domain/ranking/rules/group_ordinal_banzhaf.py` | `GroupOrdinalBanzhafRule.evaluate` | complete `CoalitionGame` | `rank_g-o-banzhaf` | 論文主分析外 | score は domain では持つが compatibility CSV は rank中心 | registry/integrationあり |
| Shapley | `src/srs_calculation/domain/ranking/rules/shapley.py` | `ShapleyRule.evaluate` | complete `CoalitionGame`、score | player score/rank | 論文主分析外 | cardinal rule | parityあり |
| Banzhaf | `src/srs_calculation/domain/ranking/rules/banzhaf.py` | `BanzhafRule.evaluate` | complete `CoalitionGame`、score | player score/rank | 論文主分析外 | cardinal rule | parityあり |
| Lex-cel | `src/srs_calculation/domain/ranking/rules/lexcel.py` | `LexcelRule.evaluate` | complete `CoalitionGame` | player rank | 論文主分析外 | player-level Lex-cel | parityあり |
| Ordinal Banzhaf | `src/srs_calculation/domain/ranking/rules/ordinal_banzhaf.py` | `OrdinalBanzhafRule.evaluate` | complete `CoalitionGame` | player score/rank | 論文主分析外 | ordinal player rule | parityあり |
| Group Shapley | `src/srs_calculation/domain/ranking/rules/group_shapley.py` | `GroupShapleyRule.evaluate` | complete `CoalitionGame`、score | coalition score/rank | 論文主分析外 | cardinal group value | integrationあり |
| Group Sum Shapley | `src/srs_calculation/domain/ranking/rules/group_sum_shapley.py` | `GroupSumShapleyRule.evaluate` | complete `CoalitionGame`、score | coalition score/rank | 論文主分析外 | member Shapley sum | integrationあり |
| Shapley Interaction | `src/srs_calculation/domain/ranking/rules/shapley_interaction.py` | `ShapleyInteractionRule.evaluate` | complete `CoalitionGame`、score | coalition score/rank | 論文主分析外 | interaction index | integrationあり |
| Banzhaf Interaction | `src/srs_calculation/domain/ranking/rules/banzhaf_interaction.py` | `BanzhafInteractionRule.evaluate` | complete `CoalitionGame`、score | coalition score/rank | 論文主分析外 | interaction index | integrationあり |

## 3. 実装済みlens / axiom

| lens / axiom | 実装ファイル | 関数名 / クラス名 | 制約集合の生成方法 | 厳密比較 / 弱比較 / tie の扱い | 論文定義との一致度 | 差異・要確認点 | テストの有無 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Reversal lens | `src/srs_calculation/domain/axioms/evaluators/reversal.py` | `Reversal2pAxiom`, `ReversalWeakNAxiom` | 同サイズcoalition pairを走査。singleton rank multiset の sorted dominance で bijection 存在を判定 | baseは `rank` 小さいほど良い。制約満足は output rank の厳密比較 `rank_T < rank_S`。tie は満足しない | 高い | singleton側の厳密差を必須にする論文定義版 | registry/integrationあり |
| Up lens | exact name なし | 関連: `Give2pAxiom`, `GiveWeakNAxiom` | give count が大きい方を上位要求 | `measure_left > measure_right` のとき厳密 rank 比較を要求 | 要確認 | 「Up lens」という名前では存在しない。Give axiom が近い可能性 | registry/integrationあり |
| Down lens | exact name なし | 関連: `Take2pAxiom`, `TakeWeakNAxiom` | take count が大きい方を下位要求 | 厳密 rank 比較を要求 | 要確認 | 「Down lens」という名前では存在しない。Take axiom が近い可能性 | registry/integrationあり |
| Redundancy lens | `src/srs_calculation/domain/axioms/evaluators/redundancy.py` | `RedundancyAxiom.evaluate` | `S` と1要素追加superset `T` を走査し、base `rank(S) <= rank(T)` なら制約 | 満足は `interaction_rank_s <= interaction_rank_t` なので弱比較 | 論文主分析外 | Reversalとは別。tieを満足扱いにする | registry/integrationあり |
| その他 | `src/srs_calculation/domain/axioms/registry.py` | `build_default_axiom_registry` | `reversal-2p`, `reversal-weak-n`, `give-2p`, `take-2p`, `give-weak-n`, `take-weak-n`, `redundancy` | axiomごとに異なる | 論文主分析外 | individual scope は導線だけで具体axiomなし | registry testあり |

重要な確認点:

- 論文側の Reversal lens は `H \succ G` を厳密要求する方針であり、実装の満足判定も厳密比較である。
- active実装では旧定義を使わず、singleton側の厳密差を必須にする Reversal 定義へ置換する。
- `AxiomEvaluationResult.satisfaction_ratio` は制約数0のとき `1.0` を返すが、synthetic summary では per-game rate に `"0"` を書き、aggregateでは total constraints が0なら `"0"` を書く。論文方針の「制約集合が空なら平均から除外」とは異なる。

## 4. 入力生成・weak order変換

| 項目 | 現在の実装 |
| --- | --- |
| `n` の設定 | CLI `srs-game-gen gen-games -p/--players`。範囲は `1 <= n <= 12` |
| `R` の設定 | 論文でいう反復回数に相当するものは `--count/-c`。デフォルトは config または `1` |
| seed の扱い | `--seed` または `gen_games.seed`。`random.Random(seed)` を1つ作り、複数gameで連続消費する |
| coalition value 生成方法 | unconstrained では各 `mask in range(2^n)` に `rng.randint(0, max_score)` を独立に付与 |
| tie の発生方法 | 整数 score の同値により自然発生。tie は dense rank の同順位クラスとして保持 |
| weak order / rank class 変換 | `CoalitionGame._dense_base_ranks` と CSV writer が score 降順、同点同rankで dense rank を作る |
| coalition size monotonicity | unconstrained では仮定しない。`--constraint monotone` や `--profile tu` を明示した場合だけ単調性を満たす生成になる |
| `X=2^N\setminus{\emptyset}` | rule/lens内部では多くが非空coalitionを対象にする。CSV game自体は空集合も含む complete table |
| singleton | complete game 生成なので singleton は必ず含まれる |
| 出力パス | 現行コード・テストの canonical path は `outputs/synthetic/<constraint_set_id>/games/nN/` など |

注意:

- `src/srs_calculation/application/game_generation/generate_synthetic_games.py` は unconstrained なら空集合もランダム値を持たせる。
- `CoalitionGame.require_complete()` を各 rule が呼ぶため、論文主分析の synthetic 入力は complete table が前提になる。
- `docs/ja/specs/synthetic-game-methodology.md` は旧 flat path `outputs/games/nN` を記述しているが、現在の e2e test は `outputs/synthetic/unconstrained/games/nN` を期待している。

## 5. Metrics 実装

### 5.1 Lens consistency rate

| 項目 | 現在の状態 |
| --- | --- |
| 実装の有無 | あり。ただし名前は lens consistency ではなく axiom satisfaction |
| 対応lens | `reversal-2p`, `reversal-weak-n`, `give-*`, `take-*`, `redundancy` |
| 対応rule | coalition-scoped rankを持つ全rule。`rp_index` も対象 |
| 制約集合が空の場合 | per-game CSVでは `"0"`、summaryも total constraints が0なら `"0"`。domain property は `1.0` |
| 厳密比較の扱い | `reversal` は output rank の厳密比較を要求 |
| tie の扱い | `reversal` では output tie は不満足。`redundancy` は弱比較なので tie 満足 |
| 出力形式 | `analysis/nN/axiom/coalition/<axiom_id>/<rule>.csv` と `summary.csv`、`summary_heatmap.png` |
| 論文定義との一致度 | Reversal lensについては要修正または要説明。空制約除外も未実装 |

不足:

- 論文名 `Reversal lens consistency rate for RP-Difference` に絞った CSV/figure は未作成。
- 空制約入力を平均から除外する集計は未実装。
- Reversal lens の制約生成が論文定義と完全一致するかを検証するテストが不足。

### 5.2 Rank correlation

| 項目 | 現在の状態 |
| --- | --- |
| 実装の有無 | あり。ただし full rule correlation heatmap として実装 |
| 対応rule pair | scope内の全 rank column。`rank_g-lexcel` と `rank_rp-index` も含められる |
| 同サイズ集合 `X_k` ごとの計算 | 未実装。現行 coalition-scope は非空coalition全体を縦結合 |
| tie の rank 処理 | serialized rank を `effective_rank = 1 + strictly better count` に変換。average rank ではない |
| Spearman correlation | `pandas.DataFrame.corr(method="spearman", min_periods=1)` |
| constant vector / NA の扱い | pandas に依存し、NaN が出る。除外集計ロジックは未整備 |
| 出力形式 | `rule_corr_player.csv`, `rule_corr_coalition.csv`, 対応PNG |
| 論文定義との一致度 | 部分一致。論文方針の「同サイズ `X_k` ごと」「tie は average rank」「NA除外」は未実装 |

不足:

- Group Lex-cel と RP-Difference に絞った per-game/per-size Spearman summary CSV がない。
- 論文用の rank correlation 平均値・分散・信頼区間などの要約がない。

## 6. 既存出力物

| ファイルパス | 生成元スクリプト | 内容 | 論文に使えるか | 再生成可能か | 備考 |
| --- | --- | --- | --- | --- | --- |
| `outputs/games/n3/*.csv` | 旧または過去の root synthetic | n=3 game CSV 100件 | 条件確認後なら参考 | おそらく可能 | 現行 canonical path ではない |
| `outputs/games/n4/*.csv` | 同上 | n=4 game CSV 100件 | 条件確認後なら参考 | おそらく可能 |  |
| `outputs/games/n5/*.csv` | 同上 | n=5 game CSV 100件 | 条件確認後なら参考 | おそらく可能 | rankings は見つからない |
| `outputs/games/n8/*.csv` | 同上 | n=8 game CSV 100件 | 条件確認後なら参考 | おそらく可能 | rankings は見つからない |
| `outputs/rankings/n3/*.csv` | 旧または過去の root apply-rules | n=3 rankings CSV 100件 | 参考可 | 可能 | 全rule列あり |
| `outputs/rankings/n4/*.csv` | 同上 | n=4 rankings CSV 100件 | 参考可 | 可能 | 全rule列あり |
| `outputs/heatmaps/n3/*.png` | 旧または過去の heatmap | `rank_lexcel_vs_rank_shapley.png`, `rule_corr_*.png` | 主分析には不足 | 可能 | GLC vs RP 専用ではない |
| `outputs/heatmaps/n4/*.png` | 同上 | n=4 heatmap PNG | 主分析には不足 | 可能 |  |
| `legacy/outputs/axiom/n{3,4,5,10}/summary.csv` | legacy `check-axioms` / summary | axiom satisfaction summary | 定義確認後なら参考 | legacyで可能 | Reversal相当は `gekokujou-*` |
| `legacy/outputs/axiom/n*/gekokujou-weak-n/rp-index.csv` | legacy axiom workflow | per-game RP Index gekokujou counts | Reversalとの差分確認が必要 | legacyで可能 | 既存値を本文に使うには条件確認が必要 |
| `legacy/outputs/axiom/n*/summary_heatmap.png` | legacy summary heatmap | axiom satisfaction heatmap | 参考 | legacyで可能 | 論文主分析の最小図とは異なる |
| `legacy/outputs/heatmaps/n*/rule_corr_coalition.png` | legacy heatmap | coalition rule correlation | 参考 | legacyで可能 | CSV summary は見つからない |
| `legacy/outputs/figures/n*/*.png` | legacy figure command | game別 ranking table PNG | 主分析には不向き | legacyで可能 | 個別確認用 |
| `legacy/outputs/real/*` | real-gen | 実データ結果 | 今回のSimulation主分析外 | 可能 | wine/covid19等 |

存在しないもの:

- `results/simulation_summary.csv`
- `results/lens_consistency.csv`
- `results/rank_correlation.csv`
- `figures/reversal_consistency.pdf`
- `figures/rank_correlation_glc_rp.pdf`
- `docs/simulation_result_summary.md`
- 現行 canonical `outputs/synthetic/.../analysis/` の既存ファイル

## 7. 論文主分析に必要な最小実装との差分

| 必要項目 | 実装済みか | 既存ファイル | 不足点 | 優先度 | 次に必要な作業 |
| --- | --- | --- | --- | --- | --- |
| Group Lex-cel rule | はい | `src/.../group_lexcel.py` | 同サイズ `X_k` の論文用集計 | 高 | rule outputをsize別に集計する |
| RP-Difference rule | はい | `src/.../rp_index.py` | 名前整理、singleton除外範囲の明示 | 高 | 論文では `RP-Difference` として列名/表示名を整理 |
| Reversal lens | はい | `src/.../reversal.py` | paper simulation 用の集計と図表が必要 | 最高 | Reversal consistency と一体で検証する |
| RP-Difference の Reversal consistency | 部分的 | `evaluate_synthetic_axioms`, `synthetic_reports.py` | 空制約除外、RP専用summary、論文用CSVなし | 最高 | `rp_index` x Reversal の per-game/per-size CSVを出力 |
| Group Lex-cel と RP-Difference の rank correlation | 部分的 | `synthetic_rank_heatmap.py` | `X_k` ごと、average rank tie、NA除外が未実装 | 最高 | 論文定義版 correlation metric を実装 |
| summary CSV | 部分的 | axiom summary / rule corr matrix | 論文主分析用の縦持ち summary がない | 高 | `results/simulation_summary.csv` 相当を生成 |
| lens consistency figure | 部分的 | axiom summary heatmap | Reversal x RP 専用ではない | 高 | bar/heatmap を生成 |
| rank correlation figure | 部分的 | rule_corr_coalition.png | GLC vs RP, size別ではない | 高 | `rank_correlation_glc_rp` 図を生成 |
| 論文本文に入れる数値要約 | いいえ | なし | 数値集計未実施 | 高 | 実験実行後に markdown/json summary を生成 |

## 8. 論文へ取り込むべき図表候補

| 図表名 | 目的 | 入力データ | 出力ファイル候補 | 本文向け / appendix向け | 未実装事項 |
| --- | --- | --- | --- | --- | --- |
| Reversal consistency of RP-Difference | RQ2: RP-Difference が Reversal 制約をどの程度満たすか | Reversal constraint counts for `rp_index` | `figures/reversal_consistency.pdf`, `.png` | 本文向け | 論文定義版 Reversal、空制約除外、summary CSV |
| GLC vs RP rank correlation | RQ1: Group Lex-cel と RP-Difference の差を見る | size別 rank vectors | `figures/rank_correlation_glc_rp.pdf`, `.png` | 本文向け | `X_k` ごと、average rank tie、NA除外 |
| Full coalition rule correlation heatmap | 他ruleとの相対的位置付け | `rule_corr_coalition.csv` | `figures/rule_corr_coalition_appendix.pdf` | appendix向け | 現行PNGはあるがPDF/論文用整形は未実装 |
| Reversal constraints by `n,k` heatmap | 制約の発生量と安定性確認 | per-game/per-size constraints | `figures/reversal_constraint_counts.pdf` | appendix向け | size別 constraint count CSV |
| Robustness by constraint profile | unconstrained vs TU などの比較 | constraint-set別 summary | `figures/robustness_constraint_profiles.pdf` | appendix向け | 大規模実験設計と出力統合 |

## 9. 再現性・実行方法

確認できた実行コマンド:

```bash
poetry install
poetry run srs-game-gen --help
poetry run srs-game-gen gen-games --help
poetry run srs-game-gen apply-rules --help
poetry run srs-game-gen rank-heatmap --help
poetry run srs-game-gen rule-corr-heatmap --help
poetry run srs-game-gen evaluate-axioms --help
poetry run srs-test
```

小規模 workflow の典型例:

```bash
poetry run srs-game-gen gen-games -p 4 -c 100 --max-score 15 --seed 1 --out outputs
poetry run srs-game-gen apply-rules -p 4 --out outputs --rule group_lexcel --rule rp_index
poetry run srs-game-gen evaluate-axioms -p 4 --out outputs --scope coalition
poetry run srs-game-gen rule-corr-heatmap -p 4 --out outputs --method spearman
```

ただし、上のコマンドだけでは論文定義の RQ1/RQ2 を完全には満たさない。理由は、Reversal制約生成とrank correlation metricに差分があるためである。

再現性に関する現状:

- dependency install は Poetry。
- seed は `gen-games --seed` で固定可能。
- config は `--config <path>` を明示した場合だけ読む。
- root `config.yaml` の自動探索はない。
- 出力 canonical path は `outputs/synthetic/<constraint_set_id>/...`。
- 既存 `outputs/games` などは過去形式の可能性がある。
- 大規模実験用の固定 config、Makefile、paper export script は未整備。

今回実行できた検証:

```bash
poetry run srs-game-gen --help
poetry run srs-game-gen gen-games --help
poetry run srs-game-gen apply-rules --help
poetry run srs-game-gen rank-heatmap --help
poetry run srs-game-gen rule-corr-heatmap --help
poetry run srs-game-gen evaluate-axioms --help
poetry run srs-test tests/unit/domain/ranking tests/unit/domain/axioms tests/unit/application/synthetic_workflow -q
poetry run srs-test tests/e2e/interfaces/cli/test_synthetic_workflow.py tests/integration/application/axiom_evaluation/test_synthetic_reports.py tests/integration/application/experiments/test_run_synthetic_experiment.py -q
```

結果:

- unit subset: 7 passed
- e2e/integration subset: 7 passed

整備すべき内容:

- 論文実験用 config YAML。
- 実行コマンドを固定した `docs/simulation_runbook.md` または Makefile。
- 実行した commit、seed、`n`, `R`, `max_score`, constraints を保存する metadata JSON。
- 生成結果を `results/` と `figures/` へ paper-ready に export するコマンド。

## 10. 次に行うべき実装タスク

1. 論文定義版 Reversal lens constraint generator を検証し、active surfaceでは `reversal` を正式名にする。
2. Reversal lens consistency rate を `rp_index` 専用に集計する。空制約入力は平均から除外する。
3. Group Lex-cel と RP-Difference の rank correlation を、同サイズ `X_k` ごと、tie average rank、constant vector NA除外で実装する。
4. `results/lens_consistency.csv`, `results/rank_correlation.csv`, `results/simulation_summary.csv` 相当を生成する。
5. `figures/reversal_consistency.pdf/png` と `figures/rank_correlation_glc_rp.pdf/png` を生成する。
6. `docs/simulation_result_summary.md` に、実験設定、件数、除外件数、主要数値を自動または半自動で書き出す。
7. 論文リポジトリへコピーしやすい成果物配置を整える。
8. root docs の出力パス記述を現行 canonical layout に合わせて更新する。

## 11. 論文リポジトリへ渡すべき成果物

| 成果物 | 目的 | 論文側の挿入先 |
| --- | --- | --- |
| `results/simulation_summary.csv` | RQ1/RQ2 の主要指標をまとめる | Simulation Analysis 本文の数値要約 |
| `results/lens_consistency.csv` | RP-Difference x Reversal の per-game/per-size consistency | RQ2 の表、appendix の詳細表 |
| `results/rank_correlation.csv` | Group Lex-cel vs RP-Difference の per-game/per-size Spearman | RQ1 の表、appendix の詳細表 |
| `results/experiment_metadata.json` | commit, seed, `n`, `R`, `max_score`, constraints, commands | 再現性 appendix |
| `figures/reversal_consistency.pdf` | Reversal consistency の本文図 | RQ2 本文 |
| `figures/reversal_consistency.png` | preview / slide / issue共有 | 補助 |
| `figures/rank_correlation_glc_rp.pdf` | GLC vs RP correlation の本文図 | RQ1 本文 |
| `figures/rank_correlation_glc_rp.png` | preview / slide / issue共有 | 補助 |
| `figures/rule_corr_coalition_appendix.pdf` | full comparison heatmap | appendix |
| `docs/simulation_result_summary.md` | 本文へ転記する短い自然文要約 | paper draft の Simulation Analysis |

未解決事項:

- legacy archive には旧命名が残るが、論文用 active surface では `reversal` を正式名にする。
- RQ1/RQ2 の対象 `n`, `R`, `max_score`, constraints を確定する必要がある。
- `rank_style` は CSV serialize では competition が既定だが、論文metricでは average rank を使う方針なので、metric計算は CSV rank label に依存しない専用実装が望ましい。
- 既存 `outputs/` と `legacy/outputs/` は生成条件が十分に記録されていないため、そのまま論文数値として使うべきではない。
