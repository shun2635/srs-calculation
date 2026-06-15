# 仕様書: legacy ranking / axiom core の完了移行

## Summary

この spec は、最初の ranking-domain foundation を拡張し、legacy synthetic に存在した ranking rule 全体と coalition-ranking 用の axiom evaluator を `src/` 側へ移す移行スライスを定義します。

## Goals

- legacy synthetic の全 ranking rule を `src/` へ移す
- player-scope と coalition-scope の両方を共通の domain result model で扱えるようにする
- 拡張後の rule 群に対しても compatibility-format rankings CSV を維持する
- coalition-ranking 用の axiom evaluator を `src/domain/axioms` へ移す
- root CLI 契約は維持し、archive-only の axiom command は公開しない

## 対象

- `legacy/src/gamegen/rules/` にある残りの synthetic rule
- serialzed base `rank` を保持できるようにする `CoalitionGame`
- coalition-scope rule に対応する compatibility-format rankings CSV serializer
- coalition-scoped ranking result に対する application 層の公理評価
- 拡張後の rule registry / axiom registry を検証する test

## 対象外

- `check-axioms` などを root CLI の公開 command にすること
- archive-only の axiom figure command をサポート対象 workflow に戻すこと
- `legacy/` archive 自体の置き換え

## 移行する rule 群

player-scope:

- `shapley`
- `banzhaf`
- `lexcel`
- `ordinal_banzhaf`

coalition-scope:

- `group_shapley`
- `group_sum_shapley`
- `group_ordinal_banzhaf`
- `group_lexcel`
- `shapley_interaction`
- `banzhaf_interaction`
- `rp_index`
- `ud`
- `du`
- `red_index`

## 移行する axiom 群

- `reversal-2p`
- `reversal-weak-n`
- `give-2p`
- `take-2p`
- `give-weak-n`
- `take-weak-n`
- `redundancy`

## 設計メモ

- player-scope と coalition-scope は、scope 情報を持つ score/rank set を通じて単一の `RankingResult` 形に載せる
- base `rank` 列に依存する coalition rule は `CoalitionGame.base_ranks_by_mask` を通じて読む
- compatibility-format の列名は serialization 境界の責務であり、domain では持ち込まない
- `ud` / `du` の `score_*_up` / `score_*_down` は serializer 側の special case として維持する

## Testing plan

- 既存の first-batch parity test は維持する
- 全 rule set を対象にした registry / integration test を追加する
- 移行した axiom evaluator に対する registry / application test を追加する
- root Poetry test suite を通す

## Related documents

- [`ranking-domain-foundation.md`](ranking-domain-foundation.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md`](../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md)
