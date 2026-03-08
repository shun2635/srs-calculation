# srs-calculation

このリポジトリは、協力ゲームの生成・ランキング計算・公理検証と、実データに対する同系統の集計/可視化を扱う Python CLI 群を管理しています。

現時点の実装本体は [`legacy/`](legacy/) 配下にあります。リポジトリ直下は入口ドキュメントと共通設定を置くための薄いレイヤーです。

## 構成

- [`legacy/`](legacy/): 実行可能な Poetry プロジェクト本体
- [`legacy/src/gamegen`](legacy/src/gamegen): 合成ゲームの生成、ランキング列の計算、公理チェック
- [`legacy/src/realgen`](legacy/src/realgen): 実データ取り込み、ルール適用、可視化
- [`legacy/docs/`](legacy/docs/): ランキング指標と公理の設計/仕様ドキュメント
- [`legacy/inputs/`](legacy/inputs/): 入力データ置き場
- [`legacy/outputs/`](legacy/outputs/): 生成物の出力先

## セットアップ

作業ディレクトリは `legacy/` を前提にします。

```bash
cd legacy
poetry install
```

CLI の確認:

```bash
poetry run game-gen --help
poetry run real-gen --help
```

テスト:

```bash
poetry run pytest
```

## 主な使い方

### 合成ゲームパイプライン

```bash
cd legacy

# ゲーム生成
poetry run game-gen gen-games -p 4 -c 100 --out outputs

# ランキング列を付与
poetry run game-gen apply-rules -p 4 --out outputs

# 公理チェック
poetry run game-gen check-axioms -p 4 --out outputs

# 一括実行
poetry run game-gen pipeline -p 4 -c 100 --out outputs
```

主な出力先:

- `outputs/games/nN/`
- `outputs/rankings/nN/`
- `outputs/axiom/nN/`
- `outputs/heatmaps/nN/`

### 実データパイプライン

```bash
cd legacy

# raw CSV + schema.yaml からゲーム表へ正規化
poetry run real-gen import-game <dataset_id>

# ranking ルールを適用
poetry run real-gen apply-rules <dataset_id>

# 図表生成
poetry run real-gen make-figures <dataset_id>

# ルール別ヒートマップ生成
poetry run real-gen feature-rule-heatmap <dataset_id>
```

主な出力先:

- `outputs/real/<dataset_id>/`

## 参照ドキュメント

- [`legacy/README.md`](legacy/README.md): `legacy` プロジェクトの詳細 README
- [`legacy/docs/README.md`](legacy/docs/README.md): ドキュメント全体の目次
- [`legacy/config.yaml`](legacy/config.yaml): 既定パラメータと描画設定

## 運用メモ

- 生成物は基本的に `legacy/outputs/` 配下へ出ます。
- Python キャッシュやローカル仮想環境は `.gitignore` で除外しています。
- 将来的に `legacy/` 以外へ実装を分離する場合は、この README をリポジトリ全体の案内として更新してください。
