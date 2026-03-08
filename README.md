# srs-calculation

Repository for cooperative-game-based ranking experiments, synthetic game generation, axiom checking, and real-data analysis.

このリポジトリは、協力ゲームに基づくランキング計算、合成ゲーム生成、公理チェック、実データ解析を扱う研究用コードベースです。現在の実装は [`legacy/`](legacy/) にありますが、共同研究で読みやすく使いやすい形にするため、入口となる docs をリポジトリ直下に整理しています。

## Intended audiences

- CMIS Lab, The University of Tokyo: 日本語の入口は [`docs/ja/README.md`](docs/ja/README.md)
- LAMSADE collaborators: English overview is in [`docs/en/README.md`](docs/en/README.md)

Note: the Japanese and English audience guides are intended to stay content-synchronized. When one is updated, the other should be reviewed and updated as needed.

## Current repository status

- The executable implementation lives in [`legacy/`](legacy/).
- The new top-level [`docs/`](docs/) directory is the recommended entry point for collaborators.
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

## Documentation map

- [`docs/README.md`](docs/README.md): documentation hub
- [`docs/architecture.md`](docs/architecture.md): code and pipeline overview
- [`docs/research-workflow.md`](docs/research-workflow.md): how to use the repository in research collaboration
- [`legacy/README.md`](legacy/README.md): CLI-oriented reference for the current implementation

## Practical note

This repository is still legacy-first in its code layout. The new documentation layer is meant to make collaboration easier before a larger code reorganization happens.
