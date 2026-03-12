# srs-calculation

Repository for cooperative-game-based ranking experiments, synthetic game generation, axiom checking, and real-data analysis.

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).

このリポジトリは、協力ゲームに基づくランキング計算、合成ゲーム生成、公理チェック、実データ解析を扱う研究用コードベースです。サポート対象の Poetry project はリポジトリ root にあり、`srs-real-gen` と `srs-game-gen` は [`src/`](src/) の CLI に接続されています。[`legacy/`](legacy/) は履歴資料として保持する archive であり、[`docs/`](docs/) にはその方針と境界を整理しています。

## Intended audiences

- CMIS Lab, The University of Tokyo: 日本語の入口は [`docs/ja/README.md`](docs/ja/README.md)
- LAMSADE collaborators: English overview is in [`docs/en/README.md`](docs/en/README.md)

Note: the Japanese and English audience guides are intended to stay content-synchronized. When one is updated, the other should be reviewed and updated as needed.

## Current repository status

- The root Poetry project now publishes the `src`-based `srs-real-gen` CLI.
- The `src/` tree is now the implementation of record for supported workflows.
- The `legacy/` tree remains under [`legacy/`](legacy/) as a retained archive of historical code, commands, and design notes.
- The new top-level [`docs/`](docs/) directory is the recommended entry point for collaborators.
- The top-level [`src/`](src/) directory now contains the implementation of record for supported workflows.
- The `src/` tree already exposes module-entry CLIs for migrated synthetic and real-data slices.
- The existing [`legacy/docs/`](legacy/docs/) directory remains the detailed technical archive for ranking rules, axioms, and design notes.

## What the code currently does

### `game-gen`

The synthetic-game pipeline supports:

- generation of all-coalition game tables
- computation of ranking columns for multiple rules
- batch axiom checking
- production of heatmaps and summary figures

### `srs-real-gen`

The real-data pipeline supports:

- importing feature-mask performance tables into a coalition-game format
- reusing the ranking rules from `gamegen`
- generating dataset-specific figures and heatmaps

## Repository layout

- [`docs/`](docs/): curated entry-point documentation for collaborators
- [`src/`](src/): implementation of record for supported workflows
- [`legacy/`](legacy/): archive of historical code, commands, and design notes
- [`legacy/src/gamegen`](legacy/src/gamegen): synthetic game generation, ranking, axioms, visualization
- [`legacy/src/realgen`](legacy/src/realgen): real-data import, rule application, visualization
- [`legacy/docs/`](legacy/docs/): detailed design notes and mathematical rule descriptions
- [`legacy/tests/`](legacy/tests/): regression tests for CLI and ranking behavior

## Quick start

```bash
poetry install
poetry run srs-real-gen --help
poetry run srs-game-gen --help
poetry run srs-test
```

## Authoritative Root CLI Contract

root [`pyproject.toml`](pyproject.toml) が、共同研究向けにサポートする公開 CLI 契約の正本です。移行中でも script 名は次で固定します。

- `srs-real-gen`
- `srs-game-gen`
- `srs-test`

サポート対象コマンドは次です。

- `srs-real-gen import-game`
- `srs-real-gen apply-rules`
- `srs-real-gen make-figures`
- `srs-real-gen feature-rule-heatmap`
- `srs-game-gen gen-games`
- `srs-game-gen apply-rules`
- `srs-game-gen make-figures`
- `srs-game-gen rank-game`
- `srs-game-gen rank-heatmap`
- `srs-game-gen rule-corr-heatmap`

archive-only として `legacy/` 側に閉じる旧コマンドは、root CLI 契約には含めません。

- `game-gen check-axioms`
- `game-gen summarize-axioms`
- `game-gen axiom-summary-heatmap`
- `game-gen pipeline`
- `game-gen make-figures-png`
- `legacy/src/realgen/commands/resignation_contrib.py` 相当の未公開コマンド

