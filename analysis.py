# Generated from analysis.ipynb. Rebuild with python src/create_notebook.py.

# %%
from pathlib import Path
import hashlib
import importlib.metadata
import platform
import sys

import numpy as np
import pandas as pd
from IPython.display import display

project_root = next(
    folder for folder in [Path.cwd(), *Path.cwd().parents]
    if (folder / "submission.json").is_file()
)
case_folder = project_root
data_path = project_root / "data" / "contoso_gaming_pc_app_output.csv"

# %%
environment = {
    "interpreter": sys.executable,
    "Python": platform.python_version(),
}
for package in ["pandas", "numpy", "matplotlib", "seaborn", "nbformat", "nbclient"]:
    environment[package] = importlib.metadata.version(package)
display(pd.Series(environment, name="Installed version or path"))

# Helpers contain the audited transformations and checks; see CODE_GUIDE.md.
sys.path.insert(0, str(case_folder))
from case_helpers import audit as audit_helpers
from case_helpers import preparation, validation, metrics, features, modeling, plotting, reporting
from case_helpers.audit import AuditTrail
from case_helpers.modeling import RegressionCollection
from collections import Counter, defaultdict
from IPython.display import Markdown

# %%
source_sha256 = hashlib.sha256(data_path.read_bytes()).hexdigest()
activity_raw = pd.read_csv(data_path)

print(f"Source: {data_path.relative_to(project_root)}")
print(f"SHA-256: {source_sha256}")
print(f"Loaded table: {activity_raw.shape[0]:,} rows × {activity_raw.shape[1]} columns")

# %%
with pd.option_context("display.max_columns", None, "display.max_colwidth", 40):
    display(activity_raw.head(5))

display(activity_raw.dtypes.rename("Loaded dtype").to_frame())

# %%
output_folder = case_folder / "outputs" / "cleaning"
checks_folder = output_folder / "checks"
checks_folder.mkdir(parents=True, exist_ok=True)

# Work on a copy and retain a permanent reference to every CSV data record.
original_columns = activity_raw.columns.tolist()
activity_clean = activity_raw.copy(deep=True)
activity_clean.insert(0, "source_row_id", np.arange(1, len(activity_clean) + 1))
audit = AuditTrail(activity_clean, checks_folder)
audit.record_rule("source_lineage", "Trace every source record without modifying inputs",
    activity_raw, activity_clean, len(activity_clean), activity_clean.userid.nunique(),
    "Added 1-based CSV data-record ID; no filtering or source-value edits")
audit.audit_added_fields(activity_clean, ["source_row_id"], "source_lineage", "activity_clean", "date")

# Parse dates explicitly while preserving the original text fields.
activity_clean["activity_date"] = pd.to_datetime(activity_clean.date, format="%m/%d/%Y", errors="coerce")
activity_clean["cohort_date"] = pd.to_datetime(activity_clean.startdate, format="%m/%d/%Y", errors="coerce")
activity_clean["tenure_day"] = (activity_clean.activity_date - activity_clean.cohort_date).dt.days

# %%
validation.check_dates_and_cohort(
    activity_clean=activity_clean,
    activity_raw=activity_raw,
    audit=audit,
)

feature_columns = validation.check_feature_limits(
    activity_clean=activity_clean,
    audit=audit,
    original_columns=original_columns,
)

cancellation_date_by_user = validation.check_billing_history(activity_clean=activity_clean, audit=audit)

# %%
quality_checks = audit_helpers.save_quality_checks(audit=audit, checks_folder=checks_folder)

display(quality_checks)

# %%
activity_clean, date_fields, derived_fields = preparation.derive_activity_fields(
    activity_clean=activity_clean,
    activity_raw=activity_raw,
    audit=audit,
)

display(activity_clean.head(5))

# %%
player_summary, player_fields = preparation.build_player_table(
    activity_clean=activity_clean,
    audit=audit,
    cancellation_date_by_user=cancellation_date_by_user,
    checks_folder=checks_folder,
)

display(player_summary[["userid", "cohort_date", "initial_plan", "window_end_date"]].head())

# %%
player_day_calendar, added_calendar_rows = preparation.build_retention_calendar(
    activity_clean=activity_clean,
    audit=audit,
    feature_columns=feature_columns,
    player_summary=player_summary,
)

