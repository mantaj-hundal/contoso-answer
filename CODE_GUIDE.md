# Reading and running the code

Start with [analysis.ipynb](analysis.ipynb). Its cells follow the question,
definition, calculation, result and interpretation sequence. Important formulas
and the four mandatory answers remain visible. Repeated implementation details
are named functions with explicit inputs rather than long notebook blocks.

| Module | Responsibility | Useful entry points |
| --- | --- | --- |
| [audit.py](case_helpers/audit.py) | Record and reconcile the cleaning trail | `AuditTrail`, `reconcile_added_fields`, `save_first_week_lineage` |
| [preparation.py](case_helpers/preparation.py) | Prepare observed activity, players and calendar | `derive_activity_fields`, `build_player_table`, `build_retention_calendar` |
| [metrics.py](case_helpers/metrics.py) | Cohort metrics and conversion journeys | `retention_tables`, `conversion_risk_sets`, `preconversion_journeys` |
| [features.py](case_helpers/features.py) | Pre-outcome features and descriptive associations | `first_week_features`, `define_later_outcomes`, `correlate_features_and_outcomes`, `assign_player_segments` |
| [modeling.py](case_helpers/modeling.py) | Logistic fits and prespecified comparisons | `RegressionCollection`, `fit_error_models`, `fit_segment_comparisons` |
| [validation.py](case_helpers/validation.py) | Source contracts and independent checks | `check_dates_and_cohort`, `verify_player_events`, `verify_regression_optimizers` |
| [plotting.py](case_helpers/plotting.py) | Reproduce the three analytical figures | `correlation_heatmap`, `feature_association_intervals`, `conversion_timing_and_journey` |
| [reporting.py](case_helpers/reporting.py) | Write manifests, narratives and model tables | `write_mandatory_answers`, `export_model_diagnostics`, `write_association_findings` |

There are two stateful classes. `AuditTrail` owns one run's quality checks,
transformations and reconciliation records. `RegressionCollection` owns fitted
models, coefficient tables and diagnostics. The remaining data operations are
ordinary functions; there is no analysis framework or hidden global registry.

Functions that add columns or append audit/model records do so explicitly through
their arguments. Their docstrings explain grain, purpose and important assumptions.
Open a named function in the linked module to inspect the actual calculation.

`notebook_template.ipynb` is the annotated, unexecuted notebook source. Run
`python src/create_notebook.py` from this case folder, or run its project-relative
path from the project root, to execute it in a fresh project kernel. Successful
execution writes `analysis.ipynb` and generates `analysis.py` and `prepare_data.py`
from the same cells. The preparation export uses cell-stage metadata, not a fixed
cell-number cutoff. All three entry points require the adjacent `case_helpers/`.

This is a structural refactor: definitions, input population, cleaning rules,
model specifications, random seed, numerical results and audit coverage are
preserved. The readability check compares outputs against the original submission.