これらは `src/` への通常の移行対象ではなく、archive behavior として扱います。通常運用では root CLI を先に見てください。

互換境界に関する補足:

- `player*`, `score`, `rank`, `rank_*`, `score_*` を使う歴史的な CSV 命名は、`src` 側の compatibility format として維持しています
- その責務は [`src/srs_calculation/infrastructure/persistence/`](src/srs_calculation/infrastructure/persistence/) に閉じ込めています
- これは `legacy/` パッケージへの runtime 依存ではありません

設定の優先順位は共通で次です。

1. コマンド引数
2. `--config` で指定した YAML
3. コード内の組み込み既定値

補足:

- root CLI は `legacy/config.yaml` を暗黙には読みません
- root CLI は repository root の `./config.yaml` も自動探索しません
- YAML 設定を使う場合は、必ず `--config <path>` を明示してください

root CLI で現在使う主要設定キー:

- `output_base`: 出力ルート。既定は `outputs`
- `figures.png_dpi`: PNG 出力 DPI。既定は `150`
- `realgen.import_rank_bins`: `srs-real-gen import-game` の `rank_method: binned` で使う分割数

`srs-real-gen import-game` では各データセットの `schema.yaml` が必須です。主な schema キー:

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
| `poetry run srs-real-gen import-game <dataset_id>` | `realgen.import_rank_bins`, `inputs/feature_mask_tables/<dataset_id>/schema.yaml` | `outputs/real/<dataset_id>/games/game_<dataset_id>.csv`、`game_<dataset_id>.features.yaml`、`schema.yaml` のコピーを生成 |
| `poetry run srs-real-gen apply-rules <dataset_id>` | dataset `schema.yaml` の `rules` または migrated rule defaults | `outputs/real/<dataset_id>/rankings/game_<dataset_id>.csv` を生成または更新。`rank_*` や `score_*` 列を追加 |
| `poetry run srs-real-gen make-figures <dataset_id>` | dataset `schema.yaml` の `figures.*` | `outputs/real/<dataset_id>/figures/*.png` を生成。基本の ranking 図に加えて、interaction index, red-index, shapley values, ordinal banzhaf values, lexcel rank count, give top-k などの extra figure を best-effort で生成 |
| `poetry run srs-real-gen feature-rule-heatmap <dataset_id>` | dataset `schema.yaml` の `heatmaps.feature_rule_max_coalition_size` | `outputs/real/<dataset_id>/heatmaps/feature_rule_rank.png` を生成 |

補足:

- `legacy/src/realgen/commands/resignation_contrib.py` は実装ファイルがありますが、現時点では `srs-real-gen` CLI に登録されていないため `poetry run srs-real-gen ...` では呼べません
- archive-only command examples are collected in [`legacy/README.md`](legacy/README.md)

## `src` CLI

`src/` 側 CLI は module 実行でも叩けます。`srs-real-gen` と `srs-game-gen` は root Poetry project から呼ぶのが標準です。

