# Methods and definitions

## Population, observation and cleaning

300 players started March 3–7, 2025, with 60 players per date. The source has
7,970 observed active player-days over tenure days 0–59. A missing row is no
observed activity, not proof of cancellation. Coverage completeness relies on
the source's complete synthetic-data declaration, not players' last activity.
The final possible observation is May 5, 2025.

All original source rows and values are retained. No correction, exclusion or
imputation was required. Added fields include explicit-format dates, verified
tenure/week labels, activity/cancellation flags, and successes-plus-errors
attempt totals. A stable 1-based CSV data-record ID provides source lineage.

One player summary anchors each player on day 0. A separate 18,000-row retention
calendar expands all players to 60 days. Its 10,030 added no-activity rows retain
missing plan, billing status and feature counts. They do not change source data.
The generated audit has rule summaries, cell additions and source-to-player lineage.

## Mandatory questions

- Starting plan is the observed end-of-day plan on day 0. Same-day signup/upgrade
  ordering is unobservable.
- Daily retention counts activity on an exact tenure day. Weekly retention counts
  each player at most once within a tenure week. Both divide by the original
  day-0 cohort. Week 1 is days 0–6 and includes signup; days 56–59 are a partial week.
- Conversion is a first Paid observation among initially Free players within the
  file. Initially Paid players are not in the conversion denominator.
- Cancellation requires explicit Cancelled billing status on a Paid row.
  Initially Paid players and converters are included. Cancellation counts are
  not standardized monthly churn rates because Paid exposure differs.

## Additional goals and regressions

Definitions were agreed before fitting: first-week predictors use days 0–6;
retention means any activity days 28–34 (180/300); conversion means an upgrade
days 7–59 among initially Free players not converted by day 6 (33/232). No
first-week conversions occur in this file. One player is one independent unit.

Usage is successes plus errors, transformed as log2(1 + attempts). Error rate
is errors / attempts; it remains undefined for zero attempts. Feature-specific
error-model sample exclusions are explicitly saved.

Separate binomial logistic regressions estimate retention and conversion:

```text
retained ~ log2_optimizer + log2_coach + log2_agent + active_days + initial_paid
later_conversion ~ log2_optimizer + log2_coach + log2_agent + active_days
```

Feature-specific error models include that feature's error rate per 10 percentage
points, its log attempt volume, active days, and initial plan for retention.
They do not jointly control all feature error rates. HC1 standard errors are used.
Reported odds ratios are conditional odds changes, not percentage-point effects.
Confidence intervals are pointwise 95% model-based intervals.

Spearman correlations use 4,999 outcome-label permutations, seed 20261105.
Benjamini–Hochberg adjustment is separate across 18 correlation tests, 12 primary
feature slopes, and the exploratory subgroup coefficients. Raw correlations do
not control general engagement or plan. The clearest primary signals have q=.033:
Coach retention OR 1.51, Agent retention OR 1.52, Optimizer conversion OR 1.84.
All six adjusted error-rate intervals include 1.

## Segments and journeys

Weekend preference compares first-week active weekend days / 2 with active
weekdays / 5. Feature preference compares usage relative to daily plan limits,
not raw counts across unequal feature caps. Exact ties are a separate category.
Group tables report event counts, denominators and Wilson intervals. Segment
regressions adjust active days and initial plan where applicable.

A 3-player balanced feature-preference category caused non-finite standard errors
in an initial subgroup fit. The recorded revision restricts adjusted group models
to categories with at least 10 players. All groups remain in descriptive tables.
This excludes 3 retention and 2 conversion players from those particular fits,
not from the main analyses. Group models do not support confident feature ranking.

Daily conversion hazard divides conversions by initially Free players not yet
converted, retaining inactive players in the risk set. Its regression uses
11,162 at-risk player-days, fixed first-week predictors and log tenure, with
player-clustered standard errors. A centered quadratic log-tenure sensitivity
and simpler usage specifications are included. Repeated days do not create more
than 33 events. The largest observed full-week window is days 7–13: 11/232.

Preconversion journeys describe eventual converters only and exclude upgrade-day
usage because plan is measured at day end. Feature means are per observed active
day; absence of activity remains distinct. Conditioning on eventual conversion
prevents treating those journeys as evidence of an intervention effect.

## Interpretation limits

These exploratory synthetic associations do not identify causal effects or
validate a forecasting model. Only 33 conversions limit precision. Unmeasured
intent, plan, exposure and cohort patterns can confound associations; measured
adjustment does not remove all confounding. Collinearity limits attribution to
one feature. No held-out predictive performance or real-customer lift is claimed.
Recommended follow-up is real-cohort replication and a powered randomized test.
