"""Command-line interface for realgen (real-data pipeline)."""

from __future__ import annotations

import click

from .commands.apply_rules import apply_rules
from .commands.feature_rule_heatmap import feature_rule_heatmap
from .commands.import_game import import_game
from .commands.make_figures import make_figures


@click.group()
@click.version_option()
def main() -> None:
    """Entry point for the real-gen CLI."""


main.add_command(import_game)
main.add_command(apply_rules)
main.add_command(make_figures)
main.add_command(feature_rule_heatmap)


if __name__ == "__main__":  # pragma: no cover
    main()
