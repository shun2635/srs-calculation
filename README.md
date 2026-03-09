# srs-calculation

Repository for cooperative-game-based ranking experiments, synthetic game generation, axiom checking, and real-data analysis.

このリポジトリは、協力ゲームに基づくランキング計算、合成ゲーム生成、公理チェック、実データ解析を扱う研究用コードベースです。次実装の Poetry project はリポジトリ root にあり、`real-gen` は [`src/`](src/) の CLI に接続されています。[`legacy/`](legacy/) は参照実装として残し、[`docs/`](docs/) にはその方針と境界を整理しています。

## Intended audiences

- CMIS Lab, The University of Tokyo: 日本語の入口は [`docs/ja/README.md`](docs/ja/README.md)
- LAMSADE collaborators: English overview is in [`docs/en/README.md`](docs/en/README.md)

Note: the Japanese and English audience guides are intended to stay content-synchronized. When one is updated, the other should be reviewed and updated as needed.

## Current repository status

- The root Poetry project now publishes the `src`-based `real-gen` CLI.
- The legacy Poetry project remains under [`legacy/`](legacy/) for reference and still carries the old `game-gen` / `real-gen` scripts.
- The new top-level [`docs/`](docs/) directory is the recommended entry point for collaborators.
- The new top-level [`src/`](src/) directory already contains the in-progress next implementation.
- The `src/` tree already exposes module-entry CLIs for migrated `game-gen` and `real-gen` slices.
- The existing [`legacy/docs/`](legacy/docs/) directory remains the detailed technical archive for ranking rules, axioms, and design notes.

## What the code currently does

### `game-gen`

The synthetic-game pipeline supports:

- generation of all-coalition game tables
- computation of ranking columns for multiple rules
- batch axiom checking
- production of heatmaps and summary figures

### `real-gen`

The real-data pipeline supports:

- importing feature-mask performance tables into a coalition-game format
- reusing the ranking rules from `gamegen`
- generating dataset-specific figures and heatmaps

## Repository layout

- [`docs/`](docs/): curated entry-point documentation for collaborators
- [`src/`](src/): in-progress next implementation
- [`legacy/`](legacy/): current Poetry project and implementation
- [`legacy/src/gamegen`](legacy/src/gamegen): synthetic game generation, ranking, axioms, visualization
- [`legacy/src/realgen`](legacy/src/realgen): real-data import, rule application, visualization
- [`legacy/docs/`](legacy/docs/): detailed design notes and mathematical rule descriptions
- [`legacy/tests/`](legacy/tests/): regression tests for CLI and ranking behavior

## Quick start

```bash
poetry install
poetry run real-gen --help
poetry run srs-game-gen --help
poetry run srs-test
```

## Authoritative Root CLI Contract

root [`pyproject.toml`](pyproject.toml) が、共同研究向けにサポートする公開 CLI 契約の正本です。移行中でも script 名は次で固定します。

- `real-gen`
- `srs-game-gen`
- `srs-test`

サポート対象コマンドは次です。

