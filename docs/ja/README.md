# CMIS Lab 向けガイド

このドキュメントは、CMIS Lab を含む日本語話者の共同研究者向けに、このリポジトリを短時間で把握するための入口です。

メンテナンスメモ: 内容は [`../en/README.md`](../en/README.md) と同期対象です。案内内容や導線を更新した場合は、英語版も見直してください。

## このリポジトリの位置づけ

- 協力ゲームのランキング規則を比較するための研究用コードベースです。
- 合成ゲーム実験と実データ実験の両方を扱います。
- 現状の実装本体は [`../../legacy/`](../../legacy/) にあります。
- 新しい [`../`](../) 配下の docs は、共同研究しやすくするための整理レイヤーです。

## 何ができるか

### 1. 合成ゲーム実験

`game-gen` により、以下を一連で実行できます。

- 全連合を持つゲーム表の生成
- 複数のランキング規則の適用
- 公理適合率の集計
- ヒートマップや図表の出力

### 2. 実データ実験

`real-gen` により、以下を実行できます。

- 特徴量マスク性能表を協力ゲーム形式へ変換
- `gamegen` 側のランキング規則を再利用
- データセットごとの図表・ヒートマップを生成

## 最初に読むべき資料

1. [`../../README.md`](../../README.md)
2. [`../architecture.md`](../architecture.md)
3. [`../research-workflow.md`](../research-workflow.md)
4. 必要に応じて [`../../legacy/docs/README.md`](../../legacy/docs/README.md)

## 典型的な読み方

### コード全体を把握したい場合

- [`../architecture.md`](../architecture.md) でモジュール構成を確認
- [`../../legacy/src/gamegen`](../../legacy/src/gamegen) と [`../../legacy/src/realgen`](../../legacy/src/realgen) を見る

### 数式やルール定義を確認したい場合

- [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

### 実験の流れだけ知りたい場合

- [`../research-workflow.md`](../research-workflow.md)
- [`../../legacy/config.yaml`](../../legacy/config.yaml)

## セットアップ

```bash
cd legacy
poetry install
poetry run game-gen --help
poetry run real-gen --help
```

## 最小限の実行例

```bash
cd legacy

# 合成ゲーム実験
poetry run game-gen pipeline -p 4 -c 100 --out outputs

# 実データ実験
poetry run real-gen import-game <dataset_id>
poetry run real-gen apply-rules <dataset_id>
```

## 読み替えの指針

- `legacy/README.md` は「CLI の使い方」
- `legacy/docs/` は「詳細仕様・設計メモ」
- `docs/` は「共同研究者向けの案内」

コード再編前の段階では、この分担で読むのが最も効率的です。
