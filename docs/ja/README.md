# CMIS Lab 向けガイド

このドキュメントは、CMIS Lab を含む日本語話者の共同研究者向けに、このリポジトリを短時間で把握するための入口です。

メンテナンスメモ: 内容は [`../en/README.md`](../en/README.md) と同期対象です。案内内容や導線を更新した場合は、英語版も見直してください。

構成メモ: `en/` と `ja/` のドキュメントツリーは構造をそろえて維持します。片方で章を追加・移動・削除した場合は、もう片方でも同じ構造変更を反映してください。

## このリポジトリの位置づけ

- 協力ゲームのランキング規則を比較するための研究用コードベースです。
- 合成ゲーム実験と実データ実験の両方を扱います。
- サポート対象の Poetry CLI は repository root にあります。
- `srs-real-gen` は root の Poetry project から `src` 側実装へ接続されています。
- 移行済みスライスの module-entry CLI は [`../../src/`](../../src/) からも直接叩けます。
- 新しい [`../`](../) 配下の docs は、共同研究しやすくするための整理レイヤーです。

## 何ができるか

### 1. 合成ゲーム実験

root CLI 契約に含まれる `srs-game-gen` により、以下を実行できます。

- 全連合を持つゲーム表の生成
- 複数のランキング規則の適用
- ranking figure の出力

公理評価や一部の集計コマンドは、まだ root CLI 契約には含めていません。

### 2. 実データ実験

`srs-real-gen` により、以下を実行できます。

- 特徴量マスク性能表を協力ゲーム形式へ変換
- 移行済みのランキング規則を再利用
- データセットごとの図表・ヒートマップを生成

## 最初に読むべき資料

1. [`../../README.md`](../../README.md)
2. [`architecture.md`](architecture.md)
3. [`architecture/README.md`](architecture/README.md)
4. [`../../src/README.md`](../../src/README.md)
5. [`research-workflow.md`](research-workflow.md)
6. 数理的な補足が必要な場合だけ [`../../legacy/docs/README.md`](../../legacy/docs/README.md)

## 典型的な読み方

### コード全体を把握したい場合

- [`architecture.md`](architecture.md) でモジュール構成を確認
- 新規実装の前提は [`architecture/module-boundaries.md`](architecture/module-boundaries.md) と [`../../src/README.md`](../../src/README.md) を見る
- 実装の主対象は [`../../src/`](../../src/) を見る
- 旧実装の細部が必要な場合だけ [`../../legacy/src/gamegen`](../../legacy/src/gamegen) と [`../../legacy/src/realgen`](../../legacy/src/realgen) を参照する

### 数式やルール定義を確認したい場合

- [`../../legacy/docs/ranking/README.md`](../../legacy/docs/ranking/README.md)
- [`../../legacy/docs/axioms/README.md`](../../legacy/docs/axioms/README.md)

### 実験の流れだけ知りたい場合

- [`research-workflow.md`](research-workflow.md)
- [`../../README.md`](../../README.md) の root CLI 契約

## セットアップ

```bash
poetry install
poetry run srs-real-gen --help
poetry run srs-game-gen --help
```

## 最小限の実行例

```bash
# 合成ゲーム実験
poetry run srs-game-gen gen-games -p 4 -c 100 --out outputs
poetry run srs-game-gen apply-rules -p 4 --out outputs
poetry run srs-game-gen make-figures --rankings-dir outputs/rankings --out outputs

# 実データ実験
mkdir -p inputs/feature_mask_tables/<dataset_id>
poetry run srs-real-gen import-game <dataset_id>
poetry run srs-real-gen apply-rules <dataset_id>
poetry run srs-real-gen make-figures <dataset_id>
```

## 読み替えの指針

- `legacy/README.md` は「歴史的な CLI リファレンス」
- `legacy/docs/` は「数理 appendix と詳細仕様」
- `docs/` は「共同研究者向けの案内」と「新規実装の標準文書」
- `src/` は「サポート対象 workflow の implementation of record」

現時点では、この分担で読むのが最も効率的です。通常運用では root CLI と `docs/` を先に見てください。`legacy/` は履歴資料として保持する archive であり、一次導線ではありません。
