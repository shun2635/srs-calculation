# ADR-0003: synthetic の順位相関 command を root CLI に戻す

## Status

Accepted

## Context

ADR-0002 では、repository が `legacy/` から切り離される途中段階だったため、historical な synthetic command 群を広めに root CLI 契約の外へ出しました。

当時の判断自体は妥当でしたが、`rank-heatmap` と `rule-corr-heatmap` は full な historical synthetic surface よりもずっと限定的です。

- 論文や研究メモで直接使う分析 command である
- すでに `src/` に移行済みの rankings CSV workflow の上で動く
- archive-only の axiom 系や pipeline 系 command を前提にしない
- method が十分安定しており、サポート対象仕様として明文化できる

同時に現在の repository には次があります。

- root から公開された `srs-game-gen` CLI
- 論文向けの synthetic methodology spec
- 移行済み synthetic workflow に対する integration / e2e test

## Decision

次の command を、サポート対象の root `srs-game-gen` surface に戻します。

- `rank-heatmap`
- `rule-corr-heatmap`

実装は `src/` 側に置き、root CLI 契約の一部として公開します。

移植後の挙動では、historical な method の中核を維持します。

- serialize 済みの `rank_*` 列を effective な competition-style rank に変換する
- player-scope rule は singleton 行で評価する
- coalition-scope rule は空連合を除く coalition 行で評価する
- rule 間相関行列は `pandas.DataFrame.corr(method=...)` で計算する
- 相関 method の既定値は `spearman` を維持する

この判断は、ADR-0002 で archive-only にした残りの command を再度公開するものではありません。次は引き続き archive-only のままです。

- `check-axioms`
- `summarize-axioms`
- `axiom-summary-heatmap`
- `pipeline`
- `make-figures-png`

## Consequences

Positive:

- root がサポートする synthetic workflow だけで、研究で使う主要な順位比較分析まで完結する
- 論文中で順位相関分析を説明する際に、読者を `legacy/` へ戻さなくてよくなる
- historical な synthetic surface 全体を復活させずに、必要なところだけ `src/` へ取り戻せる

Negative:

- ADR-0002 は `rank-heatmap` と `rule-corr-heatmap` については最新判断ではなくなる
- `src/` 側で追加の plotting behavior を保守する責務が増える

Operational:

- root README と共同研究者向け docs に、この 2 command をサポート対象として明記する必要がある
- synthetic methodology docs に、移植後の順位相関 method を明記する必要がある
- この 2 command に対する integration / e2e test を維持する必要がある

## Alternatives considered

### 2 command とも archive-only のままにする

不採用。用途が限定的で有用であり、すでに移行済み rankings workflow と自然につながるためです。

### 廃止した synthetic command をすべて root へ戻す

不採用。必要以上に大きな migration surface を再び開いてしまうためです。

### 片方だけ戻す

不採用。pairwise な rank heatmap と rule-correlation heatmap は同じ rankings 出力に対する補完的な可視化だからです。

## Related documents

- [`0002-retire-legacy-only-synthetic-commands.md`](0002-retire-legacy-only-synthetic-commands.md)
- [`../specs/synthetic-game-methodology.md`](../specs/synthetic-game-methodology.md)
- [`../architecture/legacy-removal-runbook.md`](../architecture/legacy-removal-runbook.md)
- [`../../../README.md`](../../../README.md)
