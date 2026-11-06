# Data and audit guide

The complete original field dictionary and product limits are in
[source/README.md](../source/README.md).

| Prepared file | Grain and key | Purpose |
| --- | --- | --- |
| outputs/cleaning/activity_clean.parquet | Observed player-day, userid + activity_date | Original columns plus derived dates, tenure, activity/cancellation flags and attempt totals |
| outputs/cleaning/player_summary.parquet | Player, userid | Day-0 plan, first Paid date, conversion and explicit cancellation dates/flags, declared follow-up |
| outputs/cleaning/player_day_calendar.parquet | Player-day, userid + tenure_day | Days 0–59 with observed_activity and row_origin; absent plan/status/counts remain missing |
| outputs/additional_analysis/player_model_inputs.parquet | Player, userid | First-week predictors, later outcomes and segment assignments |

Load Parquet files using `pd.read_parquet(...)` to preserve types. In player
summaries, a missing event date means not recorded during this file. It does not
mean the event can never occur. `last_observed_activity_date` is not a coverage
cutoff; `full_60_day_window_available` uses the source-declared observation window.

## Audit trail

- `outputs/cleaning/checks/transformation_summary.csv`: each rule, rationale,
  affected rows/players, before/after counts and denominator impact.
- `outputs/cleaning/checks/cell_edits.csv`: 102,800 added-field/calendar-row log
  entries, labeled separately from corrections. Every addition reconciles to output.
- `outputs/cleaning/checks/player_lineage.csv`: source rows contributing to players.
- `outputs/cleaning/checks/quality_checks.csv` and `quality_issues.csv`: 29 passed
  source-contract checks and an empty issue ledger with headers.
- `outputs/cleaning/checks/reconciliation_checks.csv`: 20 preparation checks.
- `outputs/additional_analysis/checks/derived_feature_audit.csv` and
  `first_week_source_lineage.csv`: added first-week features and source contributors.
- `outputs/additional_analysis/checks/sample_membership.csv`: individual main-model
  and error-model eligibility, including zero-attempt exclusions.
- `outputs/additional_analysis/checks/segment_assignment_audit.csv` and
  `segment_regression_scope.csv`: segment rules, assignments and sparse-group scope.
- `outputs/additional_analysis/checks/model_diagnostics.csv`: formula, sample,
  events, parameters, convergence, rank, condition number, VIF and warnings.

Result tables, PNG figures and generated findings are under the corresponding
`outputs/mandatory_questions/` and `outputs/additional_analysis/` folders.
