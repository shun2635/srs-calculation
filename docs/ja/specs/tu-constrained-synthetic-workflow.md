# 仕様書: 制約付き synthetic ranking workflow

## Summary

この spec は、現在の制約なし synthetic game 生成に加えて、`v(∅)=0`、超加法性、単調性を含む TU 条件付き生成を `src/` 側 workflow に追加し、その生成物に対する ranking rule 適用結果を公理適合率と順位相関の両面から比較できるようにする変更を定義します。

初期スコープでは、`unconstrained` に加えて、複数条件を重ねがけできる constraint-set 方式を導入します。最初にサポートする constraint は `empty_zero`、`superadditive`、`monotone` で、`tu` はこの 3 条件を束ねた shorthand profile として扱います。出力ディレクトリ・CLI・分析 artefact は constraint-set aware に整理し、将来の制約付き generator を増やしやすいように、生成設定と synthetic output path 解決もリファクタ対象に含めます。

## Problem

現状の root synthetic workflow には次の問題があります。

- `gen-games` は「制約なしの complete cooperative game」を 1 種類しか生成できず、TU 条件付きサンプルや今後の複合制約サンプルとの比較実験ができない
- synthetic output は `games/nN`, `rankings/nN`, `heatmaps/nN` という固定構造で、生成条件ごとの共存を前提にしていない
- `src/` 側には公理評価 core はあるが、synthetic ranking workflow からルール別・公理別の適合率を集計し、PNG heatmap まで出す公開導線がない
- `rule-corr-heatmap` は PNG を出せる一方、constraint set 比較に使いやすい machine-readable な summary を標準出力していない

このため、「制約なし生成」と「TU 条件付き生成」で同じ rule 群を比較し、公理適合率や順位相関がどう変わるかを系統的に追えません。

## Goals

- synthetic game 生成に constraint-set を導入し、複数条件を重ねがけできるようにする
- 初回サポートとして `empty_zero`, `superadditive`, `monotone` を実装し、`tu` shorthand で指定できるようにする
- constraint set ごとに games / rankings / figures / heatmaps / analysis を分離保存できるようにする
- ranking rule 適用後の coalition-scope と individual-scope の両方について、公理適合率を `src/` workflow から集計できる拡張点を用意する
- rule correlation について、既存 PNG に加えて summary CSV を出力できるようにする
- 公理比較の PNG heatmap を root synthetic workflow に含める
- 将来 `convex` などの追加制約を載せやすい構造へ寄せる

## Non-goals

- 初回実装で任意制約を表現する DSL や constraint solver を導入すること
- archive-only の axiom example PNG 生成や full legacy pipeline をそのまま root CLI に戻すこと
- individual-scope 公理の具体的な数理定義をこの spec 単体で確定すること
- 論文本文に入れる結論や解釈をこの spec で固定すること

## Scope

対象:

- `src/srs_calculation/application/game_generation`
- `src/srs_calculation/application/ranking`
- `src/srs_calculation/application/axiom_evaluation`
- `src/srs_calculation/application/experiments`
- `src/srs_calculation/interfaces/cli/game_gen.py`
- synthetic output path を解決する周辺 helper
- `docs/ja` / `docs/en` の synthetic workflow 文書
- synthetic workflow に関する unit / integration / e2e test

対象外:

- `legacy/` archive の削除
- 実データ workflow (`srs-real-gen`) の挙動変更

## Proposed design

### 1. 生成条件を constraint set として first-class にする

`generate_synthetic_games(...)` の暗黙仕様を、次のような明示設定へ置き換えます。

- `constraints`: `tuple[str, ...]`
- `players`
- `count`
- `max_score`
- `seed`
- `out_dir`

内部では constraint set ごとに generator strategy を切り替えます。

- `unconstrained`: 制約なし。現行どおり全 coalition mask に値を割り当てる
- `empty_zero`: `v(∅)=0`
- `monotone`: `S ⊆ T` なら `v(S) <= v(T)`
- `superadditive`: `S ∩ T = ∅` なら `v(S ∪ T) >= v(S) + v(T)`
- `tu`: shorthand profile。`empty_zero + monotone + superadditive`

初回実装では profile 展開後の正規化済み constraint set を canonical とし、出力 path や metadata には正規化後の set を使います。

制約を複数重ねる以上、generator は「iid に生成してから reject」よりも、制約を保ったまま構成的に値を作る方針を優先してよいです。実装は任意ですが、少なくとも次を満たします。

- `empty_zero` は空連合の値を常に 0 にする
- `monotone` と `superadditive` が有効なとき、それぞれの不等式違反を生まない
- `tu` は上記 3 条件をすべて満たす

### 2. constraint-set aware な synthetic output layout に整理する

拡張性を優先し、synthetic artefact の canonical layout を次に寄せます。

