# ADR-0002: legacy 専用 synthetic commands を root CLI 契約から外す

## Status

Accepted

## Context

このリポジトリでは、root CLI 契約を次に絞って定義しています。

- `real-gen`
- `srs-game-gen`
- `srs-test`

一方で、historical な synthetic commands の一部はまだ `legacy/` にしかありません。

- `game-gen check-axioms`
- `game-gen summarize-axioms`
- `game-gen axiom-summary-heatmap`
- `game-gen rank-heatmap`
- `game-gen rule-corr-heatmap`
- `game-gen pipeline`
- `game-gen make-figures-png`

これらを曖昧なまま残すと、長期的に次の問題があります。

- 共同研究者が「今後 root に移る予定なのか、もう使わない前提なのか」を判断できない
- docs がサポート対象の root execution surface を明確に書けない
- `legacy` 剥離 runbook で、移行必須の対象と archive に閉じる対象を区別できない

そのため、これらの commands を root の将来計画に含めるのかどうかを明示的に決める必要があります。

## Decision

上記の commands は、root CLI 契約から外し、archive-only とする。

この判断により、次を採用します。

- これらは `src/` への通常の移行対象とはみなさない
- 共同研究向けのサポート対象 root workflow には含めない
- archive が残る間だけ、`legacy/` 配下の historical behavior として保持する
- primary docs では通常運用の導線として案内しない

サポート対象の synthetic root workflow は、次に限定する。

- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen make-figures`
- `srs-game-gen rank-game`

将来、archive-only にした commands のいずれかを再度必要と判断した場合は、暗黙に scope へ戻すのではなく、新しい spec または ADR で再決定する。

## Consequences

良い影響:

- サポート対象の root CLI surface が小さく明確になる
- docs で「未移行」ではなく「archive-only」として整理できる
- `legacy` 剥離計画で、移行必須の command 数を減らせる

悪い影響:

- いくつかの historical な研究 workflow は、root project ではもうサポート対象とみなさない
- それらをまだ必要とする利用者は、forward path ではなく archive behavior として扱う必要がある

運用上の影響:

- root docs ではこれらの commands を archive-only と記述する
- 今後の移行計画では、新しい判断がない限りこれらを必須対象に数えない
- root CLI の test や docs は、これらがサポート surface に現れることを前提にしない

## Alternatives considered

- historical な synthetic commands をすべて `src/` に移植する
  - 共同研究で実際に必要な範囲を超えて root support surface を広げるため不採用
- docs に書かず、将来課題として曖昧に残す
  - 曖昧さが残り、deprecation 計画をきれいに進められないため不採用
- 履歴ごと即座に削除する
  - 移行期の参照用 archive としてはまだ有用なため不採用

## Related documents

- [`../architecture/legacy-removal-runbook.md`](../architecture/legacy-removal-runbook.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../../../README.md`](../../../README.md)
- [`../../../src/README.md`](../../../src/README.md)
