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

1. `game-gen gen-games` でゲーム表を生成する。
2. `game-gen apply-rules` または `game-gen pipeline` でランキング規則を適用する。
3. `game-gen check-axioms` で公理適合率を評価する。
4. ヒートマップやサマリ図を出力して確認する。

関連ドキュメント:

- CLI リファレンス: [`../../legacy/README.md`](../../legacy/README.md)
- ルール説明: [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- 公理説明: [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

### 2. 実データ実験

モデル評価表や特徴量部分集合実験から研究を始めるときに使います。

典型的な流れ:

1. raw 入力を [`../../legacy/inputs/feature_mask_tables/`](../../legacy/inputs/feature_mask_tables/) に置く。
2. `real-gen import-game` で正規化する。
3. `real-gen apply-rules` でランキング規則を適用する。
4. `real-gen make-figures` と `real-gen feature-rule-heatmap` で図表を作成する。

関連ドキュメント:

- 入力データの説明: [`../../legacy/inputs/README.md`](../../legacy/inputs/README.md)
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
3. ルール定義や公理条件を厳密に確認したくなった段階で `legacy/docs` を参照する。
4. リポジトリ再編が完了するまでは、[`../../legacy/`](../../legacy/) を実装上の正本として扱う。

## この構成を採っている理由

コード配置はまだ歴史的な `legacy/` 中心ですが、共同研究の要件はすでに現在進行形です。そのため、`docs/ja` と `docs/en` を入口にして、全面的なコード移行を待たずにオンボーディングしやすくしています。
