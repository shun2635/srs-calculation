"""Command-line interface for the game-gen toolkit."""

from __future__ import annotations

import click

from .commands.axioms import axiom_summary_heatmap, check_axioms, summarize_axioms
from .commands.figures import make_figures, make_figures_png
from .commands.games import gen_games
from .commands.heatmaps import rank_heatmap, rule_corr_heatmap
from .commands.pipeline import apply_rules, pipeline
from .commands.rankings import rank_game


@click.group()
@click.version_option()
def main() -> None:
    """Entry point for the game-gen CLI."""


# Register commands
main.add_command(gen_games)
main.add_command(rank_game)
main.add_command(make_figures)
main.add_command(make_figures_png)
main.add_command(rank_heatmap)
main.add_command(rule_corr_heatmap)
main.add_command(check_axioms)
main.add_command(summarize_axioms)
main.add_command(axiom_summary_heatmap)
main.add_command(pipeline)
main.add_command(apply_rules)


if __name__ == "__main__":  # pragma: no cover
    main()