# %%
week_windows = pd.DataFrame({"tenure_week": np.arange(1, 10)})
week_windows["start_day_inclusive"] = (week_windows.tenure_week - 1) * 7
week_windows["end_day_inclusive"] = (week_windows.start_day_inclusive + 6).clip(upper=59)
week_windows["days_in_window"] = week_windows.end_day_inclusive - week_windows.start_day_inclusive + 1
week_windows["is_partial_week"] = week_windows.days_in_window.lt(7)
display(week_windows)
print(f"Prepared {len(player_day_calendar):,} player-days; {len(added_calendar_rows):,} constructed rows clearly labeled.")

# %%
validation.verify_preservation_and_calendar(
    activity_clean=activity_clean,
    activity_raw=activity_raw,
    added_calendar_rows=added_calendar_rows,
    audit=audit,
    data_path=data_path,
    feature_columns=feature_columns,
    original_columns=original_columns,
    player_day_calendar=player_day_calendar,
    player_summary=player_summary,
    source_sha256=source_sha256,
)

# %%
source_ledger, source_keys = validation.read_player_ledger(data_path=data_path)

validation.verify_player_events(
    audit=audit,
    player_day_calendar=player_day_calendar,
    player_summary=player_summary,
    source_keys=source_keys,
    source_ledger=source_ledger,
)

# %%
cell_edits, transformation_summary = audit_helpers.reconcile_added_fields(
    activity_clean=activity_clean,
    added_calendar_rows=added_calendar_rows,
    audit=audit,
    checks_folder=checks_folder,
    date_fields=date_fields,
    derived_fields=derived_fields,
    player_fields=player_fields,
    player_summary=player_summary,
)

display(transformation_summary)
display(pd.DataFrame(audit.validation_results))

# %%
preparation.save_prepared_tables(
    activity_clean=activity_clean,
    audit=audit,
    output_folder=output_folder,
    player_day_calendar=player_day_calendar,
    player_summary=player_summary,
    week_windows=week_windows,
)

# %%
manifest = reporting.save_preparation_manifest(
    activity_clean=activity_clean,
    activity_raw=activity_raw,
    added_calendar_rows=added_calendar_rows,
    audit=audit,
    cell_edits=cell_edits,
    checks_folder=checks_folder,
    data_path=data_path,
    environment=environment,
    output_folder=output_folder,
    player_day_calendar=player_day_calendar,
    player_summary=player_summary,
    project_root=project_root,
    quality_checks=quality_checks,
    source_sha256=source_sha256,
)

reporting.write_preparation_record(
    case_folder=case_folder,
    manifest=manifest,
    source_sha256=source_sha256,
)

# %%
# Reload the saved player table so these answers use the cleaned outputs.
players = pd.read_parquet(output_folder / "player_summary.parquet")
assert players.userid.is_unique, "Player summary must contain exactly one row per player."
assert players.cohort_date.between("2025-03-03", "2025-03-07").all()
assert players.full_60_day_window_available.all(), "Review incomplete follow-up before answering."

results_folder = case_folder / "outputs" / "mandatory_questions"
tables_folder = results_folder / "tables"
tables_folder.mkdir(parents=True, exist_ok=True)

new_accounts = players.groupby("initial_plan").size().reindex(["Free", "Paid"], fill_value=0)
new_accounts = new_accounts.rename("new_players").rename_axis("initial_plan").reset_index()
new_accounts_by_date = pd.crosstab(players.cohort_date, players.initial_plan)
new_accounts_by_date = new_accounts_by_date.reindex(columns=["Free", "Paid"], fill_value=0)
new_accounts_by_date["Total"] = new_accounts_by_date.sum(axis=1)
assert new_accounts.new_players.sum() == len(players), "Starting-plan counts must cover the entire cohort."

display(new_accounts)
display(new_accounts_by_date)
initial_counts = new_accounts.set_index("initial_plan").new_players
print(f"Answer: {initial_counts['Free']:,} initially Free and {initial_counts['Paid']:,} initially Paid players; {len(players):,} total.")
print("These are observed day-0 end-of-day plans, not separately logged signup-plan events.")
new_accounts.to_csv(tables_folder / "q1_new_accounts.csv", index=False)
new_accounts_by_date.to_csv(tables_folder / "q1_new_accounts_by_date.csv")

# %%
calendar = pd.read_parquet(output_folder / "player_day_calendar.parquet")
assert not calendar.duplicated(["userid", "tenure_day"]).any()
assert set(calendar.userid) == set(players.userid)
assert calendar.groupby("userid").size().eq(60).all()
assert calendar.full_60_day_window_available.all()
cohort_players = len(players)

