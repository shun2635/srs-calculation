# アーキテクチャ概要

このドキュメントは、現在のリポジトリ構成をそのまま説明するためのものです。将来の理想構成を定義する文書ではありません。

`src/` 配下に置く新規実装の目標アーキテクチャは、次を参照してください。

- [`architecture/README.md`](architecture/README.md)
- [`architecture/module-boundaries.md`](architecture/module-boundaries.md)
- [`../../src/README.md`](../../src/README.md)

## 全体構成

現状のリポジトリは、実質的には [`../../legacy/`](../../legacy/) 配下の 1 つの Poetry プロジェクトを中心に構成されています。

- [`../../legacy/pyproject.toml`](../../legacy/pyproject.toml): パッケージ定義、依存関係、CLI エントリポイント
- [`../../legacy/config.yaml`](../../legacy/config.yaml): 実行時の既定設定
- [`../../legacy/tests/`](../../legacy/tests/): CLI と主要挙動の回帰テスト

コードは大きく 2 つのパッケージに分かれています。

## パッケージ 1: `gamegen`

場所: [`../../legacy/src/gamegen`](../../legacy/src/gamegen)

役割:

- 合成協力ゲームを生成する
- 複数のランキング値とランキング列を計算する
- 公理チェックを実行する
- 図表やヒートマップを出力する

主な構成要素:

- [`../../legacy/src/gamegen/commands`](../../legacy/src/gamegen/commands): Click ベースの CLI コマンド
- [`../../legacy/src/gamegen/rules`](../../legacy/src/gamegen/rules): ランキング規則の実装
- [`../../legacy/src/gamegen/axioms`](../../legacy/src/gamegen/axioms): 公理チェックとサマリ可視化
- [`../../legacy/src/gamegen/io`](../../legacy/src/gamegen/io): CSV パスと I/O 補助
- [`../../legacy/src/gamegen/ranking`](../../legacy/src/gamegen/ranking): ルール登録

処理の流れ:

1. ゲーム表を生成する。
2. ランキング規則を適用する。
3. ランキング結果に対して公理を検証する。
4. 可視化を出力する。

## パッケージ 2: `realgen`

場所: [`../../legacy/src/realgen`](../../legacy/src/realgen)

役割:

- 実データの評価表を協力ゲーム表現へ変換する
- `gamegen` のランキングロジックを再利用する
- データセット単位の可視化を作成する

主な構成要素:

- [`../../legacy/src/realgen/commands`](../../legacy/src/realgen/commands): 実データ用 CLI コマンド
- [`../../legacy/src/realgen/rules`](../../legacy/src/realgen/rules): 観測データ特有のルール処理
- [`../../legacy/src/realgen/io`](../../legacy/src/realgen/io): 特徴量ラベル関連の補助
- [`../../legacy/src/realgen/datasets.py`](../../legacy/src/realgen/datasets.py): データセット定義と振り分け

処理の流れ:

1. raw CSV と schema メタデータからデータセットを取り込む。
2. 内部のゲーム表形式へ正規化する。
3. ランキング規則を適用する。
4. 図表とヒートマップを出力する。

## データ入出力

入力:

- [`../../legacy/inputs/`](../../legacy/inputs/)
- 特に [`../../legacy/inputs/feature_mask_tables/`](../../legacy/inputs/feature_mask_tables/)

出力:

- [`../../legacy/outputs/games/`](../../legacy/outputs/games/)
- [`../../legacy/outputs/rankings/`](../../legacy/outputs/rankings/)
- [`../../legacy/outputs/axiom/`](../../legacy/outputs/axiom/)
- [`../../legacy/outputs/heatmaps/`](../../legacy/outputs/heatmaps/)
- [`../../legacy/outputs/real/`](../../legacy/outputs/real/)

## ドキュメント層

現在は 2 つのドキュメント層があります。

- [`./`](./): 日本語の共同研究向け案内
- [`../en/`](../en/): 英語の共同研究向け案内
- [`../../legacy/docs/`](../../legacy/docs/): 詳細な設計メモ、ランキング規則説明、公理定義

まず `docs/ja` または `docs/en` を読み、実装詳細が必要になった時点で `legacy/docs` に進むのが基本です。

## 拡張時の主要ポイント

機能を拡張する場合、主な変更候補は次です。

- ランキング規則の追加や修正: [`../../legacy/src/gamegen/rules`](../../legacy/src/gamegen/rules)
- ルール登録の更新: [`../../legacy/src/gamegen/ranking/registry.py`](../../legacy/src/gamegen/ranking/registry.py)
- CLI 操作の追加: [`../../legacy/src/gamegen/commands`](../../legacy/src/gamegen/commands) または [`../../legacy/src/realgen/commands`](../../legacy/src/realgen/commands)
- 数理的な説明の追記: [`../../legacy/docs/ranking/`](../../legacy/docs/ranking/)
- 公理ロジックの説明追加: [`../../legacy/docs/axioms/`](../../legacy/docs/axioms/)

## 現状の制約

現時点の実行コードは歴史的な `legacy/` 構成に依存しています。新しい docs 構造は共同開発しやすくするためのものであり、まだコード配置そのものを置き換えてはいません。
