"""Plotting adapters."""

from .figure_renderer import generate_real_ranking_figure
from .figure_renderer import generate_synthetic_ranking_figure
from .figure_renderer import (
    generate_give_topk_table,
    generate_interaction_index_figure,
    generate_kset_rank_occurrence_distribution_heatmap,
    generate_lexcel_rank_count_heatmap,
    generate_ordinal_banzhaf_values_plot,
    generate_rank_occurrence_distribution_heatmap,
    generate_red_index_scatter_plot,
    generate_red_index_topk_by_size_figures,
    generate_rp_index_top_size2_figure,
    generate_shapley_values_plot,
)
from .heatmap_renderer import (
    feature_rule_rank_table,
    normalize_ranks_per_rule,
    render_feature_rule_rank_heatmap,
)
from .synthetic_rank_heatmap import (
    collect_rank_pairs,
    collect_rule_correlation_matrix,
    infer_rank_column_scopes,
    render_correlation_heatmap,
    render_rank_pair_heatmap,
)

__all__ = [
    "feature_rule_rank_table",
    "generate_give_topk_table",
    "generate_interaction_index_figure",
    "generate_kset_rank_occurrence_distribution_heatmap",
    "generate_lexcel_rank_count_heatmap",
    "generate_ordinal_banzhaf_values_plot",
    "generate_rank_occurrence_distribution_heatmap",
    "generate_real_ranking_figure",
    "generate_red_index_scatter_plot",
    "generate_red_index_topk_by_size_figures",
    "generate_rp_index_top_size2_figure",
    "generate_shapley_values_plot",
    "generate_synthetic_ranking_figure",
    "normalize_ranks_per_rule",
    "collect_rank_pairs",
    "collect_rule_correlation_matrix",
    "infer_rank_column_scopes",
    "render_feature_rule_rank_heatmap",
    "render_correlation_heatmap",
    "render_rank_pair_heatmap",
]
