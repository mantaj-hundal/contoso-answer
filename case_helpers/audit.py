"""Audit helpers for the Contoso gaming case.

Extracted without changing the original calculations or audit rules.
"""

import pandas as pd


class AuditTrail:
    """Collect source-quality results, transformations and reconciliations.

    The activity frame is the unfiltered source copy with stable row IDs.
    Lists belong to this run, never to module-level or notebook hidden state.
    Every verify() call writes the check ledger before raising on failure.
    """

    def __init__(self, activity, checks_folder):
        self.activity = activity
        self.checks_folder = checks_folder
        self.quality_records = []
        self.quality_issues = []
        self.rule_records = []
        self.edit_records = []
        self.validation_results = []

    def check_rows(self, name, failure_mask, description):
        """Save violations at source-row grain and a count; do not correct records."""
        failed = self.activity.loc[failure_mask.fillna(True)]
        self.quality_records.append({
            "check": name, "description": description,
            "violating_rows": len(failed), "violating_players": failed.userid.nunique(),
            "passed": failed.empty,
        })
        for row in failed.itertuples():
            self.quality_issues.append({"check": name, "source_row_id": row.source_row_id,
                                   "userid": row.userid, "source_date": row.date})

    def check_condition(self, name, condition, description):
        """Record a table-level requirement separately from row-level violations."""
        self.quality_records.append({"check": name, "description": description,
                                "violating_rows": None, "violating_players": None,
                                "passed": bool(condition)})

    def record_rule(self, rule, reason, before, after, affected_rows, affected_players, detail):
        """Record actual input/output grain and row/player population reconciliation."""
        self.rule_records.append({
            "rule": rule, "reason": reason, "affected_rows": int(affected_rows),
            "affected_players": int(affected_players),
            "rows_before": len(before), "rows_after": len(after),
            "players_before": before.userid.nunique(), "players_after": after.userid.nunique(),
            "cohort_denominator_change": int(after.userid.nunique() - before.userid.nunique()),
            "detail": detail,
        })

    def audit_added_fields(self, table, fields, rule, table_name, date_column):
        """Log added values with source keys; player-level values anchor to day 0."""
        for row in table.to_dict("records"):
            for field in fields:
                value = row[field]
                self.edit_records.append({
                    "rule": rule, "table": table_name, "action": "add_derived_field",
                    "source_row_id": row.get("source_row_id", row.get("day0_source_row_id")),
                    "userid": row["userid"], "date": str(row[date_column])[:10],
                    "field": field, "before": None,
                    "after": None if pd.isna(value) else str(value),
                })

    def verify(self, name, condition):
        """Persist each reconciliation result and stop immediately if it fails."""
        self.validation_results.append({"check": name, "passed": bool(condition)})
        pd.DataFrame(self.validation_results).to_csv(self.checks_folder / "reconciliation_checks.csv", index=False)
        assert condition, name


def save_quality_checks(audit, checks_folder):
    """Persist the quality/issue ledgers and stop if any source contract check failed."""
    quality_checks = pd.DataFrame(audit.quality_records)
    quality_checks.to_csv(checks_folder / "quality_checks.csv", index=False)
    pd.DataFrame(audit.quality_issues, columns=["check", "source_row_id", "userid", "source_date"]).to_csv(checks_folder / "quality_issues.csv", index=False)
    assert quality_checks.passed.all(), "Contract check failed: inspect quality_checks.csv and quality_issues.csv before continuing."
    print("All source-contract checks passed. No exclusions, imputations, or source-value corrections are required.")
    return quality_checks


