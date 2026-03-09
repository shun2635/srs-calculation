# 研究ワークフロー

このドキュメントは、共同研究の文脈でこのリポジトリをどう使うかを整理したものです。

貢献ルールや新規実装の移行方針については、次も参照してください。

- [`development/contributing.md`](development/contributing.md)
- [`architecture/migration-from-legacy.md`](architecture/migration-from-legacy.md)

## 2 つの主要ワークフロー

このリポジトリは、関連する 2 つのワークフローを持っています。

### 1. 合成ゲーム実験

ランキング規則の性質を制御されたゲーム生成のもとで比較したいときに使います。

典型的な流れ:

1. `srs-game-gen gen-games` でゲーム表を生成する。
2. `srs-game-gen apply-rules` でランキング規則を適用する。
3. `srs-game-gen make-figures` で ranking figure を出力して確認する。

関連ドキュメント:

- root CLI 契約: [`../../README.md`](../../README.md)
- `src` 実装の入口: [`../../src/README.md`](../../src/README.md)
- ルール説明: [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- 公理説明: [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

補足:

- `check-axioms` などの synthetic 周辺コマンドは archive-only であり、root CLI 契約には含めていません
- 数理定義の確認には引き続き `legacy/docs` を参照します

### 2. 実データ実験

モデル評価表や特徴量部分集合実験から研究を始めるときに使います。

典型的な流れ:

1. raw 入力を [`../../inputs/feature_mask_tables/`](../../inputs/feature_mask_tables/) に置く。
2. `srs-real-gen import-game` で正規化する。
3. `srs-real-gen apply-rules` でランキング規則を適用する。
4. `srs-real-gen make-figures` と `srs-real-gen feature-rule-heatmap` で図表を作成する。

関連ドキュメント:

- root CLI 契約: [`../../README.md`](../../README.md)
- 入力データ配置: [`../../src/README.md`](../../src/README.md)
- 実データ設計メモ: [`../../legacy/docs/design/real_data.md`](../../legacy/docs/design/real_data.md)

## 再現性チェックリスト

共同研究では、次の情報をできるだけ固定・保存してください。

- リポジトリの commit hash
- 使用した `config.yaml` の値
- 実行した CLI コマンドとオプション
- データセット ID と schema ファイル
- 検証用に保存した出力ディレクトリ

## 推奨される協業パターン

CMIS Lab 内での議論でも、LAMSADE との議論でも、基本の進め方は同じです。

1. まずこの `ja/` 配下、または英語が必要なら [`../en/`](../en/) を読む。
2. 研究課題に応じて、合成ゲーム実験か実データ実験の流れを選ぶ。
3. 実行は root CLI を使い、実装確認は `src/` を優先して見る。
4. ルール定義や公理条件を厳密に確認したくなった段階で `legacy/docs` を appendix として参照する。

## この構成を採っている理由

コード配置にはまだ移行途中の要素が残りますが、共同研究の一次導線はすでに root CLI と `docs/` に寄せています。そのため、全面的なコード移行を待たずにオンボーディングしやすくしています。
