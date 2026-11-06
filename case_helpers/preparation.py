"""Preparation helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

import json
import numpy as np
import pandas as pd


def derive_activity_fields(activity_clean, activity_raw, audit):
    """Add tenure-week/activity/cancellation/attempt fields, preserve original columns, audit additions and sort player timelines."""
    date_fields = ["activity_date", "cohort_date", "tenure_day"]
    audit.record_rule("typed_dates_and_tenure", "Add analysis-safe dates and verify tenure without replacing source fields",
                activity_raw, activity_clean, len(activity_clean), activity_clean.userid.nunique(),
                "Explicit %m/%d/%Y parsing; original date, startdate and DaysSinceStart retained")
    audit.audit_added_fields(activity_clean, date_fields, "typed_dates_and_tenure", "activity_clean", "activity_date")

    activity_clean["tenure_week"] = activity_clean.tenure_day // 7 + 1
    activity_clean["is_partial_week"] = activity_clean.tenure_week.eq(9)
    activity_clean["observed_activity"] = True
    activity_clean["explicit_cancellation"] = activity_clean.Status.eq("Cancelled")
    attempt_fields = []
    for feature, label in [("AutoComplete", "optimizer"), ("Chat", "coach"), ("Agent", "agent")]:
        field = f"{label}_attempts"
        activity_clean[field] = activity_clean[f"AI_{feature}_Success"] + activity_clean[f"AI_{feature}_Error"]
        attempt_fields.append(field)
    derived_fields = ["tenure_week", "is_partial_week", "observed_activity", "explicit_cancellation", *attempt_fields]
    audit.record_rule("activity_derivations", "Prepare daily/weekly activity and feature denominators",
                activity_raw, activity_clean, len(activity_clean), activity_clean.userid.nunique(),
                "Source-row presence establishes activity; no aggregation of business outcomes")
    audit.audit_added_fields(activity_clean, derived_fields, "activity_derivations", "activity_clean", "activity_date")
    activity_clean = activity_clean.sort_values(["userid", "activity_date"]).reset_index(drop=True)
    audit.record_rule("sort_activity", "Order records for reproducible within-player timelines",
                activity_raw, activity_clean, len(activity_clean), activity_clean.userid.nunique(),
                "Sorted by userid and activity_date; source_row_id retains original ordering")
    return (activity_clean, date_fields, derived_fields)


def build_player_table(activity_clean, audit, cancellation_date_by_user, checks_folder):
    """Return one row per day-0 player with first Paid/cancellation dates and full declared follow-up. Never infer cancellation from gaps."""
    player_summary = activity_clean.loc[activity_clean.tenure_day.eq(0),
        ["userid", "cohort_date", "plan", "source_row_id"]].rename(columns={
            "plan": "initial_plan", "source_row_id": "day0_source_row_id"
        }).copy()

    event_dates = activity_clean.groupby("userid", as_index=False).agg(
        first_observed_activity_date=("activity_date", "min"),
        last_observed_activity_date=("activity_date", "max"),
    )
    first_paid_dates = activity_clean.loc[activity_clean.plan.eq("Paid")].groupby("userid").activity_date.min()
    event_dates["first_paid_date"] = event_dates.userid.map(first_paid_dates)
    event_dates["cancellation_date"] = event_dates.userid.map(cancellation_date_by_user)
    player_summary = player_summary.merge(event_dates, on="userid", how="left", validate="one_to_one", indicator=True)
    assert player_summary["_merge"].eq("both").all(), "A day-0 player is missing from event history."
    player_summary = player_summary.drop(columns="_merge")
    player_summary["initially_free"] = player_summary.initial_plan.eq("Free")
    player_summary["ever_observed_paid"] = player_summary.first_paid_date.notna()
    player_summary["converted_from_initial_free"] = player_summary.initially_free & player_summary.ever_observed_paid
    player_summary["conversion_date"] = player_summary.first_paid_date.where(player_summary.converted_from_initial_free)
    player_summary["explicit_cancellation_observed"] = player_summary.cancellation_date.notna()
    player_summary["conversion_tenure_day"] = (player_summary.conversion_date - player_summary.cohort_date).dt.days.astype("Int64")
    player_summary["cancellation_tenure_day"] = (player_summary.cancellation_date - player_summary.cohort_date).dt.days.astype("Int64")
    player_summary["window_end_date"] = player_summary.cohort_date + pd.Timedelta(days=59)
    player_summary["source_observation_cutoff"] = pd.Timestamp("2025-05-05")
    player_summary["full_60_day_window_available"] = player_summary.window_end_date.le(player_summary.source_observation_cutoff)
    player_summary["coverage_basis"] = "Complete synthetic file per pinned source README; not last observed activity"
    player_summary = player_summary.sort_values("userid").reset_index(drop=True)
    assert player_summary.userid.is_unique and player_summary.full_60_day_window_available.all()

    audit.record_rule("player_roster_and_events", "Prepare stable cohort denominators and event dates without answering aggregate questions",
                activity_clean, player_summary, len(activity_clean), player_summary.userid.nunique(),
                "Observed player-day -> player; day0/event join one_to_one; unmatched=0; multiplied=0; no excluded players")
    player_fields = [column for column in player_summary if column not in ["userid", "day0_source_row_id"]]
    audit.audit_added_fields(player_summary, player_fields, "player_roster_and_events", "player_summary", "cohort_date")
    player_lineage = activity_clean[["userid", "source_row_id", "activity_date"]].copy()
    player_lineage["is_day0"] = activity_clean.tenure_day.eq(0)
    player_lineage["is_paid_record"] = activity_clean.plan.eq("Paid")
    player_lineage["is_cancellation_record"] = activity_clean.explicit_cancellation
    player_lineage.to_csv(checks_folder / "player_lineage.csv", index=False)
    print(f"Prepared {len(player_summary):,} player records; event flags are saved without aggregate outcome counts.")
    return (player_summary, player_fields)


def build_retention_calendar(activity_clean, audit, feature_columns, player_summary):
    """Expand every day-0 player to days0–59. Keep absent billing/features unknown and audit only the added calendar rows."""
    tenure_days = pd.DataFrame({"tenure_day": np.arange(60)})
    player_day_calendar = player_summary[["userid", "cohort_date", "full_60_day_window_available"]].merge(tenure_days, how="cross")
    player_day_calendar["activity_date"] = player_day_calendar.cohort_date + pd.to_timedelta(player_day_calendar.tenure_day, unit="D")
    source_fields = ["userid", "activity_date", "source_row_id", "plan", "Status", *feature_columns]
    player_day_calendar = player_day_calendar.merge(
        activity_clean[source_fields], on=["userid", "activity_date"],
        how="left", validate="one_to_one", indicator=True,
    )
    player_day_calendar["observed_activity"] = player_day_calendar["_merge"].eq("both")
    player_day_calendar = player_day_calendar.drop(columns="_merge")
    player_day_calendar["source_row_id"] = player_day_calendar.source_row_id.astype("Int64")
    player_day_calendar["tenure_week"] = player_day_calendar.tenure_day // 7 + 1
    player_day_calendar["is_partial_week"] = player_day_calendar.tenure_week.eq(9)
    player_day_calendar["row_origin"] = np.where(player_day_calendar.observed_activity, "source_record", "constructed_no_observed_activity")
    player_day_calendar = player_day_calendar.sort_values(["userid", "tenure_day"]).reset_index(drop=True)

    added_calendar_rows = player_day_calendar.loc[~player_day_calendar.observed_activity]
    for row in added_calendar_rows.itertuples():
        audit.edit_records.append({
            "rule": "retention_calendar", "table": "player_day_calendar", "action": "add_calendar_row",
            "source_row_id": None, "userid": row.userid, "date": row.activity_date.strftime("%Y-%m-%d"),
            "field": "__row__", "before": None,
            "after": json.dumps({"tenure_day": row.tenure_day, "observed_activity": False,
                                  "plan": None, "Status": None, "feature_counts": None}),
        })
    audit.record_rule("retention_calendar", "Preserve full day0 cohort for each tenure day without inventing activity or billing",
                activity_clean, player_day_calendar, len(added_calendar_rows), added_calendar_rows.userid.nunique(),
                f"Player x 60 tenure days; observed matches={len(activity_clean)}; added inactive calendar rows={len(added_calendar_rows)}; source rows unmatched=0; multiplied=0")
    return (player_day_calendar, added_calendar_rows)


def save_prepared_tables(
    activity_clean,
    audit,
    output_folder,
    player_day_calendar,
    player_summary,
    week_windows,
):
    """Save all three Parquet tables and verify save/reload equality; retain the existing reconciliation checks."""
    prepared_tables = {
        "activity_clean": activity_clean,
        "player_summary": player_summary,
        "player_day_calendar": player_day_calendar,
    }
    for name, table in prepared_tables.items():
        destination = output_folder / f"{name}.parquet"
        table.to_parquet(destination, index=False)
        pd.testing.assert_frame_equal(pd.read_parquet(destination), table)
        audit.verify("parquet_roundtrip_" + name, True)
    week_windows.to_csv(output_folder / "week_windows.csv", index=False)
