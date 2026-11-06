# InterviewCase_Gaming_PC_App
Example data. Not real data.

# Contoso AI Gaming Companion (PC): Growth Modeling Assignment

## Executive Summary

Contoso AI Gaming Companion is an AI-powered PC gaming app (think an Xbox-style companion for PC players). It uses AI to help players get better performance, get unstuck in games, and automate tedious setup tasks so they spend more time playing. The product team is seeking ways to grow the business and improve the product by leveraging player activity data and AI feature usage patterns.

---

## 1. Product Overview

Contoso AI Gaming Companion offers three core AI features:

- **AI Game Optimizer**: Real-time AI suggestions while you play — recommended graphics settings, FPS/latency tweaks, and per-game performance profiles, similar to autocomplete but for your game settings.
- **AI Game Coach (Chat)**: An in-game overlay where players ask plain-language questions and get answers — strategy tips, quest/boss help, loadout advice, and troubleshooting, similar to ChatGPT for gaming.
- **AI Game Agent**: An overlay where players give a prompt and the AI takes action on their behalf — installing/updating games and mods, fixing driver or crash issues, setting up controllers, or creating clips and highlights from a session.

---

## 2. Data

The complete, synthetic dataset is in `contoso_gaming_pc_app_output.csv` (300 players, 60 starting on each day from March 3 through March 7, 2025). It contains one row per day **with app activity**, from each player's start day through at most day 59. A missing player-day means no observed activity, not necessarily cancellation; there are no rows after a recorded cancellation. Each player has a day-0 row. The last possible observation is May 5, 2025.

Plan and billing status reflect the **end of the recorded day**. A Free-to-Paid change first appears on the upgrade day; `Cancelled` appears on the final recorded Paid day and never on a Free row. Feature counts include successful and failed interactions and respect the per-plan daily limits below. This is generated example data, not evidence of causal effects or actual customer behavior.

To regenerate the CSV deterministically, run `python generate_dataset.py`; to check its consistency, run `python -m unittest test_dataset` (Python standard library only). Column names are kept generic; see the mapping below.

### Data Dictionary

| Column Name                | Definition                                                        |
|----------------------------|-------------------------------------------------------------------|
| `date`                     | Day of player activity                                            |
| `userid`                   | Anonymized player identifier tied to a player profile             |
| `startdate`                | First day the player has activity in the app (cohort date)        |
| `plan`                     | Either “Free” or “Paid” (premium subscription)                    |
| `Status`                   | “Active” or “Cancelled” from the billing system at day end; cancellation only occurs on a Paid row |
| `DayOfWeek`                | Day of the week for the `date` column                             |
| `Weekend`                  | Boolean: whether the day is a weekend                             |
| `DaysSinceStart`           | Days between `date` and `startdate`                               |
| `AI_AutoComplete_Success`  | Successful AI Game Optimizer suggestions applied                  |
| `AI_AutoComplete_Error`    | AI Game Optimizer interactions with errors                        |
| `AI_Chat_Success`          | Successful AI Game Coach (Chat) interactions                      |
| `AI_Chat_Error`            | AI Game Coach (Chat) interactions with errors                     |
| `AI_Agent_Success`         | Successful AI Game Agent actions                                  |
| `AI_Agent_Error`           | AI Game Agent actions with errors                                 |

---

## 3. Feature Usage Limits

AI feature usage limits by plan:

| Plan   | AI Game Optimizer (per day) | AI Game Coach (per day) | AI Game Agent (per day) |
|--------|-----------------------------|-------------------------|-------------------------|
| Free   | 100                         | 10                      | 5                       |
| Paid   | 200                         | 50                      | 20                      |

---

## 4. Modeling Assignment

You are tasked with using daily activity data for player accounts created between **3/3/2025 and 3/7/2025**, covering each player's first 60 days (day 0–59), to inform product strategy. Use the .csv file in this repository. When calculating retention, use the day-0 cohort as the denominator and distinguish “active on day N” from “active at any point during week N.” An absent row is not itself proof of cancellation.

### Analysis Goals
Mandatory questions to answer:
- How many new Free and Paid player accounts were created in the week of 3/3-3/7?
- How many players are still using the app in the following days and weeks? What is our retention rate?
- How many Free players upgraded to Paid? What is our conversion rate?
- How many of our Paid players have cancelled?

Additional questions the product team might be interested in (not in priority order):
- What is the relationship between AI feature usage and retention or conversion to Paid?
- What is the relationship between AI feature errors and retention or conversion to Paid?
- Do we observe distinct differences in behavior between player groups (e.g., weekend vs. weekday players, heavy Optimizer users vs. heavy Coach users)?
- When are players most likely to convert? What does their journey look like?
- Any other insights or recommendations you have.

---

## 5. Deliverables

Prepare the following:

- **Business Presentation (10–15 min)**: With a PowerPoint or slide deck, share the following for a Leadership Team audience:
  - Describe the problem/opportunity
  - Present insights
  - Recommend actions for product, marketing, and/or sales teams

- **Technical Discussion (10–15 min)**: Prepare the following to share with your data science colleagues, and walk through your code files.
  - Detail your analysis approach and evaluation criteria
  - Recommend actions for data science and engineering teams

- **Code Files**
  - Submit all code used to generate your outputs (Python scripts, Jupyter notebooks, queries, etc.) and your final products.

---

## 6. Guidance for Presentations

- **Business Audience**: Focus on actionable insights, business impact, and recommendations.
- **Technical Audience**: Emphasize analysis/modeling decisions, feature engineering, evaluation metrics, and reproducibility.

---
