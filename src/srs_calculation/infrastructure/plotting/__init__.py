"""Plotting adapters."""

from .axiom_summary_heatmap import render_axiom_summary_heatmap
from .figure_renderer import (
    generate_give_topk_table,
    generate_interaction_index_figure,
    generate_kset_rank_occurrence_distribution_heatmap,
    generate_lexcel_rank_count_heatmap,
    generate_ordinal_banzhaf_values_plot,
    generate_rank_occurrence_distribution_heatmap,
    generate_rankdiff_top_size2_figure,
    generate_real_ranking_figure,
    generate_red_index_scatter_plot,
    generate_red_index_topk_by_size_figures,
    generate_shapley_values_plot,
    generate_synthetic_ranking_figure,
)
from .heatmap_renderer import (
    feature_rule_rank_table,
    normalize_ranks_per_rule,
    render_feature_rule_rank_heatmap,
)
from .paper_simulation import (
    render_paper_heatmap,
    render_rank_correlation_figure,
    render_reversal_consistency_figure,
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
    "generate_rankdiff_top_size2_figure",
    "generate_shapley_values_plot",
    "generate_synthetic_ranking_figure",
    "normalize_ranks_per_rule",
    "render_paper_heatmap",
    "render_rank_correlation_figure",
    "render_reversal_consistency_figure",
    "render_axiom_summary_heatmap",
    "collect_rank_pairs",
    "collect_rule_correlation_matrix",
    "infer_rank_column_scopes",
    "render_feature_rule_rank_heatmap",
    "render_correlation_heatmap",
    "render_rank_pair_heatmap",
]
