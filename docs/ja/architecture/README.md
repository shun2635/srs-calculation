# 目標アーキテクチャ文書

このディレクトリには、[`../../../src/`](../../../src/) 配下の新規実装のためのアーキテクチャ文書をまとめます。

## このディレクトリの役割

- 目標となるパッケージ境界を定義する
- `legacy/` からの移行判断を記録する
- 共同開発で参照すべき安定した設計基準を提供する

## 読む順番

1. [`module-boundaries.md`](module-boundaries.md)
2. [`migration-from-legacy.md`](migration-from-legacy.md)
3. [`legacy-removal-runbook.md`](legacy-removal-runbook.md)
4. [`../../../src/README.md`](../../../src/README.md)

`legacy-removal-runbook.md` は、runtime 依存をどう外したかを記録するために残しています。archive tree を削除するための active plan ではありません。

## 適用範囲

ここに書くのは新規コードの目標構成とそこへの移行方針です。archive として残している `legacy/` 実装の snapshot を説明する [`../architecture.md`](../architecture.md) の代わりではありません。