def reconcile_added_fields(
    activity_clean,
    added_calendar_rows,
    audit,
    checks_folder,
    date_fields,
    derived_fields,
    player_fields,
    player_summary,
):
    """Reconcile every derived-cell addition and constructed calendar key to outputs, then save the detailed audit and rule summary."""
    cell_edits = pd.DataFrame(audit.edit_records)
    cell_edits["source_row_id"] = cell_edits.source_row_id.astype("Int64")
    audit.verify("no_original_value_edits_or_exclusions", cell_edits.action.isin(["add_derived_field", "add_calendar_row"]).all())
    audit.verify("calendar_addition_audit_reconciles", cell_edits.action.eq("add_calendar_row").sum() == len(added_calendar_rows))

    # Reconcile every logged derived cell back to its prepared value and key.
    for table_name, prepared, key_column in [
        ("activity_clean", activity_clean, "source_row_id"),
        ("player_summary", player_summary, "day0_source_row_id"),
    ]:
        lookup = prepared.set_index(key_column)
        logged = cell_edits.loc[cell_edits.table.eq(table_name)]
        expected_fields = (["source_row_id", *date_fields, *derived_fields]
                           if table_name == "activity_clean" else player_fields)
        assert len(logged) == len(prepared) * len(expected_fields)
        assert not logged.duplicated(["source_row_id", "field"]).any()
        for edit in logged.itertuples():
            assert edit.field in expected_fields
            if edit.field == key_column:
                actual = edit.source_row_id
            else:
                actual = lookup.at[edit.source_row_id, edit.field]
            recorded = edit.after
            assert (pd.isna(actual) and pd.isna(recorded)) or str(actual) == recorded
            assert lookup.at[edit.source_row_id, "userid"] == edit.userid
    audit.verify("all_derived_cell_audits_reconcile", True)

    calendar_audit_keys = set(zip(
        cell_edits.loc[cell_edits.action.eq("add_calendar_row"), "userid"],
        cell_edits.loc[cell_edits.action.eq("add_calendar_row"), "date"],
    ))
    expected_added_keys = set(zip(added_calendar_rows.userid, added_calendar_rows.activity_date.dt.strftime("%Y-%m-%d")))
    audit.verify("added_calendar_key_audit_reconciles", calendar_audit_keys == expected_added_keys)

    transformation_summary = pd.DataFrame(audit.rule_records)
    audit.verify("no_player_denominator_changes", transformation_summary.cohort_denominator_change.eq(0).all())
    transformation_summary.to_csv(checks_folder / "transformation_summary.csv", index=False)
    cell_edits.to_csv(checks_folder / "cell_edits.csv", index=False)
    return (cell_edits, transformation_summary)


def save_first_week_lineage(
    association_checks,
    calendar,
    conversion_players,
    early_activity,
    early_features,
    feature_map,
    model_players,
):
    """Save source contributors, derived feature values and per-player outcome/error-model membership."""
    # The aggregation ledger retains all source contributors and the exact new values.
    feature_lineage = early_activity[["source_row_id", "userid", "tenure_day"]].copy()
    feature_lineage.to_csv(association_checks / "first_week_source_lineage.csv", index=False)
    feature_audit = early_features.melt(id_vars="userid", var_name="field", value_name="after")
    feature_audit["rule"] = "Aggregate validated observed days0–6; error rate undefined when no attempts"
    feature_audit["action"] = "add_player_feature"
    feature_audit["before"] = None
    feature_audit.to_csv(association_checks / "derived_feature_audit.csv", index=False)
    sample_membership = model_players[["userid", "initial_plan", "conversion_eligible", "retained", "later_conversion"]].copy()
    for feature in feature_map:
        sample_membership[f"{feature}_error_model_eligible"] = model_players[f"{feature}_attempts"].gt(0)
    sample_membership.to_csv(association_checks / "sample_membership.csv", index=False)
    pd.DataFrame([
        {"rule": "first_week_aggregation", "source_rows": len(early_activity), "output_players": len(early_features), "excluded_players": 0, "reason": "One row per player; original values untouched"},
        {"rule": "retention_label", "source_rows": len(calendar.loc[calendar.tenure_day.between(28, 34)]), "output_players": len(model_players), "excluded_players": 0, "reason": "Any observed activity days28–34; full source-declared coverage"},
        {"rule": "conversion_landmark", "source_rows": len(model_players), "output_players": len(conversion_players), "excluded_players": len(model_players)-len(conversion_players), "reason": "Exclude initially Paid and conversions by day6"},
    ]).to_csv(association_checks / "transformation_summary.csv", index=False)
    return feature_audit