daily_retention, weekly_retention = metrics.retention_tables(
    calendar=calendar,
    cohort_players=cohort_players,
    output_folder=output_folder,
)

print("Daily retention — active on that exact tenure day:")
with pd.option_context("display.max_rows", 60):
    display(daily_retention.style.format({"retention_pct": "{:.1f}%"}))
print("Weekly retention — active at least once in the indicated tenure-day window:")
display(weekly_retention.style.format({"retention_pct": "{:.1f}%"}))
for day in [1, 7, 14, 30, 59]:
    result = daily_retention.loc[daily_retention.tenure_day.eq(day)].iloc[0]
    print(f"Day {day}: {int(result.active_players):,}/{cohort_players:,} active ({result.retention_pct:.1f}%).")
print("Day 7 retention is exact-day activity; week 2 retention covers any activity on days 7–13.")
print("Week 1 includes day 0. The partial final week has fewer chances to observe a return than a full week.")
daily_retention.to_csv(tables_folder / "q2_daily_retention.csv", index=False)
weekly_retention.to_csv(tables_folder / "q2_weekly_retention.csv", index=False)

# %%
initially_free_players = players.loc[players.initially_free].copy()
free_players_count = len(initially_free_players)
converted_players_count = int(initially_free_players.converted_from_initial_free.sum())
conversion_pct = 100 * converted_players_count / free_players_count if free_players_count else np.nan

conversion_summary = pd.DataFrame([{
    "initially_free_players": free_players_count,
    "converted_to_paid_players": converted_players_count,
    "not_observed_converted_players": free_players_count - converted_players_count,
    "conversion_pct": conversion_pct,
    "tenure_window": "days 0–59; conversion after observed day-0 Free state",
}])
display(conversion_summary.style.format({"conversion_pct": "{:.1f}%"}))
print(f"Answer: {converted_players_count:,} of {free_players_count:,} initially Free players upgraded; conversion = {conversion_pct:.1f}%.")
print("The remaining players were not observed converting within this window; this does not mean they can never convert.")
conversion_summary.to_csv(tables_folder / "q3_free_to_paid_conversion.csv", index=False)

# %%
paid_players = players.loc[players.ever_observed_paid].copy()
assert not players.loc[players.explicit_cancellation_observed, "ever_observed_paid"].eq(False).any()
cancelled_players_count = int(paid_players.explicit_cancellation_observed.sum())

cancellation_summary = pd.DataFrame([{
    "ever_observed_paid_players": len(paid_players),
    "explicitly_cancelled_players": cancelled_players_count,
    "no_recorded_cancellation_players": len(paid_players) - cancelled_players_count,
}])
cancellations_by_starting_plan = paid_players.groupby("initial_plan", as_index=False).agg(
    ever_observed_paid_players=("userid", "size"),
    explicitly_cancelled_players=("explicit_cancellation_observed", "sum"),
)
assert cancellations_by_starting_plan.explicitly_cancelled_players.sum() == cancelled_players_count
display(cancellation_summary)
display(cancellations_by_starting_plan)
print(f"Answer: {cancelled_players_count:,} distinct Paid players have explicit cancellation records within days 0–59.")
print("Paid players include both day-0 Paid accounts and subsequent Free-to-Paid converters.")
print("No recorded cancellation is not proof of current subscription status after the file ends; missing activity alone is not cancellation.")
cancellation_summary.to_csv(tables_folder / "q4_paid_cancellations.csv", index=False)
cancellations_by_starting_plan.to_csv(tables_folder / "q4_cancellations_by_starting_plan.csv", index=False)

# %%
answer_checks = validation.verify_mandatory_answers(
    cancelled_players_count=cancelled_players_count,
    conversion_pct=conversion_pct,
    converted_players_count=converted_players_count,
    daily_retention=daily_retention,
    data_path=data_path,
    free_players_count=free_players_count,
    initial_counts=initial_counts,
    paid_players=paid_players,
    results_folder=results_folder,
    source_sha256=source_sha256,
    weekly_retention=weekly_retention,
)

display(pd.DataFrame([{"check": name, "passed": passed} for name, passed in answer_checks.items()]))

