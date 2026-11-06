"""Metrics helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

from statsmodels.stats.proportion import proportion_confint
import numpy as np
import pandas as pd


def retention_tables(calendar, cohort_players, output_folder):
    """Return exact-day and any-activity-week retention using the fixed day-0 denominator. The final week stays explicitly partial."""
    # With a unique player-day key, each True represents one active player on that day.
    daily_retention = calendar.groupby("tenure_day", as_index=False).agg(
        active_players=("observed_activity", "sum")
    )
    daily_retention["day0_cohort_players"] = cohort_players
    daily_retention["retention_pct"] = 100 * daily_retention.active_players / cohort_players

    # First reduce to player-week: any observed day makes that player active for the week.
    player_week = calendar.groupby(["userid", "tenure_week"], as_index=False).agg(
        active_in_week=("observed_activity", "any")
    )
    weekly_retention = player_week.groupby("tenure_week", as_index=False).agg(
        active_players=("active_in_week", "sum")
    )
    week_definitions = pd.read_csv(output_folder / "week_windows.csv")
    weekly_retention = weekly_retention.merge(
        week_definitions, on="tenure_week", validate="one_to_one"
    )
    weekly_retention["day0_cohort_players"] = cohort_players
    weekly_retention["retention_pct"] = 100 * weekly_retention.active_players / cohort_players
    weekly_retention = weekly_retention[["tenure_week", "start_day_inclusive", "end_day_inclusive",
        "days_in_window", "is_partial_week", "active_players", "day0_cohort_players", "retention_pct"]]
    return (daily_retention, weekly_retention)


def conversion_risk_sets(association_tables, model_players):
    """Build daily and window-start Free risk sets, retaining inactive nonconverters until day59. Return empirical hazards and intervals."""
    initial_free_roster = model_players.loc[model_players.initially_free].copy()
    hazard_records = []
    for day in range(1, 60):
        at_risk = initial_free_roster.conversion_tenure_day.isna() | initial_free_roster.conversion_tenure_day.ge(day)
        events = int(initial_free_roster.conversion_tenure_day.eq(day).sum())
        hazard_records.append({"tenure_day": day, "at_risk_free_players": int(at_risk.sum()),
            "conversions": events, "daily_conversion_pct": 100*events/int(at_risk.sum())})
    conversion_hazard = pd.DataFrame(hazard_records)
    window_records = []
    for start, end in [(1,6),(7,13),(14,20),(21,27),(28,34),(35,41),(42,48),(49,55),(56,59)]:
        at_start = initial_free_roster.conversion_tenure_day.isna() | initial_free_roster.conversion_tenure_day.ge(start)
        events = int(initial_free_roster.conversion_tenure_day.between(start,end).sum())
        count = int(at_start.sum())
        low, high = proportion_confint(events, count, method="wilson")
        window_records.append({"start_day":start,"end_day":end,"days_in_window":end-start+1,
            "free_at_start":count,"conversions":events,"conditional_conversion_pct":100*events/count,
            "ci_low_pct":100*low,"ci_high_pct":100*high})
    conversion_windows = pd.DataFrame(window_records)
    conversion_hazard.to_csv(association_tables / "daily_conversion_hazard.csv", index=False)
    conversion_windows.to_csv(association_tables / "conversion_timing_windows.csv", index=False)
    return (initial_free_roster, conversion_hazard, conversion_windows)


def preconversion_journeys(activity, association_tables, calendar, initial_free_roster):
    """Summarize seven pre-upgrade days among eventual converters. Exclude upgrade day; distinguish activity from per-active-day feature means."""
    converters = initial_free_roster.loc[initial_free_roster.converted_from_initial_free, ["userid", "conversion_tenure_day"]]
    journey_calendar = converters.merge(pd.DataFrame({"relative_day":np.arange(-7,0)}), how="cross")
    journey_calendar["tenure_day"] = journey_calendar.conversion_tenure_day + journey_calendar.relative_day
    journey_calendar = journey_calendar.loc[journey_calendar.tenure_day.ge(0)]
    journey_calendar = journey_calendar.merge(calendar[["userid","tenure_day","observed_activity"]], on=["userid","tenure_day"], validate="one_to_one")
    journey_calendar = journey_calendar.merge(activity[["userid","tenure_day","optimizer_attempts","coach_attempts","agent_attempts"]], on=["userid","tenure_day"], how="left", validate="one_to_one")
    journey_summary = journey_calendar.groupby("relative_day", as_index=False).agg(
        eligible_converters=("userid","size"), active_converters=("observed_activity","sum"),
        optimizer_attempts_per_active_day=("optimizer_attempts","mean"),
        coach_attempts_per_active_day=("coach_attempts","mean"),
        agent_attempts_per_active_day=("agent_attempts","mean"))
    journey_summary["active_pct"] = 100*journey_summary.active_converters/journey_summary.eligible_converters
    journey_summary.to_csv(association_tables / "preconversion_journey.csv", index=False)
    print(f"Conversion tenure among {len(converters)} converters: median {converters.conversion_tenure_day.median():.0f}, range {converters.conversion_tenure_day.min():.0f}–{converters.conversion_tenure_day.max():.0f} days. This conditions on converting.")
    return (converters, journey_summary)
