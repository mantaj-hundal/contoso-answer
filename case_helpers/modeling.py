"""Modeling helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.proportion import proportion_confint
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import warnings


class RegressionCollection:
    """Fit explicit logistic formulas and retain coefficients and diagnostics.

    This object owns this run's fits, avoiding mutable global registries.
    fit() keeps the existing robust covariance, convergence and rank checks.
    """

    def __init__(self):
        self.diagnostics = []
        self.fits = {}
        self.coefficients = []

    def fit(self, name, frame, formula, cluster_column=None):
        """Fit an explicit binary-outcome formula; save all slopes and model diagnostics.

        Input grain is player, or at-risk player-day when cluster_column is provided.
        Missing predictors must be handled explicitly by the caller. OR intervals are
        pointwise robust Wald intervals. Warnings prevent unqualified interpretation.
        """
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = smf.glm(formula, data=frame, family=sm.families.Binomial(), missing="raise")
            if cluster_column:
                fit = model.fit(cov_type="cluster", cov_kwds={"groups": frame[cluster_column]}, maxiter=200)
            else:
                fit = model.fit(cov_type="HC1", maxiter=200)
        design = np.asarray(model.exog)
        rank = np.linalg.matrix_rank(design)
        predictor_vifs = []
        for index, term in enumerate(model.exog_names):
            if term != "Intercept":
                predictor_vifs.append(variance_inflation_factor(design, index))
        warnings_text = "; ".join(str(item.message) for item in caught)
        self.diagnostics.append({"model": name, "formula": formula, "rows": len(frame),
            "players": frame.userid.nunique(), "events": int(model.endog.sum()),
            "parameters": design.shape[1], "events_per_slope": float(model.endog.sum() / (design.shape[1]-1)),
            "converged": bool(fit.converged), "full_rank": rank == design.shape[1],
            "condition_number": float(np.linalg.cond(design)), "max_vif": float(max(predictor_vifs)),
            "warnings": warnings_text, "covariance": "player-clustered" if cluster_column else "HC1",
            "max_abs_coefficient": float(np.abs(fit.params).max())})
        assert fit.converged and rank == design.shape[1], f"Invalid fit: {name}"
        assert np.isfinite(fit.params).all() and np.isfinite(fit.bse).all(), name
        ci = fit.conf_int()
        coefficients = pd.DataFrame({"model": name, "term": fit.params.index,
            "coefficient": fit.params.values, "standard_error": fit.bse.values,
            "odds_ratio": np.exp(fit.params.values), "ci_low": np.exp(ci[0].values),
            "ci_high": np.exp(ci[1].values), "p_value": fit.pvalues.values})
        coefficients["interpretation_ready"] = not bool(warnings_text)
        self.fits[name] = fit
        self.coefficients.append(coefficients)
        return coefficients


def fit_usage_sensitivities(feature_map, models, samples, usage_terms):
    """Fit simpler one-feature specifications and initially-Free-only retention using the same formulas and covariance as before."""
    for name, (frame, outcome) in samples.items():
        # Simpler feature-specific fits check whether mutual adjustment changes the story.
        for feature in feature_map:
            controls = " + initial_paid" if name == "retention" else ""
            models.fit(f"{name}_{feature}_single_usage", frame,
                f"{outcome} ~ log2_{feature} + active_days" + controls)
        if name == "retention":
            models.fit("retention_usage_initial_free_only", frame.loc[frame.initially_free],
                "retained ~ " + usage_terms)


def fit_error_models(feature_map, models, samples):
    """Fit one volume-adjusted error-rate logistic model per feature/outcome, recording zero-attempt exclusions."""
    error_primary_records = []
    error_samples = []
    for outcome_name, (frame, outcome) in samples.items():
        for feature in feature_map:
            eligible = frame.loc[frame[f"{feature}_attempts"].gt(0)].copy()
            controls = " + initial_paid" if outcome_name == "retention" else ""
            formula = f"{outcome} ~ {feature}_error_10pp + log2_{feature} + active_days" + controls
            coefficients = models.fit(f"{outcome_name}_{feature}_errors", eligible, formula)
            error_primary_records.append(coefficients.loc[coefficients.term.eq(f"{feature}_error_10pp")])
            error_samples.append({"outcome": outcome_name, "feature": feature,
                "eligible_players": len(eligible), "events": int(eligible[outcome].sum()),
                "excluded_zero_attempts": len(frame)-len(eligible)})
    primary_errors = pd.concat(error_primary_records, ignore_index=True)
    return (primary_errors, error_samples)


def fit_segment_comparisons(conversion_players, model_players, models):
    """Report all descriptive groups; fit adjusted group models only for categories with at least10 players, logging narrowed scope."""
    segment_records = []
    segment_model_scope = []
    for segment in ["weekend_preference", "feature_preference"]:
        for outcome_name, frame, outcome in [("retention", model_players, "retained"), ("conversion", conversion_players, "later_conversion")]:
            for group, subset in frame.groupby(segment):
                events, count = int(subset[outcome].sum()), len(subset)
                low, high = proportion_confint(events, count, method="wilson")
                segment_records.append({"segment": segment, "group": group, "outcome": outcome_name,
                    "players": count, "events": events, "rate_pct": 100*events/count,
                    "ci_low_pct": 100*low, "ci_high_pct": 100*high})
            controls = " + initial_paid" if outcome_name == "retention" else ""
            group_sizes = frame.groupby(segment).size()
            estimable_groups = group_sizes.loc[group_sizes.ge(10)].index
            regression_subset = frame.loc[frame[segment].isin(estimable_groups)].copy()
            segment_model_scope.append({"outcome":outcome_name,"segment":segment,
                "total_players":len(frame),"regression_players":len(regression_subset),
                "excluded_sparse_players":len(frame)-len(regression_subset),
                "included_groups":", ".join(estimable_groups),
                "reason":"Diagnostic revision: sparse categories (<10 players) descriptive only"})
            group_term = ("C(weekend_preference, Treatment(reference='Weekday'))"
                          if segment == "weekend_preference" else "C(feature_preference)")
            models.fit(f"{outcome_name}_{segment}", regression_subset,
                f"{outcome} ~ {group_term} + active_days" + controls)
    segment_summary = pd.DataFrame(segment_records)
    return (segment_summary, segment_model_scope)