- `real-gen import-game`
- `real-gen apply-rules`
- `real-gen make-figures`
- `real-gen feature-rule-heatmap`
- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen make-figures`
- `srs-game-gen rank-game`

保留または未サポートの旧コマンドは、root CLI 契約には含めません。

- `game-gen check-axioms`
- `game-gen summarize-axioms`
- `game-gen axiom-summary-heatmap`
- `game-gen rank-heatmap`
- `game-gen rule-corr-heatmap`
- `game-gen pipeline`
- `game-gen make-figures-png`
- `legacy/src/realgen/commands/resignation_contrib.py` 相当の未公開コマンド

`legacy/` は参照用に残していますが、通常運用では root CLI を先に見てください。

設定の優先順位は共通で次です。

1. コマンド引数
2. `--config` で指定した YAML
3. コード内の組み込み既定値

root CLI で現在使う主要設定キー:

- `output_base`: 出力ルート。既定は `outputs`
- `figures.png_dpi`: PNG 出力 DPI。既定は `150`
- `realgen.import_rank_bins`: `real-gen import-game` の `rank_method: binned` で使う分割数

`real-gen import-game` では各データセットの `schema.yaml` が必須です。主な schema キー:

- `raw_csv`
- `score_column`
- `score_transform`
- `rank_column`
- `rank_method`
- `feature_columns`
- `feature_exclude`
- `filters`
- `empty_score`
- `empty_rank`
- `allow_incomplete`
- `rules`
- `heatmaps.feature_rule_max_coalition_size`
- `figures.*`

| コマンド | 設定 | 何がどこに生成されるか |
| --- | --- | --- |
| `poetry run real-gen import-game <dataset_id>` | `realgen.import_rank_bins`, `inputs/feature_mask_tables/<dataset_id>/schema.yaml` | `outputs/real/<dataset_id>/games/game_<dataset_id>.csv`、`game_<dataset_id>.features.yaml`、`schema.yaml` のコピーを生成 |
| `poetry run real-gen apply-rules <dataset_id>` | dataset `schema.yaml` の `rules` または migrated rule defaults | `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv` を生成または更新。`rank_*` や `score_*` 列を追加 |
| `poetry run real-gen make-figures <dataset_id>` | dataset `schema.yaml` の `figures.*` | `outputs/real/<dataset_id>/figures/*.png` を生成。基本の ranking 図に加えて、interaction index, red-index, shapley values, ordinal banzhaf values, lexcel rank count, give top-k などの extra figure を best-effort で生成 |
| `poetry run real-gen feature-rule-heatmap <dataset_id>` | dataset `schema.yaml` の `heatmaps.feature_rule_max_coalition_size` | `outputs/real/<dataset_id>/heatmaps/feature_rule_rank.png` を生成 |

補足:

- `legacy/src/realgen/commands/resignation_contrib.py` は実装ファイルがありますが、現時点では `real-gen` CLI に登録されていないため `poetry run real-gen ...` では呼べません
- 詳細な CLI 用例は [`legacy/README.md`](legacy/README.md) を参照してください

## `src` CLI

`src/` 側 CLI は module 実行でも叩けます。`real-gen` と `srs-game-gen` は root Poetry project から呼ぶのが標準です。

```bash
poetry run real-gen --help
poetry run srs-game-gen --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen make-figures --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen apply-rules --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen rank-game --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen import-game --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen apply-rules --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen make-figures --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen feature-rule-heatmap --help
```

現時点で root CLI 契約に含めているのは次です。

- `srs-game-gen gen-games`: complete synthetic game CSV を `outputs/games/nN/` に生成する
- `srs-game-gen make-figures`: synthetic rankings CSV から legacy-style PNG figure を `outputs/figures/nN/` に生成する
- `srs-game-gen apply-rules`: legacy-style game CSV ディレクトリに対して migrated rules を適用する
- `srs-game-gen rank-game`: legacy-style game CSV 1 件に対して migrated rule 1 つを適用する
- `real-gen import-game`: feature-mask table を dataset-scoped な game CSV と `features.yaml` に変換する
- `real-gen apply-rules`: dataset-scoped な `outputs/real/<dataset_id>/games/` に対して migrated rules を適用する
- `real-gen make-figures`: dataset-scoped な rankings CSV から canonical table-style PNG と extra figure 群を best-effort で生成する
- `real-gen feature-rule-heatmap`: feature × rule の rank heatmap を生成する

`real-gen` は root から公開されています。`srs-game-gen` は `gen-games`, `make-figures`, `apply-rules`, `rank-game` を root でサポートしますが、旧 `game-gen` 全機能はまだ移行していません。`legacy/` は参照用に残っていますが、root CLI 契約の正本ではありません。

## Documentation map

- [`docs/ja/README.md`](docs/ja/README.md): Japanese documentation hub
- [`docs/en/README.md`](docs/en/README.md): English documentation hub
- [`docs/en/architecture.md`](docs/en/architecture.md): current legacy-centered code and pipeline overview
- [`docs/en/architecture/README.md`](docs/en/architecture/README.md): target architecture documents for the new implementation
- [`docs/en/development/README.md`](docs/en/development/README.md): collaboration and development standards
- [`docs/en/adr/README.md`](docs/en/adr/README.md): architectural decision records
- [`docs/en/specs/README.md`](docs/en/specs/README.md): feature/specification documents
- [`docs/en/research-workflow.md`](docs/en/research-workflow.md): how to use the repository in research collaboration
- [`src/README.md`](src/README.md): intended package structure for new code
- [`legacy/README.md`](legacy/README.md): CLI-oriented reference for the legacy implementation

## Practical note

The repository now treats the root Poetry project as the authoritative executable surface for supported workflows. `legacy/` remains only as a reference implementation and archive candidate.

## Testing

Use the root Poetry environment for `src`-based tests.

```bash
poetry install
poetry run srs-test
```

You can also forward normal pytest arguments:

```bash
poetry run srs-test tests/unit -q
poetry run srs-test tests/integration/application/ranking/test_apply_ranking_rules.py
```
