# srs-calculation

Repository for cooperative-game-based ranking experiments, synthetic game generation, axiom checking, and real-data analysis.

このリポジトリは、協力ゲームに基づくランキング計算、合成ゲーム生成、公理チェック、実データ解析を扱う研究用コードベースです。公開されている Poetry CLI は引き続き [`legacy/`](legacy/) にありますが、次の実装は [`src/`](src/) 配下で進行しており、[`docs/`](docs/) にはその方針と境界を整理しています。

## Intended audiences

- CMIS Lab, The University of Tokyo: 日本語の入口は [`docs/ja/README.md`](docs/ja/README.md)
- LAMSADE collaborators: English overview is in [`docs/en/README.md`](docs/en/README.md)

Note: the Japanese and English audience guides are intended to stay content-synchronized. When one is updated, the other should be reviewed and updated as needed.

## Current repository status

- The published Poetry CLI still lives in [`legacy/`](legacy/).
- The new top-level [`docs/`](docs/) directory is the recommended entry point for collaborators.
- The new top-level [`src/`](src/) directory already contains the in-progress next implementation.
- The `src/` tree already exposes experimental module-entry CLIs for migrated `game-gen` and `real-gen` slices.
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
cd legacy
poetry install
poetry run game-gen --help
poetry run real-gen --help
poetry run pytest
```

## Current CLI Commands

現在 `poetry run` で実行できる CLI は [`legacy/pyproject.toml`](legacy/pyproject.toml) に登録されている `game-gen` と `real-gen` です。実行時は `legacy/` で `poetry install` 済みであることを前提にしてください。

設定の優先順位は共通で次です。

1. コマンド引数
2. `--config` で指定した YAML、または `legacy/config.yaml`
3. コード内の組み込み既定値

主要な共通設定キー:

- `output_base`: 出力ルート。既定は `outputs`
- `figures.png_dpi`: PNG 出力 DPI。既定は `150`
- `pipeline.rules`: `apply-rules` と `pipeline` の既定ルール群
- `pipeline.rank_heatmaps`: `apply-rules` と `pipeline` 実行時に `rank-heatmap` を自動生成するか
- `axioms.rules`: `check-axioms` の既定対象ルール
- `rank_heatmap.pairs`: `rank-heatmap` の対象ペア
- `rule_corr_heatmap.method`: `rule-corr-heatmap` の相関指標
- `realgen.import_rank_bins`: `real-gen import-game` の `rank_method: binned` で使う分割数

### `game-gen`

`game-gen` は合成ゲームの生成、ルール適用、公理チェック、図表出力を担当します。

| コマンド | 設定 | 何がどこに生成されるか |
| --- | --- | --- |
| `poetry run game-gen gen-games -p N -c K` | `gen_games.count`, `gen_games.max_score`, `gen_games.seed`, `output_base` | `output_base/games/nN/game_*.csv` を生成。各 CSV には `player*`, `score`, `rank` 列が入る |
| `poetry run game-gen rank-game --game <path> --rule <rule>` | `output_base` | 単一の game CSV に対して `output_base/rankings/nN/<game>.csv` を生成または更新。`rank_*` や `score_*` 列を追加 |
| `poetry run game-gen apply-rules -p N` | `pipeline.rules`, `pipeline.rank_heatmaps`, `figures.png_dpi`, `output_base` | `output_base/games/nN/game_*.csv` を入力に、`output_base/rankings/nN/game_*.csv` を更新。あわせて `output_base/figures/nN/*.png` を生成し、設定次第で `output_base/heatmaps/nN/*.png` も生成 |
| `poetry run game-gen make-figures --rankings-dir <dir>` | `figures.png_dpi`, `output_base` | ranking CSV から `output_base/figures/nN/*.png` を生成 |
| `poetry run game-gen make-figures-png --rankings-dir <dir> --dpi 200` | `figures.png_dpi`, `output_base` | `make-figures` と同じ。`--dpi` を明示できる |
| `poetry run game-gen rank-heatmap -p N` | `rank_heatmap.pairs`, `rank_heatmap.dpi`, `output_base` | `output_base/rankings/nN/*.csv` を集計し、`output_base/heatmaps/nN/<x>_vs_<y>.png` を生成 |
| `poetry run game-gen rule-corr-heatmap -p N` | `rule_corr_heatmap.method`, `figures.png_dpi`, `output_base` | `output_base/heatmaps/nN/rule_corr_player.png` と `rule_corr_coalition.png` を生成 |
| `poetry run game-gen check-axioms -p N` | `axioms.rules`, `output_base` | `output_base/axiom/nN/<axiom>/<rule>.csv`、`output_base/axiom/nN/<axiom>/examples/<rule>/*.png`、`output_base/axiom/nN/summary.csv` を生成 |
| `poetry run game-gen summarize-axioms -p N` | `output_base` | 既存の `output_base/axiom/nN/<axiom>/<rule>.csv` を集約し、`output_base/axiom/nN/summary.csv` を生成 |
| `poetry run game-gen axiom-summary-heatmap -p N` | `figures.png_dpi`, `output_base` | `output_base/axiom/nN/summary.csv` から `output_base/axiom/nN/summary_heatmap.png` を生成 |
| `poetry run game-gen pipeline -p N -c K` | `gen_games.*`, `pipeline.rules`, `pipeline.rank_heatmaps`, `axioms.rules`, `figures.png_dpi`, `rule_corr_heatmap.method`, `output_base` | 一括で `games/`, `rankings/`, `figures/`, `heatmaps/`, `axiom/` を更新。`pipeline.rank_heatmaps: true` のときだけ rank pair heatmap を生成 |

### `real-gen`

`real-gen` は `inputs/feature_mask_tables/<dataset_id>/` に置いた実データ用 feature-mask table を協力ゲーム形式へ正規化し、`game-gen` のルール群を再利用します。

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
| `poetry run real-gen import-game <dataset_id>` | `output_base`, `realgen.import_rank_bins`, `inputs/feature_mask_tables/<dataset_id>/schema.yaml` | `output_base/real/<dataset_id>/games/game_<dataset_id>.csv`、`game_<dataset_id>.features.yaml`、`schema.yaml` のコピーを生成 |
| `poetry run real-gen apply-rules <dataset_id>` | `pipeline.rules` または dataset `schema.yaml` の `rules`, `output_base` | `output_base/real/<dataset_id>/rankings/game_<dataset_id>.csv` を生成または更新。`rank_*` や `score_*` 列を追加 |
| `poetry run real-gen make-figures <dataset_id>` | dataset `schema.yaml` の `figures.*`, `output_base` | `output_base/real/<dataset_id>/figures/*.png` を生成。基本の ranking 図に加えて、条件がそろえば `interaction_index.png`, `shapley_values.png`, `ordinal_banzhaf_values.png` なども生成 |
| `poetry run real-gen feature-rule-heatmap <dataset_id>` | dataset `schema.yaml` の `heatmaps.feature_rule_max_coalition_size`, `output_base` | `output_base/real/<dataset_id>/heatmaps/feature_rule_rank.png` を生成 |

補足:

- `legacy/src/realgen/commands/resignation_contrib.py` は実装ファイルがありますが、現時点では `real-gen` CLI に登録されていないため `poetry run real-gen ...` では呼べません
- 詳細な CLI 用例は [`legacy/README.md`](legacy/README.md) を参照してください

## Experimental `src` CLI

`src/` 側には、移行済みスライスを叩くための experimental CLI があります。これは `poetry run` の公開 CLI ではなく、`src` を `PYTHONPATH` に載せて module 実行する想定です。

```bash
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen apply-rules --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.game_gen rank-game --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen import-game --help
PYTHONPATH=src python -m srs_calculation.interfaces.cli.real_gen apply-rules --help
```

現時点で実装されているのは次です。

- `game_gen apply-rules`: legacy-style game CSV ディレクトリに対して migrated rules を適用する
- `game_gen rank-game`: legacy-style game CSV 1 件に対して migrated rule 1 つを適用する
- `real_gen import-game`: feature-mask table を dataset-scoped な game CSV と `features.yaml` に変換する
- `real_gen apply-rules`: dataset-scoped な `outputs/real/<dataset_id>/games/` に対して migrated rules を適用する

この CLI は意図的に partial です。`real_gen` では figure 系コマンドや heatmap 系コマンドはまだ移行していません。完全なコマンド群は引き続き [`legacy/`](legacy/) 側にあります。

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
- [`legacy/README.md`](legacy/README.md): CLI-oriented reference for the current implementation

## Practical note

This repository is still legacy-first in its published executable surface, but the next implementation is already being built and exercised in `src/` under the documented architecture boundaries.
