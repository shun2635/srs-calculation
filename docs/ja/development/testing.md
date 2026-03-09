# テスト設計

このドキュメントは、`src/` ベース実装に対する現在のテスト設計を定義します。

## 目的

テストスイートの目的は、`legacy/` から `src/` への移行を進めながら、挙動を壊さずに設計改善も進められるようにすることです。

そのため、テスト戦略は次の 2 つを同時に満たす必要があります。

- 新しい実装単体の正しさを検証する
- parity が必要な箇所では `legacy` との挙動一致を検証する

## テスト層

現在のリポジトリでは、主に 3 つのテスト層を使います。

### `tests/unit/`

役割:

- 小さく独立した振る舞いを検証する
- domain model や狭い infrastructure adapter を検証する
- 低レベルな回帰を早く検出する

例:

- `tests/unit/domain/`
- `tests/unit/infrastructure/`

unit test を使う対象:

- 決定的な domain ロジック
- validation ルール
- 小さなデータ変換
- 大きな workflow 準備なしで検証できる repository や renderer の挙動

### `tests/integration/`

役割:

- 複数モジュールにまたがる use case の連携を検証する
- infrastructure 配線や CLI adapter を検証する
- application service が期待するファイル、出力、構造化結果を返すことを確認する

例:

- `tests/integration/application/`
- `tests/integration/interfaces/cli/`

integration test を使う対象:

- application service
- CSV ベースの ranking workflow
- dataset ingestion
- CLI コマンド挙動

### `tests/parity/`

役割:

- 新しい `src/` 挙動を `legacy` 参照実装と比較する
- ルール移行や workflow 移行のリスクを下げる

例:

- `tests/parity/ranking/`

parity test を使う対象:

- migrated capability が legacy 挙動を維持すべき場合
- ranking rule や workflow を `legacy` から移す場合
- 内部実装の assert だけではなく、外部挙動の境界で回帰を検出したい場合

## ディレクトリ規約

標準構成は次です。

```text
tests/
  unit/
    domain/
    infrastructure/
  integration/
    application/
    interfaces/
  parity/
    ranking/
```

新しいテストを追加するときは次を基本にします。

- 可能な限り source-layer の境界に対応させる
- domain のテストは `unit/domain` に置く
- application workflow のテストは `integration/application` に置く
- CLI テストは `integration/interfaces/cli` に置く
- `legacy` 比較テストは `parity` に置く

## 各層で何をテストするか

### Domain

主に unit test で次を検証します。

- coalition game の validation
- ranking result contract
- rule registry の挙動
- 純粋な ranking rule ロジック
- axiom predicate ロジック

### Application

主に integration test で次を検証します。

- in-memory game への ranking rule 適用
- game CSV directory への rule 適用
- dataset 単位の ranking workflow
- experiment runner

### Infrastructure

主に unit test で次を検証します。

- CSV repository の挙動
- config 読み込み
- 入出力が狭く isolatable な plotting helper

複数 adapter の連携が必要な場合に限って integration test を使います。

### Interfaces

主に integration test で次を検証します。

- CLI help 出力
- command option の配線
- 期待されるファイル生成副作用

## 実行ルール

`src` ベースのテスト実行環境は root Poetry environment を標準とします。

全件実行:

```bash
poetry install
poetry run srs-test
```

一部だけ実行:

```bash
poetry run srs-test tests/unit -q
poetry run srs-test tests/integration/application/ranking/test_apply_ranking_rules.py
poetry run srs-test tests/parity/ranking -q
```

## コード変更時の基本期待値

### Domain ロジックを変える場合

追加または更新するもの:

- unit test
- `legacy` から移したロジックなら parity test

### Application workflow を変える場合

追加または更新するもの:

- integration test
- legacy 互換を維持する workflow なら parity test

### CLI 挙動を変える場合

追加または更新するもの:

- integration の CLI test
- サポートする command surface を説明する docs

## レビュー観点

レビュー時は次を確認します。

- その変更に対して、選ばれたテスト層は妥当か
- failure message は回帰原因の特定に十分か
- parity を約束している箇所で parity test が入っているか
- workflow や test command を変えた場合に docs が更新されているか

## 現状の制約

現在のテストスイートは移行フェーズ前提です。そのため一部のテストは、理想的な最終アーキテクチャよりも、意図的に legacy 互換挙動を重視しています。`src/` 実装が正本になった段階では、parity test の一部は縮小または廃止する可能性があります。