# %%
answer_brief = reporting.write_mandatory_answers(
    answer_checks=answer_checks,
    cancelled_players_count=cancelled_players_count,
    case_folder=case_folder,
    cohort_players=cohort_players,
    conversion_pct=conversion_pct,
    converted_players_count=converted_players_count,
    daily_retention=daily_retention,
    free_players_count=free_players_count,
    initial_counts=initial_counts,
    paid_players=paid_players,
    results_folder=results_folder,
    weekly_retention=weekly_retention,
)

display(Markdown(answer_brief))

# %%
association_folder = case_folder / "outputs" / "additional_analysis"
association_tables = association_folder / "tables"
association_checks = association_folder / "checks"
association_figures = association_folder / "figures"
for folder in [association_tables, association_checks, association_figures]:
    folder.mkdir(parents=True, exist_ok=True)

analysis_plan = reporting.save_association_plan(association_checks=association_checks)

activity = pd.read_parquet(output_folder / "activity_clean.parquet")
roster = pd.read_parquet(output_folder / "player_summary.parquet")
calendar = pd.read_parquet(output_folder / "player_day_calendar.parquet")

# %%
early_activity, early_features, feature_map = features.first_week_features(activity=activity)

model_players, conversion_players, samples, sample_summary = features.define_later_outcomes(
    association_tables=association_tables,
    calendar=calendar,
    early_features=early_features,
    roster=roster,
)

display(sample_summary)

# %%
feature_audit = audit_helpers.save_first_week_lineage(
    association_checks=association_checks,
    calendar=calendar,
    conversion_players=conversion_players,
    early_activity=early_activity,
    early_features=early_features,
    feature_map=feature_map,
    model_players=model_players,
)

# %%
profile_fields = ["active_days"] + [f"{feature}_{suffix}" for feature in feature_map for suffix in ["attempts", "errors", "error_rate"]]
feature_profile = model_players[profile_fields].describe().T
feature_profile["missing_players"] = model_players[profile_fields].isna().sum()
feature_profile.to_csv(association_tables / "first_week_feature_profile.csv")
display(feature_profile)

# %%
correlations = features.correlate_features_and_outcomes(
    association_tables=association_tables,
    feature_map=feature_map,
    samples=samples,
)

display(correlations.round(4))

# %%
plotting.correlation_heatmap(
    association_figures=association_figures,
    association_tables=association_tables,
    correlations=correlations,
)

# %%
from statsmodels.stats.multitest import multipletests

# The collection records each fit and its diagnostics; formulas remain visible.
models = RegressionCollection()
usage_terms = "log2_optimizer + log2_coach + log2_agent + active_days"
retention_formula = "retained ~ " + usage_terms + " + initial_paid"
conversion_formula = "later_conversion ~ " + usage_terms
print("Retention model:", retention_formula)
print("Conversion model:", conversion_formula)

# %%
retention_usage = models.fit("retention_usage", model_players, retention_formula)
conversion_usage = models.fit("conversion_usage", conversion_players, conversion_formula)
primary_usage = pd.concat([retention_usage, conversion_usage], ignore_index=True)
primary_usage = primary_usage.loc[primary_usage.term.isin(["log2_optimizer", "log2_coach", "log2_agent"])].copy()
display(primary_usage[["model", "term", "odds_ratio", "ci_low", "ci_high", "p_value"]].round(4))
primary_usage.to_csv(association_tables / "usage_regression_coefficients.csv", index=False)

# %%
modeling.fit_usage_sensitivities(
    feature_map=feature_map,
    models=models,
    samples=samples,
    usage_terms=usage_terms,
)

# %%
primary_errors, error_samples = modeling.fit_error_models(feature_map=feature_map, models=models, samples=samples)

display(pd.DataFrame(error_samples))
display(primary_errors[["model", "term", "odds_ratio", "ci_low", "ci_high", "p_value"]].round(4))
pd.DataFrame(error_samples).to_csv(association_tables / "error_model_samples.csv", index=False)
primary_errors.to_csv(association_tables / "error_regression_coefficients.csv", index=False)
primary_associations = pd.concat([primary_usage, primary_errors], ignore_index=True)
primary_associations["bh_q"] = multipletests(primary_associations.p_value, method="fdr_bh")[1]
primary_associations.to_csv(association_tables / "primary_associations.csv", index=False)
display(primary_associations[["model", "term", "odds_ratio", "ci_low", "ci_high", "p_value", "bh_q"]].round(4))

