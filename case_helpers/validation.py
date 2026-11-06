"""Validation helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

from collections import Counter
from collections import defaultdict
from datetime import datetime
from scipy import optimize
from scipy import special
from scipy import stats
import csv
import hashlib
import numpy as np
import pandas as pd


def check_dates_and_cohort(activity_clean, activity_raw, audit):
    """Validate date/key/cohort consistency before metrics. Records issues without changing source values."""
    audit.check_rows("required_fields_present", activity_raw.isna().any(axis=1), "All supplied fields must be present")
    audit.check_rows("valid_dates", activity_clean[["activity_date", "cohort_date"]].isna().any(axis=1), "Dates parse under the stated US format")
    audit.check_rows("unique_player_day", activity_clean.duplicated(["userid", "activity_date"], keep=False), "One row per player per activity date")
    audit.check_rows("no_exact_duplicates", activity_raw.duplicated(keep=False), "No identical input records")
    audit.check_rows("valid_plans", ~activity_clean.plan.isin(["Free", "Paid"]), "Only documented plans")
    audit.check_rows("valid_status", ~activity_clean.Status.isin(["Active", "Cancelled"]), "Only documented billing statuses")
    audit.check_rows("cohort_dates", ~activity_clean.cohort_date.between("2025-03-03", "2025-03-07"), "Account creation dates are in assignment window")
    audit.check_rows("stable_cohort", activity_clean.groupby("userid").cohort_date.transform("nunique").ne(1), "Each player has one cohort date")

    activity_clean["tenure_day"] = (activity_clean.activity_date - activity_clean.cohort_date).dt.days
    audit.check_rows("tenure_matches_source", activity_clean.tenure_day.ne(activity_clean.DaysSinceStart), "Calendar date difference equals supplied tenure")
    audit.check_rows("tenure_in_window", ~activity_clean.tenure_day.between(0, 59), "Only days 0 through 59")
    audit.check_rows("weekday_consistent", activity_clean.activity_date.dt.day_name().ne(activity_clean.DayOfWeek), "Supplied weekday agrees with date")
    audit.check_rows("weekend_consistent", activity_clean.activity_date.dt.dayofweek.ge(5).ne(activity_clean.Weekend), "Supplied weekend flag agrees with date")

    day0_counts = activity_clean.loc[activity_clean.tenure_day.eq(0)].groupby("userid").size()
    audit.check_rows("one_day0_per_player", activity_clean.userid.map(day0_counts).fillna(0).ne(1), "Exactly one day-0 row for every observed player")
    day0_cohorts = activity_clean.loc[activity_clean.tenure_day.eq(0)].groupby("cohort_date").size()
    expected_cohorts = pd.date_range("2025-03-03", "2025-03-07")
    audit.check_condition("documented_cohort_size", activity_clean.userid.nunique() == 300,
                    "Source describes 300 synthetic players")
    audit.check_condition("documented_daily_cohorts", day0_cohorts.reindex(expected_cohorts, fill_value=0).eq(60).all(),
                    "Source describes 60 new players per start date")


def check_feature_limits(activity_clean, audit, original_columns):
    """Check nonnegative whole-number counts and plan-specific daily attempt limits. Returns source feature column names."""
    feature_columns = [column for column in original_columns if column.startswith("AI_")]
    for column in feature_columns:
        counts = pd.to_numeric(activity_clean[column], errors="coerce")
        audit.check_rows("valid_count_" + column, counts.isna() | counts.lt(0) | counts.mod(1).ne(0),
                   "Feature counts must be nonnegative whole numbers")
    for feature, free_limit, paid_limit in [("AutoComplete", 100, 200), ("Chat", 10, 50), ("Agent", 5, 20)]:
        attempts = activity_clean[f"AI_{feature}_Success"] + activity_clean[f"AI_{feature}_Error"]
        limit = activity_clean.plan.map({"Free": free_limit, "Paid": paid_limit})
        audit.check_rows("daily_limit_" + feature, attempts.gt(limit), "Successes plus errors respect end-of-day plan limit")
    return feature_columns


def check_billing_history(activity_clean, audit):
    """Check ordered plan/cancellation histories. Returns first explicit cancellation date indexed by player."""
    # Check temporal relationships after sorting; never use physical CSV row order as time.
    ordered_activity = activity_clean.sort_values(["userid", "activity_date"])
    paid_seen = ordered_activity.plan.eq("Paid").groupby(ordered_activity.userid).cummax()
    audit.check_rows("no_paid_to_free", (ordered_activity.plan.eq("Free") & paid_seen).reindex(activity_clean.index),
               "No undocumented Paid-to-Free reversal")
    cancellation_date_by_user = activity_clean.loc[activity_clean.Status.eq("Cancelled")].groupby("userid").activity_date.min()
    cancellation_rows_by_user = activity_clean.Status.eq("Cancelled").groupby(activity_clean.userid).sum()
    audit.check_rows("cancellation_paid_only", activity_clean.Status.eq("Cancelled") & activity_clean.plan.ne("Paid"), "Cancellation must occur on a Paid record")
    audit.check_rows("single_cancellation", activity_clean.userid.map(cancellation_rows_by_user).gt(1), "At most one cancellation record per player")
    audit.check_rows("no_post_cancellation_activity", activity_clean.activity_date.gt(activity_clean.userid.map(cancellation_date_by_user)), "No observed rows after recorded cancellation")
    audit.check_rows("date_not_beyond_cutoff", activity_clean.activity_date.gt(pd.Timestamp("2025-05-05")), "No records beyond documented source end")
    return cancellation_date_by_user


def verify_preservation_and_calendar(
    activity_clean,
    activity_raw,
    added_calendar_rows,
    audit,
    data_path,
    feature_columns,
    original_columns,
    player_day_calendar,
    player_summary,
    source_sha256,
):
    """Reconcile original values, input fingerprint, player population, calendar matches and feature totals."""
    source_order = activity_clean.sort_values("source_row_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(source_order[original_columns], activity_raw.reset_index(drop=True))
    audit.verify("all_original_values_preserved", True)
    audit.verify("input_sha256_unchanged", hashlib.sha256(data_path.read_bytes()).hexdigest() == source_sha256)
    audit.verify("activity_row_count_preserved", len(activity_clean) == len(activity_raw))
    audit.verify("player_population_preserved", set(player_summary.userid) == set(activity_raw.userid))
    audit.verify("calendar_one_row_per_player_day", not player_day_calendar.duplicated(["userid", "tenure_day"]).any())
    audit.verify("calendar_60_days_per_player", player_day_calendar.groupby("userid").size().eq(60).all())
    audit.verify("all_observed_rows_match_calendar_once", player_day_calendar.source_row_id.dropna().astype(int).sort_values().tolist() == list(range(1, len(activity_raw) + 1)))
    audit.verify("absent_billing_and_counts_remain_unknown", added_calendar_rows[["plan", "Status", *feature_columns]].isna().all().all())
    audit.verify("all_day0_players_present_in_calendar", player_day_calendar.loc[player_day_calendar.tenure_day.eq(0)].observed_activity.all())
    audit.verify("feature_totals_preserved", activity_clean[feature_columns].sum().equals(activity_raw[feature_columns].sum()))


def read_player_ledger(data_path):
    """Independently read CSV via csv.DictReader; return player history facts and observed player-date keys."""
    source_ledger = {}
    source_keys = set()
    with data_path.open(newline="", encoding="utf-8-sig") as source_file:
        for source_row_id, row in enumerate(csv.DictReader(source_file), start=1):
            user = int(row["userid"])
            observed_date = datetime.strptime(row["date"], "%m/%d/%Y").date()
            cohort = datetime.strptime(row["startdate"], "%m/%d/%Y").date()
            entry = source_ledger.setdefault(user, {"cohort": cohort, "initial_plan": None,
                "first_paid": None, "cancelled": None, "day0_source_row_id": None})
            source_keys.add((user, observed_date))
            if observed_date == cohort:
                entry["initial_plan"] = row["plan"]
                entry["day0_source_row_id"] = source_row_id
            if row["plan"] == "Paid":
                entry["first_paid"] = min(entry["first_paid"] or observed_date, observed_date)
            if row["Status"] == "Cancelled":
                entry["cancelled"] = observed_date
    return (source_ledger, source_keys)


def verify_player_events(audit, player_day_calendar, player_summary, source_keys, source_ledger):
    """Compare each prepared player's dates/flags and calendar activity keys against the independent CSV ledger."""
    for player in player_summary.itertuples():
        expected = source_ledger[player.userid]
        assert player.initial_plan == expected["initial_plan"]
        assert player.cohort_date.date() == expected["cohort"]
        assert player.day0_source_row_id == expected["day0_source_row_id"]
        for actual, target in [(player.first_paid_date, expected["first_paid"]),
                               (player.cancellation_date, expected["cancelled"])]:
            assert (pd.isna(actual) and target is None) or (not pd.isna(actual) and actual.date() == target)
        expected_conversion = expected["initial_plan"] == "Free" and expected["first_paid"] is not None
        assert player.converted_from_initial_free == expected_conversion
        assert player.explicit_cancellation_observed == (expected["cancelled"] is not None)
        expected_conversion_date = expected["first_paid"] if expected_conversion else None
        assert (pd.isna(player.conversion_date) and expected_conversion_date is None) or (
            not pd.isna(player.conversion_date) and player.conversion_date.date() == expected_conversion_date)
    audit.verify("independent_player_events_and_cohort_match", True)
    calendar_observed_keys = set(zip(
        player_day_calendar.loc[player_day_calendar.observed_activity, "userid"],
        player_day_calendar.loc[player_day_calendar.observed_activity, "activity_date"].dt.date,
    ))
    audit.verify("independent_observed_activity_keys_match", calendar_observed_keys == source_keys)