- `outputs/synthetic/<constraint_set_id>/games/nN/game_*.csv`
- `outputs/synthetic/<constraint_set_id>/rankings/nN/game_*.csv`
- `outputs/synthetic/<constraint_set_id>/figures/nN/game_*.png`
- `outputs/synthetic/<constraint_set_id>/heatmaps/nN/*.png`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/rule_corr_player.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/rule_corr_coalition.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/coalition/<axiom_id>/<rule>.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/coalition/summary.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/coalition/summary_heatmap.png`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/individual/<axiom_id>/<rule>.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/individual/summary.csv`
- `outputs/synthetic/<constraint_set_id>/analysis/nN/axiom/individual/summary_heatmap.png`

`constraint_set_id` は正規化済み制約集合から決まる決定的な slug です。例:

- `unconstrained`
- `empty_zero+monotone`
- `empty_zero+monotone+superadditive`

この変更に合わせて、現在 CLI 内に散在している path 解決ロジックを 1 箇所へ寄せます。想定する責務は次です。

- `constraints`, `players`, `out_dir` から canonical path 群を返す
- `--games-dir` / `--rankings-dir` 明示時は canonical path を上書きできる
- constraint-set aware path を `gen-games`, `apply-rules`, `make-figures`, `rank-heatmap`, `rule-corr-heatmap`, `evaluate-axioms`, `axiom-summary-heatmap` で共有する

互換 path は残しません。既存の `outputs/games`, `outputs/rankings`, `outputs/heatmaps`, `outputs/axiom` を canonical path から外し、docs / CLI / test も新構造へ一本化します。

### 3. 公理評価 workflow を root synthetic surface に追加する

`src/` には `evaluate_axioms_for_results(...)` があるため、synthetic rankings CSV を対象にした集計 command を新設します。

推奨 surface:

- `srs-game-gen evaluate-axioms --players N --constraint <id>...`
- `srs-game-gen axiom-summary-heatmap --players N --constraint <id>... --scope coalition|individual`

責務:

- `rankings` と対応する `games` を読み込む
- coalition-scope と individual-scope の rule を scope ごとに分けて評価する
- 1 game ごとの counts CSV を `analysis/nN/axiom/<scope>/<axiom_id>/<rule>.csv` に書く
- aggregate summary を `analysis/nN/axiom/<scope>/summary.csv` に書く
- root workflow の artefact として `summary_heatmap.png` を出せるようにする

summary CSV の列は legacy と揃えます。

- `rule`
- `axiom`
- `constraints`
- `satisfied`
- `satisfied_rate`

individual-scope 公理は後続仕様で定義される前提なので、初回実装では次の形にしてよいです。

- CLI / path / registry の拡張点は先に用意する
- individual 用 registry が空なら `no axioms evaluated for scope=individual` を返す
- concrete axiom が渡された後で evaluator を追加する

PNG heatmap は root workflow に含めます。実装方式は次のどちらでもよいです。

- `evaluate-axioms` 実行時に summary CSV と summary heatmap を同時生成する
- `evaluate-axioms` で CSV を作り、`axiom-summary-heatmap` で再描画可能にする

再計算コストと再描画用途を考えると、両方の command を持つのが素直です。

### 4. rule correlation を PNG だけでなく CSV でも残す

既存の `rule-corr-heatmap` は内部で相関行列を計算しています。これを summary artefact として保存できるようにします。

- `analysis/nN/rule_corr_player.csv`
- `analysis/nN/rule_corr_coalition.csv`

`rule-corr-heatmap` はこの summary を利用して PNG を描く形に寄せてもよいし、同一計算結果を CSV と PNG に同時出力してもよいです。重要なのは、constraint set 間比較に使える数値 artefact を標準で残すことです。

### 5. 既存 heatmap / figure workflow は constraint-set aware に保つ

`apply-rules`, `make-figures`, `rank-heatmap`, `rule-corr-heatmap` は `--constraint` を受け取り、明示ディレクトリ指定が無い場合は同じ constraint-set root を見るようにします。

最小 CLI 案:

- `srs-game-gen gen-games --constraint empty_zero --constraint monotone --constraint superadditive`
- `srs-game-gen gen-games --profile tu`
- `srs-game-gen apply-rules --constraint ...`
- `srs-game-gen make-figures --constraint ...`
- `srs-game-gen rank-heatmap --constraint ...`
- `srs-game-gen rule-corr-heatmap --constraint ...`
- `srs-game-gen evaluate-axioms --constraint ...`
- `srs-game-gen axiom-summary-heatmap --constraint ... --scope coalition|individual`

### 6. リファクタ方針

今回の変更では、次の 2 点を先に分離するのが妥当です。

- `SyntheticOutputLayout` のような constraint-set aware path resolver
- `SyntheticGenerationSpec` / `SyntheticGenerator` のような生成条件オブジェクト
- `ConstraintSet` / `ConstraintProfile` の正規化 helper