# %%
plotting.feature_association_intervals(
    association_figures=association_figures,
    primary_associations=primary_associations,
)

# %%
model_players, conversion_players, normalized_fields = features.assign_player_segments(
    early_activity=early_activity,
    feature_map=feature_map,
    model_players=model_players,
)

# %%
segment_summary, segment_model_scope = modeling.fit_segment_comparisons(
    conversion_players=conversion_players,
    model_players=model_players,
    models=models,
)

segment_coefficients = reporting.save_segment_comparisons(
    association_checks=association_checks,
    association_tables=association_tables,
    model_players=model_players,
    models=models,
    normalized_fields=normalized_fields,
    segment_model_scope=segment_model_scope,
    segment_summary=segment_summary,
)

display(segment_summary.round(2))
display(pd.DataFrame(segment_model_scope))
display(segment_coefficients[["model", "term", "odds_ratio", "ci_low", "ci_high", "bh_q"]].round(4))

# %%
initial_free_roster, conversion_hazard, conversion_windows = metrics.conversion_risk_sets(
    association_tables=association_tables,
    model_players=model_players,
)

display(conversion_windows.round(2))

# %%
risk_days = features.at_risk_player_days(conversion_players=conversion_players)

# %%
hazard_formula = "converted_today ~ log_tenure_day + log2_optimizer + log2_coach + log2_agent + active_days"
hazard_coefficients = models.fit("daily_conversion_hazard", risk_days, hazard_formula, cluster_column="userid")
hazard_coefficients.to_csv(association_tables / "conversion_hazard_regression.csv", index=False)
display(hazard_coefficients[["term", "odds_ratio", "ci_low", "ci_high", "p_value"]].round(4))
print("Hazard ORs refer to conditional daily conversion odds, not 53-day cumulative conversion probabilities.")

# %%
converters, journey_summary = metrics.preconversion_journeys(
    activity=activity,
    association_tables=association_tables,
    calendar=calendar,
    initial_free_roster=initial_free_roster,
)

display(journey_summary.round(2))

# %%
plotting.conversion_timing_and_journey(
    association_figures=association_figures,
    conversion_windows=conversion_windows,
    journey_summary=journey_summary,
)

# %%
risk_days["log_tenure_centered"] = risk_days.log_tenure_day - risk_days.log_tenure_day.mean()
risk_days["log_tenure_squared"] = risk_days.log_tenure_centered ** 2
models.fit("daily_conversion_hazard_quadratic_time", risk_days,
    hazard_formula.replace("log_tenure_day", "log_tenure_centered") + " + log_tenure_squared", cluster_column="userid")

# %%
all_coefficients, diagnostics = reporting.export_model_diagnostics(
    association_checks=association_checks,
    association_tables=association_tables,
    models=models,
)

sensitivity_summary, hazard_sensitivity = reporting.export_sensitivities(
    all_coefficients=all_coefficients,
    association_tables=association_tables,
    feature_map=feature_map,
)

display(diagnostics[["model", "players", "events", "parameters", "converged", "max_vif", "warnings"]].round(2))
display(sensitivity_summary.round(3))

# %%
source_later_converters = validation.verify_features_and_risk_sets(
    conversion_hazard=conversion_hazard,
    conversion_players=conversion_players,
    data_path=data_path,
    feature_map=feature_map,
    model_players=model_players,
)

validation.verify_rank_correlations(correlations=correlations, samples=samples)

# %%
validation.verify_regression_optimizers(association_checks=association_checks, models=models)

validation.verify_final_analysis_population(
    association_folder=association_folder,
    conversion_windows=conversion_windows,
    converters=converters,
    data_path=data_path,
    early_features=early_features,
    feature_audit=feature_audit,
    model_players=model_players,
    risk_days=risk_days,
    source_later_converters=source_later_converters,
    source_sha256=source_sha256,
)

# %%
findings = reporting.write_association_findings(
    association_folder=association_folder,
    conversion_players=conversion_players,
    conversion_windows=conversion_windows,
    converters=converters,
    correlations=correlations,
    model_players=model_players,
    primary_associations=primary_associations,
    segment_summary=segment_summary,
)

reporting.save_association_record(
    analysis_plan=analysis_plan,
    association_checks=association_checks,
    case_folder=case_folder,
    conversion_players=conversion_players,
    diagnostics=diagnostics,
    model_players=model_players,
    models=models,
    source_sha256=source_sha256,
)

display(Markdown(findings))
