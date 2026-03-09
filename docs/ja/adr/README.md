# Architectural Decision Records

このディレクトリには、新規実装とリポジトリ全体の技術判断を記録する ADR を置きます。

## ADR を追加する条件

次のような判断では ADR を追加してください。

- モジュール境界を変える
- 大きな依存関係を追加または削除する
- 長期的な保守性に影響する
- `src/` と `legacy/` の共存方針を変える

## 命名規則

連番付きのファイル名を使います。

- `0001-short-title.md`
- `0002-short-title.md`

タイトルは短く、判断内容が分かるものにしてください。

## 最低限入れる節

- Status
- Context
- Decision
- Consequences

## テンプレート

新しい ADR は [`0000-template.md`](0000-template.md) をベースに作成します。

## 現在の ADR

- [`0001-ranking-domain-foundation.md`](0001-ranking-domain-foundation.md): ranking domain foundation を `src/` への最初の移行スライスとして定義する
- [`0002-retire-legacy-only-synthetic-commands.md`](0002-retire-legacy-only-synthetic-commands.md): 一部の historical な synthetic commands を root CLI へ移さず archive-only として閉じる
- [`0003-reintroduce-synthetic-rank-correlation-commands.md`](0003-reintroduce-synthetic-rank-correlation-commands.md): `rank-heatmap` と `rule-corr-heatmap` を `src/` に移植した上で root `srs-game-gen` 契約へ戻す
- [`0004-complete-legacy-ranking-and-axiom-core-in-src.md`](0004-complete-legacy-ranking-and-axiom-core-in-src.md): legacy synthetic の全 rule と coalition-ranking axiom evaluator を `src/` core へ取り込む