```bash
poetry run srs-real-gen --help
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
- `srs-game-gen make-figures`: synthetic rankings CSV から compatibility-format PNG figure を `outputs/figures/nN/` に生成する
- `srs-game-gen apply-rules`: compatibility-format game CSV ディレクトリに対して migrated rules を適用する
- `srs-game-gen rank-game`: compatibility-format game CSV 1 件に対して migrated rule 1 つを適用する
- `srs-game-gen rank-heatmap`: synthetic rankings CSV から pairwise rank heatmap を `outputs/heatmaps/nN/` に生成する
- `srs-game-gen rule-corr-heatmap`: synthetic rankings CSV から rule-rank correlation heatmap を `outputs/heatmaps/nN/` に生成する
- `srs-real-gen import-game`: feature-mask table を dataset-scoped な game CSV と `features.yaml` に変換する
- `srs-real-gen apply-rules`: dataset-scoped な `outputs/real/<dataset_id>/games/` に対して migrated rules を適用する
- `srs-real-gen make-figures`: dataset-scoped な rankings CSV から canonical table-style PNG と extra figure 群を best-effort で生成する
- `srs-real-gen feature-rule-heatmap`: feature × rule の rank heatmap を生成する

`srs-real-gen` は root から公開されています。`srs-game-gen` は `gen-games`, `make-figures`, `apply-rules`, `rank-game`, `rank-heatmap`, `rule-corr-heatmap` を root でサポートしますが、旧 `game-gen` 全機能はまだ移行していません。`legacy/` は参照用に残っていますが、root CLI 契約の正本ではありません。

互換メモ:

- `real-gen` は既存利用者向けの compatibility alias として残しています
- root docs では並列な命名である `srs-real-gen` / `srs-game-gen` を正本として使います

### Minimal `srs-game-gen` examples

```bash
# Generate synthetic games
poetry run srs-game-gen gen-games -p 4 -c 100 --out outputs

# Apply migrated ranking rules
poetry run srs-game-gen apply-rules -p 4 --out outputs

# Render ranking figures
poetry run srs-game-gen make-figures --rankings-dir outputs/rankings --out outputs

# Render pairwise rank heatmaps
poetry run srs-game-gen rank-heatmap -p 4 --rankings-dir outputs/rankings --out outputs

# Render rule-rank correlation heatmaps
poetry run srs-game-gen rule-corr-heatmap -p 4 --rankings-dir outputs/rankings --out outputs
```

## Documentation map

- [`docs/ja/README.md`](docs/ja/README.md): Japanese documentation hub
- [`docs/en/README.md`](docs/en/README.md): English documentation hub
- [`docs/en/architecture.md`](docs/en/architecture.md): historical architecture snapshot of the archived `legacy/` tree
- [`docs/en/architecture/README.md`](docs/en/architecture/README.md): target architecture documents for the new implementation
- [`docs/en/development/README.md`](docs/en/development/README.md): collaboration and development standards
- [`docs/en/adr/README.md`](docs/en/adr/README.md): architectural decision records
- [`docs/en/specs/README.md`](docs/en/specs/README.md): feature/specification documents
- [`docs/en/research-workflow.md`](docs/en/research-workflow.md): how to use the repository in research collaboration
- [`src/README.md`](src/README.md): implementation-of-record package structure and CLI surface
- [`legacy/README.md`](legacy/README.md): archive-only CLI reference for historical commands

## Practical note

The repository now treats the root Poetry project as the authoritative executable surface for supported workflows. `src/` is the implementation of record, and `legacy/` is intentionally retained as a historical archive for commands, mathematical notes, and design context.

## Migration progress

The repository has already completed the main decoupling work needed to keep the supported root workflows independent from `legacy/`.

- root CLI contract is fixed in this README and [`src/README.md`](src/README.md)
- collaborator-facing docs no longer require `legacy/` for normal operation
- parity tests use frozen fixtures instead of importing `legacy`
- compatibility-format CSV handling is isolated inside [`src/srs_calculation/infrastructure/persistence/`](src/srs_calculation/infrastructure/persistence/)
- `legacy/config.yaml` is no longer part of the root CLI lookup path
- `poetry run srs-verify-no-legacy` exists to verify that root CLI workflows still run when `legacy/` is hidden
- `legacy/` is now documented as a retained historical archive, not a supported execution surface

## Testing

Use the root Poetry environment for `src`-based tests.

```bash
poetry install
poetry run srs-test
poetry run srs-verify-no-legacy
```

You can also forward normal pytest arguments:

```bash
poetry run srs-test tests/unit -q
poetry run srs-test tests/integration/application/ranking/test_apply_ranking_rules.py
```

`poetry run srs-verify-no-legacy` temporarily hides the `legacy/` directory, runs the root CLI help commands, runs the full root test suite, and then restores `legacy/`.
