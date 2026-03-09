# ADR-0004: legacy synthetic の ranking / axiom core を `src` で完結させる

## Status

Accepted

## Context

ADR-0001 では、最初の移行単位として ranking rule の初回バッチだけを `src/` に移しました。現在その基盤は安定したので、synthetic ranking の core を `legacy/` と `src/` に分断したままにしないため、残りを `src/` 側へ取り込む必要があります。

残っていた主な差分は次です。

- coalition-scope の synthetic ranking rule
- それらに対応する rankings CSV serializer
- coalition-ranking 用の axiom evaluator

## Decision

repository は `src/` 側の core を拡張し、次を取り込みます。

- legacy synthetic の全 ranking rule
- player / coalition の両方を表現できる scope-aware な ranking result model
- synthetic rule 群全体に対する compatibility-format serializer
- `src/srs_calculation/domain/axioms` 配下の coalition-ranking axiom evaluator
- application 層の axiom evaluation use case

この判断は、archive-only の axiom CLI command を root 契約へ公開することまでは意味しません。

## Consequences

Positive:

- `src/` に legacy synthetic の ranking core 全体が入り、初回バッチだけの状態を脱する
- real-data / synthetic workflow が同じ rule registry を共有できる
- axiom ロジックが retained archive にしか無い状態を解消できる

Negative:

- player / coalition の両方を表すため ranking result model は少し複雑になる
- `ud` / `du` のような compatibility special case を serializer が持つ必要がある

Operational:

- 拡張後の registry surface を test で保護する必要がある
- docs では「移行済み axiom core」と「archive-only の axiom CLI」を明確に分ける必要がある

## Related documents

- [`../specs/legacy-ranking-and-axiom-completion.md`](../specs/legacy-ranking-and-axiom-completion.md)
- [`0001-ranking-domain-foundation.md`](0001-ranking-domain-foundation.md)
