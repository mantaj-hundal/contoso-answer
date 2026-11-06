"""Plotting helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def correlation_heatmap(association_figures, association_tables, correlations):
    """Save correlation chart inputs and render the existing labeled rank-correlation heatmap."""
    heatmap_data = correlations.assign(label=correlations.feature + " " + correlations.measurement).pivot(index="label", columns="outcome", values="spearman_rho")
    heatmap_data.to_csv(association_tables / "correlation_heatmap_inputs.csv")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="vlag", center=0, vmin=-0.5, vmax=0.5,
                cbar_kws={"label": "Spearman rank correlation"}, ax=ax)
    ax.set(title="First-week features and later outcomes", xlabel="Later outcome", ylabel="Days 0–6 feature")
    fig.tight_layout()
    fig.savefig(association_figures / "feature_correlations.png", dpi=180)
    plt.show()
    plt.close(fig)
    print("Error counts can reflect volume rather than reliability. The error-rate regressions below control for attempts.")


def feature_association_intervals(association_figures, primary_associations):
    """Render pointwise adjusted OR intervals on log axes, with separate outcome panels and correct feature/error units."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    for ax, outcome_name in zip(axes, ["retention", "conversion"]):
        rows = primary_associations.loc[primary_associations.model.str.startswith(outcome_name)].copy()
        positions = np.arange(len(rows))
        errors = np.vstack([rows.odds_ratio - rows.ci_low, rows.ci_high - rows.odds_ratio])
        ax.errorbar(rows.odds_ratio, positions, xerr=errors, fmt="o", color="#126C78", capsize=3)
        ax.axvline(1, color="#666666", linestyle="--", linewidth=1)
        ax.set_yticks(positions, rows.term.str.replace("log2_", "Usage: ", regex=False).str.replace("_error_10pp", " error rate", regex=False))
        ax.set_xscale("log")
        ax.set(title=outcome_name.title(), xlabel="Adjusted odds ratio (95% interval)")
        ax.invert_yaxis()
    fig.suptitle("Usage: doubling (1 + attempts)    Error rate: +10 percentage points", fontsize=12)
    fig.tight_layout()
    fig.savefig(association_figures / "adjusted_feature_associations.png", dpi=180)
    plt.show()
    plt.close(fig)


def conversion_timing_and_journey(association_figures, conversion_windows, journey_summary):
    """Render empirical window conversion proportions and converter-only pre-upgrade activity, retaining unequal-edge-window labels."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    labels = conversion_windows.start_day.astype(str) + "–" + conversion_windows.end_day.astype(str)
    axes[0].bar(labels, conversion_windows.conditional_conversion_pct, color="#126C78")
    axes[0].set(title="Observed Free-to-Paid conversion timing", xlabel="Tenure-day window (unequal at edges)", ylabel="Converted / Free at window start (%)")
    axes[0].tick_params(axis="x", rotation=45)
    axes[1].plot(journey_summary.relative_day, journey_summary.active_pct, marker="o", color="#126C78")
    axes[1].set(title="Activity before upgrade among converters", xlabel="Days before first Paid observation", ylabel="Observed activity among eligible converters (%)", ylim=(0,100))
    fig.tight_layout()
    fig.savefig(association_figures / "conversion_timing_and_journey.png", dpi=180)
    plt.show()
    plt.close(fig)
