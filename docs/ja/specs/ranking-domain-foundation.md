# Specification: Ranking Domain Foundation

## Summary

この spec は、`legacy/` から `src/` へ移す最初の具体的な対象を定義します。対象は、CLI、CSV、描画処理から切り離された ranking の domain foundation であり、連合ゲームのモデル、ランキング規則の共通インターフェース、そして最初の純粋なランキング規則群を `src/` 側へ移します。

## Problem

現在の `legacy/` 実装は研究用の参照として有用ですが、ランキングの中核ロジックはまだコマンド配線、レジストリ処理、ファイル中心のワークフローと近い位置にあります。そのため、大規模な共同開発では次の問題があります。

- 安全に拡張できる安定した domain 層がない
- `legacy` との同等性確認が必要以上に難しい
- `src/` 側でも同じ構造的結合を繰り返すリスクがある

リポジトリ上は `src/` を新規実装の主な置き場として定義済みですが、最初に何を移すかを定義した実 spec がまだありません。

## Goals

- `src/srs_calculation/domain/` に最初の本実装スライスを作る
- 連合ゲームとランキング結果の安定した domain model を定義する
- 複数の規則で共有できる rule interface を導入する
- `legacy` から最初の純粋なランキング規則群を移し、同等性テストを付ける
- CLI 全体を作り直さずに完了できる狭い移行単位にする

## Non-goals

- この段階で `game-gen` CLI を置き換えること
- 描画、ヒートマップ、図表生成の移行
- 実データワークフロー全体の移行
- CSV 形式や出力ディレクトリ構造の変更
- すべてのランキング規則を一度に設計し直すこと

## Scope

対象:

- `src/srs_calculation/domain/` に置く連合ゲームとランキング規則の基盤
- in-memory のゲーム表現に対して規則を適用する最小限の `src/srs_calculation/application/` サービス
- legacy 互換の game CSV を読み、legacy 互換の rankings CSV を書くための最小限の `src/srs_calculation/infrastructure/persistence/` アダプタ
- 移行した ranking workflow を叩くための薄い `src/srs_calculation/interfaces/cli/` アダプタ
- 移行した規則の同等性テスト
- この移行対象を説明する docs 更新

対象外:

- 現在の `game-gen` CLI 全体の置き換え
- ranking slice の移行に必要な CSV アダプタを超える広い永続化対応
- 実データ import と可視化
- 公理チェックの移行

## Proposed design

### Target modules

最初の移行スライスでは、少なくとも次のモジュール群を導入します。

```text
src/srs_calculation/
  domain/
    games/
      coalition_game.py
    ranking/
      result.py
      rule.py
      registry.py
      rules/
        shapley.py
        banzhaf.py
        lexcel.py
        ordinal_banzhaf.py
  application/
    ranking/
      apply_ranking_rules.py
      apply_ranking_rules_to_game_csv.py
  infrastructure/
    persistence/
      csv_game_repository.py
      csv_ranking_repository.py
  interfaces/
    cli/
      game_gen.py
```

`models/` や `rules/` のような汎用バケットではなく、feature ごとのまとまりで切ることを前提にします。

### Domain model

domain 層では、CSV や pandas に依存しない in-memory の協力ゲーム表現を定義します。

最低限必要な性質:

- 連合を決定的かつ hashable な形で表現できる
- 連合スコアを DataFrame に縛られずに扱える
- 規則の出力を、後で表へ変換できる構造化データとして持てる

想定する domain concept:

- `CoalitionGame`
- `CoalitionValue`
- `RuleScoreSet`
- `RuleRankSet`
- `RankingResult`

これらの正確な名前を固定する必要はありませんが、責務分離の考え方は維持します。

### Rule interface

各ランキング規則は、次を満たす共通インターフェースを実装します。

- ルール ID を宣言する
- domain の game object を受け取る
- DataFrame の破壊的更新ではなく、構造化された結果を返す

