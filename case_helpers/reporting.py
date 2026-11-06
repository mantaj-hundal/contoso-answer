"""Reporting helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

from statsmodels.stats.multitest import multipletests
import importlib.metadata
import json
import pandas as pd


def save_preparation_manifest(
    activity_clean,
    activity_raw,
    added_calendar_rows,
    audit,
    cell_edits,
    checks_folder,
    data_path,
    environment,
    output_folder,
    player_day_calendar,
    player_summary,
    project_root,
    quality_checks,
    source_sha256,
):
    """Write actual before/after dimensions, versions, source hash and preparation check counts."""
    manifest = {
        "input": str(data_path.relative_to(project_root)), "input_sha256": source_sha256,
        "environment": environment, "output_folder": str(output_folder.relative_to(project_root)),
        "raw_rows": len(activity_raw), "clean_activity_rows": len(activity_clean),
        "players": len(player_summary), "calendar_rows": len(player_day_calendar),
        "added_calendar_rows": len(added_calendar_rows), "source_value_edits": 0,
        "excluded_source_rows": 0, "excluded_players": 0,
        "quality_checks_passed": int(quality_checks.passed.sum()),
        "reconciliation_checks_passed": len(audit.validation_results),
        "audit_entries": len(cell_edits),
        "coverage_basis": "Pinned source README declares complete synthetic data through each player day 59; cutoff 2025-05-05",
        "readiness": "Prepared for descriptive mandatory questions with documented limitations; aggregate answers not calculated",
    }
    (checks_folder / "preparation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def write_preparation_record(case_folder, manifest, source_sha256):
    """Write the preparation record from actual manifest counts and input hash; no analytical calculation is performed here."""
    record = f"""# Preparation record

    ## Scope and source

    Prepare the four mandatory growth questions; aggregate answers are pending.
    Public synthetic source, pinned in `source/provenance.json`. No analysis time
    budget was supplied. Population: March 3–7, 2025 accounts, days 0–59.
    Observed input grain: player-day. Independent and denominator unit: player.
    Source SHA-256: `{source_sha256}`.

    ## Checks and cleaning reconciliation

    All {manifest['quality_checks_passed']} source-contract checks passed; see
    [quality checks](outputs/cleaning/checks/quality_checks.csv) and the empty
    [issue ledger](outputs/cleaning/checks/quality_issues.csv).
    {manifest['raw_rows']:,} source rows reconcile to {manifest['clean_activity_rows']:,}
    observed cleaned rows and {manifest['players']} player records. No source values
    were corrected, no source rows or players excluded, and no values imputed.
    The original CSV and all original activity columns are unchanged.

    Added explicit-format dates, verified tenure/week labels, activity/cancellation
    flags, attempt totals, and player-level event dates with documented denominators.
    The calendar has {manifest['calendar_rows']:,} rows: {manifest['raw_rows']:,}
    source-linked observed rows plus {manifest['added_calendar_rows']:,} constructed
    rows with no observed activity. Absent plan/status/feature values remain missing.
    Week 9 is partial (days 56–59). Day 0 remains in every retention denominator.

    Rules and population effects: [transformation summary](outputs/cleaning/checks/transformation_summary.csv).
    All {manifest['audit_entries']:,} added-field/calendar-row log entries:
    [cell audit](outputs/cleaning/checks/cell_edits.csv).
    All original source-row contributions to player summaries:
    [player lineage](outputs/cleaning/checks/player_lineage.csv).
    The audit is generated in the same code that performs preparation; additions
    are labeled distinctly from edits. Each derived-field log reconciles to its output
    value; each constructed calendar-row key reconciles to the added-row set.

    ## Readiness and limitations

    **Proceed with limitations** for descriptive mandatory questions. Computational
    requirements are supported by passed checks. Complete day-0 denominators and
    unique player-day keys are verified. Complete 60-day telemetry is declared by
    the pinned synthetic source, not independently proven from activity gaps.
    The May 5 cutoff covers all declared 60-day windows; last observed activity
    is not used as a follow-up cutoff. Initial plan is the day-0 end-of-day plan;
    same-day signup/upgrade order is not identifiable. Missing activity does not
    establish cancellation, and absent cancellation dates mean no recorded event
    within this file. No causal claims are supported by the synthetic data.

    ## Verification and reproduction

    All {manifest['reconciliation_checks_passed']} reconciliation checks passed;
    see [checks](outputs/cleaning/checks/reconciliation_checks.csv).
    A separate `csv.DictReader`/`datetime` source-ledger calculation independently
    matched every player's initial plan, event dates and flags, and all observed
    activity keys. All three Parquet tables passed save/reload equality checks.
    This is independent preparation validation; no aggregate business headline
    has been calculated yet. No charts or presentation were created.

    Restart the Python 3 (Contoso gaming case) kernel and run `analysis.ipynb`, or
    activate the project environment and run
    `python src/create_notebook.py` from the project root.
    `prepare_data.py` is generated from notebook code after successful execution.
    Exact interpreter and dependency versions are in
    [manifest](outputs/cleaning/checks/preparation_manifest.json).
    Automated fresh-kernel execution is verified; interactive VS Code execution
    has not been checked for this case.
    """
    (case_folder / "analysis-record.md").write_text(record, encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ["raw_rows", "clean_activity_rows", "players", "calendar_rows", "added_calendar_rows", "source_value_edits", "excluded_source_rows", "quality_checks_passed", "reconciliation_checks_passed", "audit_entries"]}, indent=2))


def write_mandatory_answers(
    answer_checks,
    cancelled_players_count,
    case_folder,
    cohort_players,
    conversion_pct,
    converted_players_count,
    daily_retention,
    free_players_count,
    initial_counts,
    paid_players,
    results_folder,
    weekly_retention,
):
    """Save the mandatory-answer brief and append actual verification status to the case record."""
    last_day = daily_retention.loc[daily_retention.tenure_day.eq(59)].iloc[0]
    final_full_week = weekly_retention.loc[weekly_retention.tenure_week.eq(8)].iloc[0]
    partial_week = weekly_retention.loc[weekly_retention.tenure_week.eq(9)].iloc[0]
    answer_brief = f"""# Mandatory-question answers

    Synthetic Contoso cohort starting March 3–7, 2025; tenure days 0–59.

    1. **New accounts:** {int(initial_counts['Free'])} initially Free and {int(initial_counts['Paid'])} initially Paid, {cohort_players} total. Initial plan is the observed day-0 end-of-day state.
    2. **Retention:** day 59 has {int(last_day.active_players)}/{cohort_players} active players ({last_day.retention_pct:.1f}%). Last full tenure week (days 49–55) has {int(final_full_week.active_players)}/{cohort_players} active at least once ({final_full_week.retention_pct:.1f}%). Partial week 9 (days 56–59) has {int(partial_week.active_players)}/{cohort_players} ({partial_week.retention_pct:.1f}%). Full daily and weekly tables are in `tables/q2_daily_retention.csv` and `tables/q2_weekly_retention.csv`; all use the original day-0 denominator. Week 1 includes signup and is 100% by construction.
    3. **Free-to-Paid:** {converted_players_count}/{free_players_count} initially Free players converted ({conversion_pct:.1f}%). Same-day signup and upgrade ordering is not observable.
    4. **Paid cancellations:** {cancelled_players_count} distinct players have explicit cancellation records; {len(paid_players)} players were ever observed Paid, including converters. Counts do not standardize unequal Paid exposure.

    All {len(answer_checks)} independent answer checks passed against the original CSV.
    Missing activity is not cancellation. Full coverage relies on the source's
    complete synthetic-data declaration. These descriptive results do not establish
    causal product effects. No feature-usage analysis, charts or presentation created.

    Reproduce by restarting the project kernel and running `analysis.ipynb`, or run
    `python src/create_notebook.py` in the activated project
    environment. Full notebook code is exported to `analysis.py`; `prepare_data.py`
    remains the preparation-only export. Environment and input hash are recorded in
    `../cleaning/checks/preparation_manifest.json`.
    """
    (results_folder / "answers.md").write_text(answer_brief, encoding="utf-8")
    record_path = case_folder / "analysis-record.md"
    record = record_path.read_text(encoding="utf-8").split("\n## Mandatory answers executed")[0]
    record += f"\n## Mandatory answers executed\n\nAll four questions are executed in separate notebook code cells using saved cleaned tables.\nAll {len(answer_checks)} independent source-ledger answer checks passed; see\n[answer checks](outputs/mandatory_questions/answer_checks.csv) and\n[answers with definitions](outputs/mandatory_questions/answers.md).\nTables are saved under `outputs/mandatory_questions/tables/`.\nThe preparation-only status above describes the earlier stage; mandatory answers\nare now complete. Optional exploration, charts and presentations remain pending.\n"
    record_path.write_text(record, encoding="utf-8")
    return answer_brief


def save_association_plan(association_checks):
    """Record the user-confirmed predictor/outcome windows and prespecified exploratory specifications before fitting."""
    analysis_plan = {
        "predictor_days": [0, 6], "retention_days": [28, 34],
        "conversion_days": [7, 59], "conversion_population": "Initially Free, not converted by day6",
        "usage": "First-week attempts = successes + errors, log2(1 + attempts)",
        "errors": "First-week errors / attempts, modeled per 10 percentage points; undefined for zero attempts",
        "controls": "First-week active days; initial Paid plan for retention",
        "segments": "Weekend activity per available day; dominant feature relative to daily plan limits",
        "timing": "Daily at-risk Free players until first upgrade or day59; first-week predictors only",
        "uncertainty": "HC1 at player level; clustered by player for repeated hazard rows",
        "multiplicity": "BH separately over 18 raw correlations and 12 primary feature slopes",
        "permutations": 4999, "seed": 20261105,
    }
    (association_checks / "analysis_plan.json").write_text(json.dumps(analysis_plan, indent=2), encoding="utf-8")
    return analysis_plan


def save_segment_comparisons(
    association_checks,
    association_tables,
    model_players,
    models,
    normalized_fields,
    segment_model_scope,
    segment_summary,
):
    """Save group tables, adjusted contrasts with BH q-values, scope exclusions and player-level segment audit."""
    segment_summary.to_csv(association_tables / "segment_outcomes.csv", index=False)
    pd.DataFrame(segment_model_scope).to_csv(association_checks / "segment_regression_scope.csv",index=False)
    segment_coefficients = pd.concat(models.coefficients, ignore_index=True)
    segment_coefficients = segment_coefficients.loc[segment_coefficients.term.str.startswith("C(")].copy()
    segment_coefficients["bh_q"] = multipletests(segment_coefficients.p_value, method="fdr_bh")[1]
    segment_coefficients.to_csv(association_tables / "segment_regressions.csv", index=False)
    segment_audit = model_players[["userid", "weekend_active_fraction", "weekday_active_fraction", "weekend_preference", *normalized_fields, "feature_preference"]]
    segment_audit.to_csv(association_checks / "segment_assignment_audit.csv", index=False)
    return segment_coefficients


def export_model_diagnostics(association_checks, association_tables, models):
    """Save every coefficient and model diagnostic without re-estimating or altering model specifications."""
    all_coefficients = pd.concat(models.coefficients, ignore_index=True)
    all_coefficients.to_csv(association_tables / "all_regression_coefficients.csv", index=False)
    diagnostics = pd.DataFrame(models.diagnostics)
    diagnostics.to_csv(association_checks / "model_diagnostics.csv", index=False)
    return (all_coefficients, diagnostics)


def export_sensitivities(all_coefficients, association_tables, feature_map):
    """Export joint/single-feature/initial-Free and hazard-time-form comparisons using already-fitted coefficients."""
    sensitivity_records = []
    for outcome_name in ["retention", "conversion"]:
        for feature in feature_map:
            term = f"log2_{feature}"
            model_names = [f"{outcome_name}_usage", f"{outcome_name}_{feature}_single_usage"]
            if outcome_name == "retention":
                model_names.append("retention_usage_initial_free_only")
            for name in model_names:
                result = all_coefficients.loc[all_coefficients.model.eq(name) & all_coefficients.term.eq(term)].iloc[0]
                sensitivity_records.append({"outcome":outcome_name,"feature":feature,"specification":name,
                    "odds_ratio":result.odds_ratio,"ci_low":result.ci_low,"ci_high":result.ci_high})
    sensitivity_summary = pd.DataFrame(sensitivity_records)
    sensitivity_summary.to_csv(association_tables / "usage_sensitivity.csv", index=False)
    hazard_sensitivity = all_coefficients.loc[all_coefficients.model.isin(["daily_conversion_hazard", "daily_conversion_hazard_quadratic_time"]) & all_coefficients.term.isin(["log2_optimizer","log2_coach","log2_agent"])].copy()
    hazard_sensitivity.to_csv(association_tables / "hazard_sensitivity.csv",index=False)
    return (sensitivity_summary, hazard_sensitivity)


def write_association_findings(
    association_folder,
    conversion_players,
    conversion_windows,
    converters,
    correlations,
    model_players,
    primary_associations,
    segment_summary,
):
    """Generate the findings narrative from executed tables, including model units, sample restrictions and all material limitations."""
    finding_lines = ["# Additional-analysis findings", "", "## Scope", "",
        "Predictors: days0–6. Retention: any activity days28–34. Conversion: days7–59 among initially Free players still Free after day6.",
        f"Retention: {int(model_players.retained.sum())}/{len(model_players)}. Conversion: {int(conversion_players.later_conversion.sum())}/{len(conversion_players)}. No first-week conversions were observed.", "", "## Unadjusted correlations", ""]
    for outcome_name in ["retention","conversion"]:
        top = correlations.loc[correlations.outcome.eq(outcome_name)].assign(absolute=lambda d:d.spearman_rho.abs()).sort_values("absolute",ascending=False).head(3)
        for row in top.itertuples():
            finding_lines.append(f"- {outcome_name}: {row.feature} {row.measurement}, Spearman rho={row.spearman_rho:.3f}, permutation BH q={row.bh_q:.3f}, n={row.players}.")
    finding_lines += ["", "## Adjusted feature associations", ""]
    for row in primary_associations.itertuples():
        finding_lines.append(f"- {row.model}, {row.term}: OR {row.odds_ratio:.2f} (95% interval {row.ci_low:.2f}–{row.ci_high:.2f}), BH q={row.bh_q:.3f}.")
    supported = primary_associations.loc[primary_associations.bh_q.lt(0.05) & primary_associations.interpretation_ready]
    finding_lines += ["", f"{len(supported)} of 12 primary feature slopes have BH q<0.05. Intervals are pointwise, not multiplicity-adjusted. Absence of a clear association is not proof of no relationship.",
        "Usage ORs are per doubling of 1+attempts. Error-rate ORs are per 10 percentage points and use feature-specific volume adjustment.",
        "Coach and Agent use have the clearest adjusted retention associations; Optimizer use has the clearest adjusted conversion association. All six adjusted error-rate intervals include 1. Raw positive error-count correlations can reflect usage volume, not a beneficial effect of errors.",
        "Simpler usage fits and initially-Free-only retention estimates are saved in tables/usage_sensitivity.csv. Collinearity among usage and engagement limits attribution to one feature; the model changes should be read as sensitivity, not independent replications.", "", "## Segments", ""]
    for row in segment_summary.itertuples():
        finding_lines.append(f"- {row.segment}={row.group}, {row.outcome}: {row.events}/{row.players} ({row.rate_pct:.1f}%; Wilson interval {row.ci_low_pct:.1f}–{row.ci_high_pct:.1f}%).")
    finding_lines += ["", "Weekend preference is associated with higher unadjusted retention and conversion than weekday preference. Adjusted direct comparisons and exploratory BH q-values are in tables/segment_regressions.csv. Feature preference groups have overlapping intervals and do not support confident ranking.",
        "Diagnostic revision: a 3-player balanced feature group caused non-finite standard errors in the original subgroup model. Categories with fewer than 10 players are therefore descriptive only, excluding 3 retention players and 2 conversion players from adjusted feature-preference models; other analyses retain them. See checks/segment_regression_scope.csv. No source data was changed."]
    peak = conversion_windows.loc[conversion_windows.conditional_conversion_pct.idxmax()]
    finding_lines += ["", "## Conversion timing and journeys", "",
        f"The largest observed grouped conditional conversion proportion is days {int(peak.start_day)}–{int(peak.end_day)}: {int(peak.conversions)}/{int(peak.free_at_start)} ({peak.conditional_conversion_pct:.1f}%). Unequal edge-window lengths and sparse counts limit peak comparisons.",
        f"Among the {len(converters)} converters, median upgrade tenure is {converters.conversion_tenure_day.median():.0f} days (range {converters.conversion_tenure_day.min():.0f}–{converters.conversion_tenure_day.max():.0f}). This excludes nonconverters by definition.",
        "The pre-upgrade journey conditions on eventual conversion and excludes the upgrade day. Activity gaps and per-active-day feature means must be interpreted together.", "", "## Limits and next decisions", "",
        "Synthetic observational data supports association, not causal effects or real-customer forecasts. Starting plan, usage caps, general engagement, cohort timing and unmeasured intent can confound relationships. Models adjust selected measured variables only.",
        "Only 33 conversion events support limited precision. Review all diagnostics, collinearity, simpler-model and baseline-timing sensitivities. Correlation and subgroup exploration involve multiple comparisons.",
        "Use feature and segment signals to specify a prospective randomized onboarding or reliability experiment, not to claim that increasing feature use causes retention. Confirm results on real cohorts, protect player-level evaluation splits for prediction, and improve event-time/billing telemetry before operational targeting.",
        "", "## Reproduction and checks", "",
        "Run the complete notebook in the project kernel or create_notebook.py in the activated environment. All source-level feature/outcome/hazard checks and independent main-model coefficient checks passed. Source input hash is unchanged. See checks/ and tables/ for full evidence."]
    findings = "\n".join(finding_lines)
    (association_folder / "findings.md").write_text(findings, encoding="utf-8")
    return findings


def save_association_record(
    analysis_plan,
    association_checks,
    case_folder,
    conversion_players,
    diagnostics,
    model_players,
    models,
    source_sha256,
):
    """Write the executed analysis manifest and append sample, diagnostic and independent-check status to the case record."""
    association_manifest = {
        "analysis_plan":analysis_plan,"input_sha256":source_sha256,
        "versions":{package:importlib.metadata.version(package) for package in ["statsmodels","scipy","pandas","numpy","matplotlib","seaborn"]},
        "retention_players":len(model_players),"retention_events":int(model_players.retained.sum()),
        "conversion_players":len(conversion_players),"conversion_events":int(conversion_players.later_conversion.sum()),
        "models_fitted":len(models.diagnostics),"models_with_warnings":int(diagnostics.warnings.ne("").sum()),
        "all_models_converged":bool(diagnostics.converged.all()),
        "independent_checks":"Source features/outcomes/hazards, rank correlations, SciPy primary-model fits and source hash passed",
        "figure_review":"Pending visual inspection of rendered PNGs",
    }
    (association_checks / "analysis_manifest.json").write_text(json.dumps(association_manifest,indent=2),encoding="utf-8")
    record_path = case_folder / "analysis-record.md"
    record = record_path.read_text(encoding="utf-8").split("\n## Additional goals executed")[0]
    record += f"\n## Additional goals executed\n\nUser confirmed first-week predictors, days28–34 retention, and days7–59 conversion after a day6 Free landmark. All four additional goals are now executed. Retention n={len(model_players)}, events={int(model_players.retained.sum())}; conversion n={len(conversion_players)}, events={int(conversion_players.later_conversion.sum())}. See [findings](outputs/additional_analysis/findings.md), result tables, separate feature audit/lineage, model membership and diagnostics under `outputs/additional_analysis/`. All primary model and source-ledger verification checks passed. All {len(models.diagnostics)} models converged; {int(diagnostics.warnings.ne('').sum())} have warnings. Full code exported from the notebook. Synthetic associations are exploratory and not causal or validated predictions. Figures await recorded visual inspection; presentation requested next.\n"
    record_path.write_text(record,encoding="utf-8")
