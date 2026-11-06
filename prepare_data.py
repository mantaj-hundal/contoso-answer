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
