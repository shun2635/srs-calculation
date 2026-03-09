# ADR-0001: Ranking Domain Foundation を最初の移行スライスにする

## Status

Accepted

## Context

このリポジトリではすでに、

- `legacy/` を現在の参照実装
- `src/` を次の実装本体の配置先

として区別しています。

しかし、最初の移行対象を明示しないままだと、次のような互いに噛み合わない着手が起こりえます。

- CLI から先に作り直す
- 可視化から先に移す
- 実データ系ワークフローから先に移す
- `legacy` の大きなモジュールを、境界整理なしで `src/` にコピーする

そのため、フルスタックの作り直しを強制せずに domain 境界を立てられる、狭く安定した高レバレッジの最初の移行単位が必要です。

対応する spec は次です。

- [`../specs/ranking-domain-foundation.md`](../specs/ranking-domain-foundation.md)

## Decision

`legacy/` から `src/` への最初の移行スライスは、ranking domain foundation とする。

この判断により、次を採用します。

- `src/` に置く最初の本実装コードは、`domain/games` と `domain/ranking` を中心にする
- `domain/ranking` にランキング規則の共通 interface と registry を作る
- 最初に移行する規則は次に限定する
  - `shapley`
  - `banzhaf`
  - `lexcel`
  - `ordinal_banzhaf`
- in-memory の game object に対して規則を実行する最小限の application 層 rule runner を追加してよい

また、最初のスライスでは次を対象外とします。

- CLI の置き換え
- 描画やヒートマップの移行
- 実データワークフローの移行
- 公理チェックの移行
- `legacy` モジュールの大規模なコピー移植

## Consequences

良い影響:

- `src/` に domain 指向の実装開始点ができる
- `legacy` との parity test で移行を検証できる
- 共同開発者にとって、意味のある十分な大きさを持ちつつ完了可能なスコープになる
- 今後の CLI や infrastructure 作業が、安定した application/domain 境界を前提に進められる

悪い影響:

- 一時的に `legacy` と `src/` の重複が生じる
- 最初の段階では新しい CLI はまだ提供されない
- 後続の rule 追加時に interface の不足が見つかり、追加 ADR が必要になる可能性がある

運用上の影響:

- この機能に関する新規コードは `legacy/` ではなく `src/` を基本配置先とする
- 関連する実装変更ではこの ADR を参照する
- 最初のスライスを大きく拡張したい場合は、後続の ADR または spec で正当化する

## Alternatives considered

- CLI 全体を先に移行する
  - interface、I/O、domain を早い段階で混ぜてしまうため不採用
- 実データパイプラインを先に移行する
  - 先に安定した ranking domain 抽象が必要なため不採用
- `legacy` の ranking モジュールをそのまま `src/` にコピーする
  - 古い構造的結合を温存してしまうため不採用

## Related documents

- [`../specs/ranking-domain-foundation.md`](../specs/ranking-domain-foundation.md)
- [`../architecture/module-boundaries.md`](../architecture/module-boundaries.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
