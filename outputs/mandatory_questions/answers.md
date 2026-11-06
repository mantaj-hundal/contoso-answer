# Mandatory-question answers

    Synthetic Contoso cohort starting March 3–7, 2025; tenure days 0–59.

    1. **New accounts:** 232 initially Free and 68 initially Paid, 300 total. Initial plan is the observed day-0 end-of-day state.
    2. **Retention:** day 59 has 87/300 active players (29.0%). Last full tenure week (days 49–55) has 137/300 active at least once (45.7%). Partial week 9 (days 56–59) has 123/300 (41.0%). Full daily and weekly tables are in `tables/q2_daily_retention.csv` and `tables/q2_weekly_retention.csv`; all use the original day-0 denominator. Week 1 includes signup and is 100% by construction.
    3. **Free-to-Paid:** 33/232 initially Free players converted (14.2%). Same-day signup and upgrade ordering is not observable.
    4. **Paid cancellations:** 16 distinct players have explicit cancellation records; 101 players were ever observed Paid, including converters. Counts do not standardize unequal Paid exposure.

    All 11 independent answer checks passed against the original CSV.
    Missing activity is not cancellation. Full coverage relies on the source's
    complete synthetic-data declaration. These descriptive results do not establish
    causal product effects. No feature-usage analysis, charts or presentation created.

    Reproduce by restarting the project kernel and running `analysis.ipynb`, or run
    `python src/create_notebook.py` in the activated project
    environment. Full notebook code is exported to `analysis.py`; `prepare_data.py`
    remains the preparation-only export. Environment and input hash are recorded in
    `../cleaning/checks/preparation_manifest.json`.
    