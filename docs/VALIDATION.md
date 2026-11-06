# Validation and reproduction status

The self-contained submission was copied to a separate extraction-style directory
and executed in a fresh Jupyter kernel using the existing Windows Python 3.12.16
analysis environment. All **45 code cells completed with zero cell errors**.

All **24 saved mandatory/additional result CSVs** matched the
submitted tables (numeric tolerance 1e-9 relative / 1e-10 absolute), and all three
cleaned Parquet tables matched exactly. The unmodified input SHA-256 matched.
The packaged path setup was verified to use this copy's data directory.
Machine-readable details: [reproduction_check.json](reproduction_check.json).

The analytical run includes 29 source-contract checks, 20 preparation checks,
11 independent mandatory-answer checks, independent source-ledger feature/outcome
and conversion-risk-set checks, and independent SciPy fits for the two primary
usage regressions. All 21 final regression/sensitivity fits converged without
warnings. See the included check CSVs, diagnostics and findings for scope.

The three analytical figures and all 12 presentation slide previews were visually
inspected in the original run. The final deck passed package, layout/font and
native chart-data validation. Native PowerPoint execution was not tested.

**Limits:** a fresh dependency installation, another operating system and a new
Python version were not tested. `requirements.txt` records the actual versions
used, rather than promising availability for every future package index or platform.
The portable rerun used the existing registered kernel through `CONTOSO_KERNEL`;
the README explains how a recipient registers their own environment.