これにより、`gen-games` の条件分岐を CLI に漏らさずに済み、将来 constraint が増えても path 規約と generator 実装を局所変更で済ませやすくなります。

## Data and interfaces

### CLI

新規 / 変更される公開引数:

- `--constraint <id>` の複数指定
- `--profile tu`
- `evaluate-axioms` command の追加
- `axiom-summary-heatmap` command の追加

`--games-dir` / `--rankings-dir` を明示した場合は、constraint-aware canonical path よりそちらを優先します。

### Config

`gen_games` 設定に constraint set を追加できるようにします。

例:

```yaml
output_base: outputs
gen_games:
  profile: tu
  count: 100
  max_score: 31
  seed: 7
```

将来拡張を見越して、constraint 固有設定は別節へ逃がせる形にしてよいです。

```yaml
synthetic:
  constraints:
    - empty_zero
    - monotone
    - superadditive
  profiles:
    tu:
      expands_to:
        - empty_zero
        - monotone
        - superadditive
```

初回実装ではここまで複雑にしなくてもよいですが、`tu` が `gen_games` の一時的 special case で固定化しないようにします。

### CSV contracts

新規 summary CSV:

- `analysis/nN/rule_corr_player.csv`
- `analysis/nN/rule_corr_coalition.csv`
- `analysis/nN/axiom/coalition/summary.csv`
- `analysis/nN/axiom/coalition/summary_heatmap.png`
- `analysis/nN/axiom/individual/summary.csv`
- `analysis/nN/axiom/individual/summary_heatmap.png`

per-game axiom CSV:

- header: `game,constraints,satisfied,satisfied_rate`

rule correlation CSV:

- 行列形式のヘッダ付き CSV
- index / column は `rank_*` 列名をそのまま使う
- 値は `pandas.DataFrame.corr(method=...)` と同じ定義にする

game CSV 自体の列構造は変えません。constraint set の違いは path と生成方法で表現し、既存 serializer 互換を維持します。

## Migration plan

### 推奨実装順

1. constraint-set aware output layout resolver を追加し、既存 synthetic command をそこへ寄せる
2. `ConstraintSet` / `profile` 正規化を追加し、`gen-games --constraint` を導入する
3. `empty_zero`, `monotone`, `superadditive` を満たす generator を追加する
4. `evaluate-axioms` と `axiom-summary-heatmap` を追加する
5. `rule-corr-heatmap` に CSV summary 出力を追加する
5. docs と e2e workflow を更新する

### 互換性方針

canonical path は `outputs/synthetic/<constraint_set_id>/...` へ一本化します。

既存 path 互換は残しません。旧 path を参照する docs / tests / help text も同時に更新し、root synthetic workflow の正規導線を 1 つにします。

## Testing plan

- unit: constraint normalization が `profile=tu` を `empty_zero+monotone+superadditive` へ展開すること
- unit: constrained generator が `v(∅)=0`, monotonicity, superadditivity を満たすこと
- unit: constraint-set aware path resolver が各 artefact path を正しく返すこと
- integration: `apply-rules` が constraint-set aware directory を読んで rankings を出力すること
- integration: `evaluate-axioms` が expected header の CSV を出力すること
- integration: `axiom-summary-heatmap` が scope 別 PNG を出力すること
- integration: `rule-corr-heatmap` が PNG と CSV を両方出力すること
- e2e: `unconstrained` と `tu` を同じ `out` 配下で実行しても生成物が衝突しないこと
- e2e: `gen-games -> apply-rules -> evaluate-axioms -> rule-corr-heatmap` の比較導線が通ること

## Recommended implementation slices

- Slice 1: path resolver 導入と既存 synthetic CLI の constraint-set aware 化
- Slice 2: constraint normalization と TU 制約 generator
- Slice 3: 公理集計 command / summary CSV / summary heatmap
- Slice 4: rule correlation CSV と docs 更新

この順に切ると、途中段階でも `unconstrained` workflow を壊さずに前進しやすいです。

## Open questions

- individual-scope 公理の一覧、rule 対応表、summary heatmap 上の表示名をどう定義するか
- constraint-set slug の命名規則を `empty_zero+monotone+superadditive` のような展開形にするか、`tu` のような profile 名を優先するか

## Related documents

- [`synthetic-game-methodology.md`](synthetic-game-methodology.md)
- [`legacy-ranking-and-axiom-completion.md`](legacy-ranking-and-axiom-completion.md)
- [`../architecture/migration-from-legacy.md`](../architecture/migration-from-legacy.md)
- [`../adr/0003-reintroduce-synthetic-rank-correlation-commands.md`](../adr/0003-reintroduce-synthetic-rank-correlation-commands.md)
- [`../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md`](../adr/0004-complete-legacy-ranking-and-axiom-core-in-src.md)
