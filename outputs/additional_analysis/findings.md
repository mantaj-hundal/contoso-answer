# Additional-analysis findings

## Scope

Predictors: days0–6. Retention: any activity days28–34. Conversion: days7–59 among initially Free players still Free after day6.
Retention: 180/300. Conversion: 33/232. No first-week conversions were observed.

## Unadjusted correlations

- retention: coach attempts, Spearman rho=0.312, permutation BH q=0.001, n=300.
- retention: agent attempts, Spearman rho=0.307, permutation BH q=0.001, n=300.
- retention: optimizer attempts, Spearman rho=0.258, permutation BH q=0.001, n=300.
- conversion: agent attempts, Spearman rho=0.214, permutation BH q=0.004, n=232.
- conversion: optimizer attempts, Spearman rho=0.187, permutation BH q=0.008, n=232.
- conversion: optimizer errors, Spearman rho=0.182, permutation BH q=0.014, n=232.

## Adjusted feature associations

- retention_usage, log2_optimizer: OR 1.29 (95% interval 0.95–1.76), BH q=0.217.
- retention_usage, log2_coach: OR 1.51 (95% interval 1.11–2.06), BH q=0.033.
- retention_usage, log2_agent: OR 1.52 (95% interval 1.15–2.01), BH q=0.033.
- conversion_usage, log2_optimizer: OR 1.84 (95% interval 1.19–2.86), BH q=0.033.
- conversion_usage, log2_coach: OR 1.67 (95% interval 1.03–2.73), BH q=0.092.
- conversion_usage, log2_agent: OR 2.09 (95% interval 1.13–3.88), BH q=0.058.
- retention_optimizer_errors, optimizer_error_10pp: OR 1.00 (95% interval 0.59–1.71), BH q=0.989.
- retention_coach_errors, coach_error_10pp: OR 0.91 (95% interval 0.62–1.32), BH q=0.729.
- retention_agent_errors, agent_error_10pp: OR 1.08 (95% interval 0.82–1.42), BH q=0.729.
- conversion_optimizer_errors, optimizer_error_10pp: OR 1.23 (95% interval 0.58–2.65), BH q=0.729.
- conversion_coach_errors, coach_error_10pp: OR 1.24 (95% interval 0.81–1.92), BH q=0.558.
- conversion_agent_errors, agent_error_10pp: OR 0.95 (95% interval 0.54–1.68), BH q=0.935.

3 of 12 primary feature slopes have BH q<0.05. Intervals are pointwise, not multiplicity-adjusted. Absence of a clear association is not proof of no relationship.
Usage ORs are per doubling of 1+attempts. Error-rate ORs are per 10 percentage points and use feature-specific volume adjustment.
Coach and Agent use have the clearest adjusted retention associations; Optimizer use has the clearest adjusted conversion association. All six adjusted error-rate intervals include 1. Raw positive error-count correlations can reflect usage volume, not a beneficial effect of errors.
Simpler usage fits and initially-Free-only retention estimates are saved in tables/usage_sensitivity.csv. Collinearity among usage and engagement limits attribution to one feature; the model changes should be read as sensitivity, not independent replications.

## Segments

- weekend_preference=Balanced, retention: 28/41 (68.3%; Wilson interval 53.0–80.4%).
- weekend_preference=Weekday, retention: 53/109 (48.6%; Wilson interval 39.4–57.9%).
- weekend_preference=Weekend, retention: 99/150 (66.0%; Wilson interval 58.1–73.1%).
- weekend_preference=Balanced, conversion: 6/32 (18.8%; Wilson interval 8.9–35.3%).
- weekend_preference=Weekday, conversion: 5/88 (5.7%; Wilson interval 2.5–12.6%).
- weekend_preference=Weekend, conversion: 22/112 (19.6%; Wilson interval 13.3–28.0%).
- feature_preference=Balanced, retention: 3/3 (100.0%; Wilson interval 43.9–100.0%).
- feature_preference=agent, retention: 59/105 (56.2%; Wilson interval 46.6–65.3%).
- feature_preference=coach, retention: 88/146 (60.3%; Wilson interval 52.2–67.8%).
- feature_preference=optimizer, retention: 30/46 (65.2%; Wilson interval 50.8–77.3%).
- feature_preference=Balanced, conversion: 1/2 (50.0%; Wilson interval 9.5–90.5%).
- feature_preference=agent, conversion: 14/89 (15.7%; Wilson interval 9.6–24.7%).
- feature_preference=coach, conversion: 16/122 (13.1%; Wilson interval 8.2–20.2%).
- feature_preference=optimizer, conversion: 2/19 (10.5%; Wilson interval 2.9–31.4%).

Weekend preference is associated with higher unadjusted retention and conversion than weekday preference. Adjusted direct comparisons and exploratory BH q-values are in tables/segment_regressions.csv. Feature preference groups have overlapping intervals and do not support confident ranking.
Diagnostic revision: a 3-player balanced feature group caused non-finite standard errors in the original subgroup model. Categories with fewer than 10 players are therefore descriptive only, excluding 3 retention players and 2 conversion players from adjusted feature-preference models; other analyses retain them. See checks/segment_regression_scope.csv. No source data was changed.

## Conversion timing and journeys

The largest observed grouped conditional conversion proportion is days 7–13: 11/232 (4.7%). Unequal edge-window lengths and sparse counts limit peak comparisons.
Among the 33 converters, median upgrade tenure is 24 days (range 7–43). This excludes nonconverters by definition.
The pre-upgrade journey conditions on eventual conversion and excludes the upgrade day. Activity gaps and per-active-day feature means must be interpreted together.

## Limits and next decisions

Synthetic observational data supports association, not causal effects or real-customer forecasts. Starting plan, usage caps, general engagement, cohort timing and unmeasured intent can confound relationships. Models adjust selected measured variables only.
Only 33 conversion events support limited precision. Review all diagnostics, collinearity, simpler-model and baseline-timing sensitivities. Correlation and subgroup exploration involve multiple comparisons.
Use feature and segment signals to specify a prospective randomized onboarding or reliability experiment, not to claim that increasing feature use causes retention. Confirm results on real cohorts, protect player-level evaluation splits for prediction, and improve event-time/billing telemetry before operational targeting.

## Reproduction and checks

Run the complete notebook in the project kernel or create_notebook.py in the activated environment. All source-level feature/outcome/hazard checks and independent main-model coefficient checks passed. Source input hash is unchanged. See checks/ and tables/ for full evidence.