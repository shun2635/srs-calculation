# srs-calculation

Repository for cooperative-game-based ranking experiments, synthetic game generation, axiom checking, and real-data analysis.

このリポジトリは、協力ゲームに基づくランキング計算、合成ゲーム生成、公理チェック、実データ解析を扱う研究用コードベースです。現在の実装は [`legacy/`](legacy/) にありますが、共同研究と大規模開発を見据えて、新規実装用の [`src/`](src/) と標準化した [`docs/`](docs/) をリポジトリ直下に整備しています。

## Intended audiences

- CMIS Lab, The University of Tokyo: 日本語の入口は [`docs/ja/README.md`](docs/ja/README.md)
- LAMSADE collaborators: English overview is in [`docs/en/README.md`](docs/en/README.md)

Note: the Japanese and English audience guides are intended to stay content-synchronized. When one is updated, the other should be reviewed and updated as needed.

## Current repository status

- The executable implementation lives in [`legacy/`](legacy/).
- The new top-level [`docs/`](docs/) directory is the recommended entry point for collaborators.
- The new top-level [`src/`](src/) directory is reserved for the next implementation, separate from the legacy codebase.
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
- [`src/`](src/): target location for the new implementation
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

This repository is still legacy-first in its executable code, but the documentation is now organized for collaborative development and a future migration into `src/`.
