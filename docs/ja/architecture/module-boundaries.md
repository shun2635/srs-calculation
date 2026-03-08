# 新規実装のモジュール境界

このドキュメントは、[`../../../src/`](../../../src/) 配下に置くコードの想定パッケージ境界を定義します。

## 目標パッケージ構成

```text
src/
  srs_calculation/
    domain/
    application/
    infrastructure/
    interfaces/
```

## 境界定義

### `domain/`

役割:

- 中核となるビジネス概念と数理概念
- 連合モデル
- ランキング規則
- 公理定義

ルール:

- CLI コードを置かない
- ファイルシステムアクセスを持たせない
- 描画処理を入れない
- 決定的でテストしやすいロジックを優先する

### `application/`

役割:

- ユースケースをオーケストレーションする
- domain ロジックと外部サービスをつなぐ
- import、ルール適用、レポート生成のようなワークフロー単位の処理を定義する

ルール:

- `domain/` に依存してよい
- CLI の直接解析を持たない
- ワークフロー制御を保存詳細から切り離す

### `infrastructure/`

役割:

- CSV と YAML の I/O
- 設定読み込み
- 永続化アダプタ
- 描画や外部ライブラリ統合

ルール:

- `domain/` と `application/` に依存してよい
- 外部副作用をこの層に閉じ込める
- 他層には狭いインターフェースだけを公開する

### `interfaces/`

役割:

- CLI エントリポイント
- コマンドアダプタ
- 将来的な API や notebook 向けアダプタ

ルール:

- 薄い層に保つ
- ビジネスロジックは `application/` に委譲する
- 既に別箇所で表現されている検証やワークフロー制御を重複させない

## 依存方向

想定する依存方向は次です。

```text
interfaces -> application -> domain
infrastructure -> application -> domain
```

`domain/` は最も安定し、最もフレームワーク非依存な層として保つべきです。

## Tests

想定するテスト構成は次です。

```text
tests/
  unit/
  integration/
  e2e/
```

- `unit/`: domain と小さな application サービス
- `integration/`: infrastructure アダプタと CLI 配線
- `e2e/`: 現実的な fixture を使うフルワークフロー

## `src/` に入れないもの

- `legacy/` 挙動を一時的に維持するためだけの互換コード
- 大きな生成物
- `docs/` に置くべき断片的な研究メモ
- 生の外部データセット

## レビュー規則

この境界をまたぐ変更や、新しい上位アーキテクチャ概念の導入は、[`../adr/`](../adr/) の ADR で記録してください。