この interface は次の両方に対応する必要があります。

- score 列を返す規則
- rank 列を返す規則
- score と rank の両方を返す規則

また、singleton 向けか coalition 全体向けかは rule-specific metadata として持ち、共通 interface 側では決め打ちしません。

### First migrated rules

最初の実装対象は、特殊な描画やデータセット依存処理を持たない、比較的純粋な計算規則に限定します。

推奨する初回バッチ:

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`

この 4 つで、アーキテクチャ検証とスコープ管理を両立します。

### Application service

最小限の application 層サービスは次を担います。

- in-memory の game object を受け取る
- rule identifier のリストを受け取る
- 新しい registry で rule を解決する
- rule 出力をまとめた構造化結果を返す

これにより、今後 interface 層が rule モジュールを場当たり的に直接呼ぶことを防ぎます。

また、最初の移行スライスでは file-based な application use case として次も許容します。

- legacy 互換の game CSV を `CoalitionGame` に読む
- application サービス経由で規則を適用する
- infrastructure アダプタで legacy 互換の `rank_*` / `score_*` 列へ serialize する

## Data and interfaces

このフェーズでは新しい公開 CLI は定義しません。
ただし、`application/` に直接委譲する薄い CLI adapter を migration slice の検証用に追加することは許容します。

代わりに主なインターフェース契約は次です。

- 入力: in-memory の coalition game
- 出力: 後で infrastructure 層が serialize できる構造化 rule result

移行境界では、次の file-based contract も持ってよいものとします。

- 入力: `player*`, `score`, `rank` を持つ legacy 互換 game CSV
- 出力: 既存の `rank_*` / `score_*` 命名を維持した legacy 互換 rankings CSV

互換性メモ:

- 移行した rule は、対応する `legacy` rule 出力と意味的に同等である必要がある
- 出力列名の互換は serialization 境界で維持し、内部オブジェクト名は必要なら変えてよい
- 内部の rule identifier は `ordinal_banzhaf` のような snake_case を優先する

## Migration plan

### Step 1

`src/` 配下に基礎 domain model と rule interface を作る。

### Step 2

次の `legacy` 実装から、初回バッチの規則を移す。

- `legacy/src/gamegen/rules/shapley.py`
- `legacy/src/gamegen/rules/banzhaf.py`
- `legacy/src/gamegen/rules/lexcel.py`
- `legacy/src/gamegen/rules/ordinal_banzhaf.py`

### Step 3

新しい registry を使う application 層の rule runner を作る。

### Step 4

新しい ranking slice を legacy 互換ファイルへ接続する最小限の CSV アダプタを追加する。

### Step 5

共有 fixture 上で `src/` と `legacy` を比較する parity test を追加する。

### Step 6

必要に応じて、移行した ranking workflow を end-to-end で叩く薄い CLI adapter を追加する。

### Step 7

意図的な差分があれば文書化し、必要に応じて後続 ADR を起票する。

## Testing plan

移行スライスには次のテストを含めます。

- 連合ゲーム domain model の unit test
- 各 rule の unit test
- application 層の rule runner の integration test
- legacy 互換 CSV の read/write と file-based ranking application の integration test
- 移行した ranking workflow に委譲する薄い CLI adapter の integration test
- 代表的な小規模ゲームに対する `legacy` 比較の parity test

推奨する parity 方針:

- 小さく決定的な協力ゲームを使う
- rule ごとに score と rank を比較する
- tie と coalition ordering の edge case を含める

## Open questions

- 最初の application サービスは強い型のオブジェクトだけを返すべきか、それともテスト用の簡易 tabular export helper も持つべきか。
- singleton 専用規則と coalition 全体規則は、単一の result contract にまとめるべきか、それとも関連する 2 種の result type に分けるべきか。

## Related documents

- [`../architecture/module-boundaries.md`](../architecture/module-boundaries.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../../../src/README.md`](../../../src/README.md)
