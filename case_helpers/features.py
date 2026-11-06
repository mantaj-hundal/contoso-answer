"""Features helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

from scipy import stats
from statsmodels.stats.multitest import multipletests
import numpy as np
import pandas as pd


def first_week_features(activity):
    """Aggregate days0–6 into one row per player. Attempts include errors; zero-attempt error rates remain undefined."""
    early_activity = activity.loc[activity.tenure_day.between(0, 6)].copy()
    feature_map = {"optimizer": "AutoComplete", "coach": "Chat", "agent": "Agent"}
    early_features = early_activity.groupby("userid", as_index=False).agg(active_days=("tenure_day", "nunique"))
    for feature, source_name in feature_map.items():
        totals = early_activity.groupby("userid")[[f"AI_{source_name}_Success", f"AI_{source_name}_Error"]].sum()
        attempts = totals.sum(axis=1)
        early_features[f"{feature}_attempts"] = early_features.userid.map(attempts)
        early_features[f"{feature}_errors"] = early_features.userid.map(totals[f"AI_{source_name}_Error"])
        early_features[f"{feature}_error_rate"] = early_features[f"{feature}_errors"].div(early_features[f"{feature}_attempts"].replace(0, np.nan))
        early_features[f"log2_{feature}"] = np.log2(1 + early_features[f"{feature}_attempts"])
        early_features[f"{feature}_error_10pp"] = early_features[f"{feature}_error_rate"] / 0.10
    return (early_activity, early_features, feature_map)


def define_later_outcomes(association_tables, calendar, early_features, roster):
    """Join first-week predictors one-to-one to the complete roster and define later retention/conversion without future-feature leakage."""
    model_players = roster.merge(early_features, on="userid", validate="one_to_one", how="left")
    retained_ids = set(calendar.loc[calendar.tenure_day.between(28, 34) & calendar.observed_activity, "userid"])
    model_players["retained"] = model_players.userid.isin(retained_ids).astype(int)
    model_players["initial_paid"] = model_players.initial_plan.eq("Paid").astype(int)
    model_players["conversion_eligible"] = model_players.initially_free & (model_players.conversion_tenure_day.isna() | model_players.conversion_tenure_day.gt(6))
    model_players["later_conversion"] = model_players.conversion_tenure_day.between(7, 59).fillna(False).astype(int)
    assert model_players.active_days.notna().all() and model_players.userid.is_unique
    conversion_players = model_players.loc[model_players.conversion_eligible].copy()
    samples = {"retention": (model_players, "retained"), "conversion": (conversion_players, "later_conversion")}
    sample_summary = pd.DataFrame([
        {"outcome": name, "players": len(frame), "events": int(frame[outcome].sum()),
         "nonevents": int(len(frame) - frame[outcome].sum())}
        for name, (frame, outcome) in samples.items()
    ])
    sample_summary.to_csv(association_tables / "sample_summary.csv", index=False)
    return (model_players, conversion_players, samples, sample_summary)


def correlate_features_and_outcomes(association_tables, feature_map, samples):
    """Compute 18 player-level rank correlations, 4999 label permutations per pair, and BH q-values with the original fixed seed."""
    rng = np.random.default_rng(20261105)
    correlation_records = []
    for outcome_name, (frame, outcome) in samples.items():
        for feature in feature_map:
            for measurement in ["attempts", "errors", "error_rate"]:
                field = f"{feature}_{measurement}"
                pair = frame[[field, outcome]].dropna()
                x = stats.rankdata(pair[field].to_numpy()).astype(float)
                y = pair[outcome].to_numpy(dtype=float)
                x -= x.mean()
                y -= y.mean()
                denominator = np.linalg.norm(x) * np.linalg.norm(y)
                rho = float(x @ y / denominator)
                permutations = np.array([rng.permutation(y) for _ in range(4999)])
                null_correlations = permutations @ x / denominator
                pvalue = (1 + np.count_nonzero(np.abs(null_correlations) >= abs(rho) - 1e-12)) / 5000
                correlation_records.append({"outcome": outcome_name, "feature": feature,
                    "measurement": measurement, "players": len(pair), "excluded_zero_attempts": len(frame)-len(pair),
                    "spearman_rho": rho, "permutation_p": pvalue})
    correlations = pd.DataFrame(correlation_records)
    correlations["bh_q"] = multipletests(correlations.permutation_p, method="fdr_bh")[1]
    correlations.to_csv(association_tables / "feature_outcome_correlations.csv", index=False)
    return correlations


def assign_player_segments(early_activity, feature_map, model_players):
    """Assign first-week weekend-frequency and plan-limit-normalized feature preference, preserving exact ties and original populations."""
    weekend_days = early_activity.loc[early_activity.Weekend].groupby("userid").size()
    weekday_days = early_activity.loc[~early_activity.Weekend].groupby("userid").size()
    model_players["weekend_active_fraction"] = model_players.userid.map(weekend_days).fillna(0) / 2
    model_players["weekday_active_fraction"] = model_players.userid.map(weekday_days).fillna(0) / 5
    difference = model_players.weekend_active_fraction - model_players.weekday_active_fraction
    model_players["weekend_preference"] = np.select([difference.gt(1e-10), difference.lt(-1e-10)], ["Weekend", "Weekday"], default="Balanced")
    limits = {"optimizer": {"Free":100, "Paid":200}, "coach":{"Free":10, "Paid":50}, "agent":{"Free":5, "Paid":20}}
    normalized_fields = []
    for feature in feature_map:
        early_activity[f"{feature}_capacity_fraction"] = early_activity[f"{feature}_attempts"] / early_activity.plan.map(limits[feature])
        daily_capacity = early_activity.groupby("userid")[f"{feature}_capacity_fraction"].sum() / 7
        field = f"{feature}_capacity_fraction"
        model_players[field] = model_players.userid.map(daily_capacity)
        normalized_fields.append(field)
    capacity_values = model_players[normalized_fields]
    top_value = capacity_values.max(axis=1)
    ties = np.isclose(capacity_values.to_numpy(), top_value.to_numpy()[:, None]).sum(axis=1)
    model_players["feature_preference"] = capacity_values.idxmax(axis=1).str.replace("_capacity_fraction", "", regex=False)
    model_players.loc[(ties > 1) | top_value.eq(0), "feature_preference"] = "Balanced"
    conversion_players = model_players.loc[model_players.conversion_eligible].copy()
    return (model_players, conversion_players, normalized_fields)


def at_risk_player_days(conversion_players):
    """Expand eligible Free players to days7–59 and remove only post-upgrade days; use fixed pre-outcome feature values."""
    risk_days = conversion_players.merge(pd.DataFrame({"tenure_day":np.arange(7,60)}), how="cross")
    risk_days = risk_days.loc[risk_days.conversion_tenure_day.isna() | risk_days.tenure_day.le(risk_days.conversion_tenure_day)].copy()
    # With complete declared follow-up, a missing conversion date means no observed
    # conversion that day; it is not a missing outcome to be dropped from the risk set.
    risk_days["converted_today"] = risk_days.tenure_day.eq(risk_days.conversion_tenure_day).fillna(False).astype(int)
    risk_days["log_tenure_day"] = np.log(risk_days.tenure_day)
    return risk_days