def verify_mandatory_answers(
    cancelled_players_count,
    conversion_pct,
    converted_players_count,
    daily_retention,
    data_path,
    free_players_count,
    initial_counts,
    paid_players,
    results_folder,
    source_sha256,
    weekly_retention,
):
    """Independently reread source CSV and verify every mandatory count, retention numerator/percentage, denominator and source hash."""
    from collections import Counter, defaultdict
    from IPython.display import Markdown

    source_initial_plan = {}
    source_paid_users = set()
    source_cancelled_users = set()
    source_daily_active = defaultdict(set)
    source_weekly_active = defaultdict(set)
    with data_path.open(newline="", encoding="utf-8-sig") as source_file:
        for row in csv.DictReader(source_file):
            user = int(row["userid"])
            day = (datetime.strptime(row["date"], "%m/%d/%Y") - datetime.strptime(row["startdate"], "%m/%d/%Y")).days
            source_daily_active[day].add(user)
            source_weekly_active[day // 7 + 1].add(user)
            if day == 0:
                source_initial_plan[user] = row["plan"]
            if row["plan"] == "Paid":
                source_paid_users.add(user)
            if row["Status"] == "Cancelled":
                source_cancelled_users.add(user)

    source_initial_counts = Counter(source_initial_plan.values())
    source_free_users = {user for user, plan in source_initial_plan.items() if plan == "Free"}
    source_converters = source_free_users & source_paid_users
    source_cohort_count = len(source_initial_plan)
    answer_checks = {
        "q1_starting_plan_counts": all(int(initial_counts[plan]) == source_initial_counts[plan] for plan in ["Free", "Paid"]),
        "q2_all_daily_counts": all(row.active_players == len(source_daily_active[row.tenure_day]) for row in daily_retention.itertuples()),
        "q2_all_weekly_counts": all(row.active_players == len(source_weekly_active[row.tenure_week]) for row in weekly_retention.itertuples()),
        "q2_fixed_day0_denominators": daily_retention.day0_cohort_players.eq(source_cohort_count).all() and weekly_retention.day0_cohort_players.eq(source_cohort_count).all(),
        "q2_all_daily_percentages": all(np.isclose(row.retention_pct, 100 * len(source_daily_active[row.tenure_day]) / source_cohort_count) for row in daily_retention.itertuples()),
        "q2_all_weekly_percentages": all(np.isclose(row.retention_pct, 100 * len(source_weekly_active[row.tenure_week]) / source_cohort_count) for row in weekly_retention.itertuples()),
        "q3_conversion_count_and_denominator": converted_players_count == len(source_converters) and free_players_count == len(source_free_users),
        "q3_conversion_percentage": bool(np.isclose(conversion_pct, 100 * len(source_converters) / len(source_free_users))) if source_free_users else bool(pd.isna(conversion_pct)),
        "q4_explicit_cancellations": cancelled_players_count == len(source_cancelled_users),
        "q4_paid_population": len(paid_players) == len(source_paid_users) and source_cancelled_users.issubset(source_paid_users),
        "source_unchanged": hashlib.sha256(data_path.read_bytes()).hexdigest() == source_sha256,
    }
    answer_checks = {name: bool(passed) for name, passed in answer_checks.items()}
    pd.DataFrame([{"check": name, "passed": passed} for name, passed in answer_checks.items()]).to_csv(results_folder / "answer_checks.csv", index=False)
    assert all(answer_checks.values()), "A mandatory-answer cross-check failed; inspect answer_checks.csv."
    return answer_checks


def verify_features_and_risk_sets(conversion_hazard, conversion_players, data_path, feature_map, model_players):
    """Rebuild first-week totals, retention outcomes and every conversion risk set independently using the source CSV."""
    source_early_totals = defaultdict(lambda: Counter())
    source_retained = set()
    source_conversion_days = {}
    source_initial = {}
    source_risk_activity = set()
    with data_path.open(newline="", encoding="utf-8-sig") as source_file:
        for row in csv.DictReader(source_file):
            user = int(row["userid"])
            day = int(row["DaysSinceStart"])
            source_risk_activity.add((user,day))
            if day == 0:
                source_initial[user] = row["plan"]
            if day <= 6:
                source_early_totals[user]["active_days"] += 1
                for feature, column in feature_map.items():
                    source_early_totals[user][f"{feature}_attempts"] += int(row[f"AI_{column}_Success"]) + int(row[f"AI_{column}_Error"])
                    source_early_totals[user][f"{feature}_errors"] += int(row[f"AI_{column}_Error"])
            if 28 <= day <= 34:
                source_retained.add(user)
            if row["plan"] == "Paid":
                source_conversion_days[user] = min(source_conversion_days.get(user,day),day)

    for row in model_players.to_dict("records"):
        for field in ["active_days"] + [f"{feature}_{suffix}" for feature in feature_map for suffix in ["attempts","errors"]]:
            assert row[field] == source_early_totals[row["userid"]][field]
        assert bool(row["retained"]) == (row["userid"] in source_retained)
    source_later_users = {user for user,plan in source_initial.items() if plan == "Free" and source_conversion_days.get(user,60) >= 7}
    source_later_converters = {user for user in source_later_users if source_conversion_days.get(user,60) <= 59}
    assert set(conversion_players.userid) == source_later_users
    assert int(conversion_players.later_conversion.sum()) == len(source_later_converters)
    for row in conversion_hazard.itertuples():
        expected_at_risk = sum(plan == "Free" and source_conversion_days.get(user,60) >= row.tenure_day for user,plan in source_initial.items())
        expected_events = sum(user in source_later_converters and day == row.tenure_day for user,day in source_conversion_days.items())
        assert row.at_risk_free_players == expected_at_risk and row.conversions == expected_events
    return source_later_converters


def verify_rank_correlations(correlations, samples):
    """Cross-check the custom permutation routine's observed rank correlation against SciPy for every outcome-feature pair."""
    for row in correlations.itertuples():
        frame, outcome = samples[row.outcome]
        pair = frame[[f"{row.feature}_{row.measurement}",outcome]].dropna()
        assert np.isclose(row.spearman_rho, stats.spearmanr(pair.iloc[:,0],pair.iloc[:,1]).statistic)


def verify_regression_optimizers(association_checks, models):
    """Refit the two main Bernoulli likelihoods with SciPy BFGS and assert coefficients match statsmodels within1e-4."""
    optimizer_checks = []
    for name in ["retention_usage", "conversion_usage"]:
        fit = models.fits[name]
        x, y = np.asarray(fit.model.exog), np.asarray(fit.model.endog)
        def negative_log_likelihood(beta):
            eta = x @ beta
            return np.logaddexp(0,eta).sum() - y @ eta
        def gradient(beta):
            return x.T @ (special.expit(x @ beta)-y)
        independent_fit = optimize.minimize(negative_log_likelihood, np.zeros(x.shape[1]), jac=gradient,
                                           method="BFGS", options={"gtol":1e-6,"maxiter":1000})
        coefficient_difference = float(np.max(np.abs(independent_fit.x - fit.params.to_numpy())))
        assert coefficient_difference < 1e-4, f"Independent regression mismatch: {name}"
        optimizer_checks.append({"model":name,"max_abs_coefficient_difference":coefficient_difference,
                                 "gradient_norm":float(np.linalg.norm(gradient(independent_fit.x))),
                                 "optimizer_message":str(independent_fit.message)})
    pd.DataFrame(optimizer_checks).to_csv(association_checks / "independent_regression_checks.csv", index=False)


def verify_final_analysis_population(
    association_folder,
    conversion_windows,
    converters,
    data_path,
    early_features,
    feature_audit,
    model_players,
    risk_days,
    source_later_converters,
    source_sha256,
):
    """Reconcile risk-set events, timing-window counts, feature-audit size and input hash, then save player model inputs."""
    assert int(risk_days.converted_today.sum()) == len(source_later_converters)
    assert int(conversion_windows.conversions.sum()) == len(converters)
    assert len(feature_audit) == len(early_features)*(len(early_features.columns)-1)
    assert hashlib.sha256(data_path.read_bytes()).hexdigest() == source_sha256
    model_players.to_parquet(association_folder / "player_model_inputs.parquet", index=False)
    print("Independent source totals/outcomes, all hazard risk sets, rank correlations, both main regression optimizers, and source hash matched.")
