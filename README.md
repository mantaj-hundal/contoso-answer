# Contoso AI Gaming Companion: interview submission

This submission contains the executed analysis, reproducible Python code, original
synthetic input, cleaning audit, checked results and a concise presentation.

## Start here

1. Open [analysis.ipynb](analysis.ipynb) to read the complete analysis with saved
   outputs. No execution is required to review it.
2. Read [methods and definitions](docs/METHODS.md) for populations, time windows,
   model specifications and limitations.
3. Open [the 12-slide presentation](presentation/contoso_growth_analysis.pptx)
   for the leadership findings and brief technical discussion.
4. Use [analysis.py](analysis.py) for a plain Python view of exactly the notebook's
   code, or [prepare_data.py](prepare_data.py) for the preparation stage alone.
5. Use [CODE_GUIDE.md](CODE_GUIDE.md) to find the named function behind each short
   notebook cell. `AuditTrail` owns audit records and `RegressionCollection` owns
   model fits. The cells keep the questions, formulas and result displays visible.

## Main results

| Question | Result |
| --- | --- |
| Starting Free / Paid accounts | 232 / 68, 300 total |
| Exact-day retention at day 59 | 87 / 300 = 29.0% |
| Last full tenure-week retention, days 49–55 | 137 / 300 = 45.7% |
| Initially Free players observed upgrading | 33 / 232 = 14.2% |
| Explicit Paid cancellations | 16, including 13 initially Paid and 3 converters |

The additional analysis uses first-week predictors (days 0–6), retention during
days 28–34, and later conversion during days 7–59. Coach and Agent usage have the
clearest adjusted retention associations; Optimizer usage has the clearest
adjusted conversion association. Adjusted error-rate relationships are inconclusive.
These are exploratory associations in synthetic data, not identified causal effects.

## Reproduce the analysis

Use Python 3.12 and run commands from this extracted folder. Dependencies and
data are local to this submission; no downloads are performed by the analysis.
Installing dependencies requires a package index connection.

```text
conda env create -f environment.yml
conda activate contoso-gaming-case
python analysis.py
```

For the interactive notebook:

```text
python -m ipykernel install --user --name contoso-gaming-case --display-name "Python (Contoso gaming case)"
jupyter lab analysis.ipynb
```

Select that kernel, then **Restart Kernel and Run All**. The source notebook is
the entry point; `analysis.py` contains the same code in the same order. Named
implementation functions are in `case_helpers/`. To regenerate the notebook from
its annotated template and execute it automatically:

```text
python src/create_notebook.py
```

This defaults to the environment's `python3` Jupyter kernel. Set the
`CONTOSO_KERNEL` environment variable to `contoso-gaming-case` to use the explicitly
registered kernel instead. The builder regenerates both Python exports after
successful execution. A rerun replaces generated outputs and records paths for
the current machine; preserve this ZIP if you want the submitted snapshot.

## Folder guide

```text
analysis.ipynb              Executed narrative and results
analysis.py                 Full notebook code export
prepare_data.py             Preparation-only code export
notebook_template.ipynb      Short-cell notebook source without saved outputs
case_helpers/               Documented preparation, metrics, models and checks
src/                        Notebook rebuild and execution entry point
CODE_GUIDE.md               Map from notebook stages to implementation functions
data/                       Unmodified synthetic source CSV
source/                     Assignment, source license and pinned provenance
outputs/cleaning/           Prepared data, rules, lineage and detailed audit
outputs/mandatory_questions/ Counts, rates and independent checks
outputs/additional_analysis/ Models, correlations, groups, timing and figures
presentation/               Final PowerPoint and slide evidence map
docs/                       Methods, field guide, validation and packaging notes
requirements.txt            Exact versions used
environment.yml             Dedicated conda environment definition
submission.json             Case and execution metadata
SHA256SUMS.txt              File fingerprints for this snapshot
```

## Data source and attribution

The input is public **synthetic example data**, not real player data. Original
assignment: https://github.com/vejadu/InterviewCase-Gaming-PC-App . The pinned
commit, exact input hash and retrieval metadata are included. The upstream MIT
license and attribution are preserved in [source/LICENSE](source/LICENSE).
No unrelated project, personal records, credentials or installed environments
are required by this submission.

See [validation](docs/VALIDATION.md) for exactly what was checked, and
[packaging notes](docs/PACKAGING_NOTES.md) for portability changes made after
the interview. The analysis logic and numerical findings were preserved.
