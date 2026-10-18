# Hillstrom Email Incrementality

A reproducible analysis of a three-arm email experiment, separating overall incremental purchase effects from exploratory regional differences.

[中文说明](README.zh-CN.md) · [Study design and results](docs/STUDY.md) · [Code and project structure](docs/STRUCTURE.md) · [Data and reproduction](docs/REPRODUCIBILITY.md)

## Research question

Does assigning customers to a merchandise email increase their two-week purchase rate compared with no email? Is the estimated effect distinguishable from a **+0.10 percentage-point scenario benchmark**? Urban, suburban and rural breakdowns are exploratory; they do not measure city-specific preferences or establish regional differences.

This portfolio project analyzes the historical, public Hillstrom dataset. It does not claim a newly conducted experiment or deployed business uplift.

## What this project demonstrates

- **Experiment analysis:** define the assignment-based population, outcome, estimand and comparison family before effect estimation.
- **Data quality:** audit allocation ratios, missing values, outcome logic, baseline balance and identical records without silently deleting ambiguous observations.
- **Statistical inference:** estimate absolute effects, invert corrected score tests, control two primary comparisons and distinguish statistical evidence from practical benchmarks.
- **Reproducible engineering:** freeze scientific settings, test numerical inference independently, validate source hashes and reproduce the report offline.

## Main findings

All **64,000 rows** are retained. The outcome is a recorded purchase within the source's two-week follow-up; the denominator includes everyone in the assigned arm, not just email openers or visitors.

| Assigned arm | Purchasers / assigned | Purchase rate |
|---|---:|---:|
| Men's merchandise email | 267 / 21,307 | 1.2531% |
| Women's merchandise email | 189 / 21,387 | 0.8837% |
| No email | 122 / 21,306 | 0.5726% |

| Comparison vs. no email | Absolute effect (pp) | Bonferroni-adjusted interval | Adjusted p-value |
|---|---:|---:|---:|
| Men's merchandise email | +0.6805 | [+0.4771, +0.8922] | 3.0484e-13 |
| Women's merchandise email | +0.3111 | [+0.1277, +0.4992] | 0.0003143 |

**pp = percentage points.** Each interval has 97.5% confidence; Bonferroni controls the two-comparison family at 5%. Both lower bounds exceed the fixed +0.10 pp scenario benchmark, conditional on the source and independence assumptions. The women's-email lower bound is close to the benchmark. This is neither a profit estimate nor a direct test of superiority between campaigns. Campaign names describe merchandise, not customer gender.

All six regional estimates are retained. For example, the rural women's-email estimate is +0.3349 pp with an exploratory nominal 95% interval of **[−0.1599, +0.8464] pp**. It leaves meaningful negative and positive effects plausible; it does not establish zero effect or regional heterogeneity.

Secondary visits and all-assigned-customer mean spend are exploratory. Mean spend differences are +$0.7698 and +$0.4244 per assigned customer; these are revenue-like outcomes, not profit. See [complete results and interpretation](docs/STUDY.md), [machine-readable results](reports/effects_results.json) and the [Chinese HTML report](reports/Hillstrom总体效果与地区探索.html) (download and open locally).

## Analysis workflow

Source and checksum → sample audit → fixed execution settings → overall inference → exploratory breakdowns → independent verification and offline report.

The primary estimator is the absolute purchase-rate difference with Miettinen–Nurminen corrected score inference. Secondary mean-spend intervals use 20,000 within-arm bootstrap draws, fixed seed 20261017, all zeros included and no trimming. No deduplication, imputation, covariate adjustment or outcome-driven method selection is performed.

The [execution record](docs/EXECUTION_SCOPE.md) documents a statistical-library issue found during synthetic validation and the independently checked implementation used instead. [Pre-run hashes](docs/pre_run_freeze.json) preserve the scientific code and settings. Outcome counts had already been seen during audit: this is a fixed retrospective analysis, **not blinded or pristine preregistered research**.

## Run locally

Python **3.12** was tested. No cloud account is needed. From the project directory on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_data.py
.\.venv\Scripts\python.exe scripts/run_offline.py
.\.venv\Scripts\python.exe scripts/verify_reproduction.py --destination ../hillstrom-reproduction-check
```

Use a new destination for each verification. On macOS/Linux, use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`; those platforms have not been tested here. Installation and the explicit data download require network access. Thereafter analysis and HTML reporting run locally, with Python socket/DNS calls disabled during the analysis runner. This is not an operating-system firewall guarantee.

Open `reports/Hillstrom总体效果与地区探索.html` after the run. On a configured Windows environment, `Run_analysis.cmd` is a convenience launcher. Raw data and the row-level identical-record extract are restored by the checksum-checked downloader, not included in the public repository bundle. [Reproduction details and source provenance](docs/REPRODUCIBILITY.md).

## Limits of the evidence

- No customer IDs, allocation/delivery logs or individual timestamps: independent identities, original randomization and complete follow-up cannot be independently verified.
- 7,634 rows belong to 1,072 identical full-row patterns. Similar records do not prove duplicate people; actual repeated customers would make nominal intervals too narrow. All rows remain in the analysis.
- No cost, margin, unsubscribe or long-term outcomes: the +0.10 pp benchmark is a scenario, not a validated profitability threshold.
- Regional intervals are nominal and exploratory. No interaction test or subgroup targeting recommendation is made.
- The downloaded mirror matches recorded hashes; it was not byte-compared with the author's inaccessible original CSV endpoint.

## Reviewable evidence

- [Original audit](history/audit/README.md), [audit tables](history/audit/reports/audit_results.json), and [sample-size scenarios](history/audit/reports/scenario_power.csv).
- [Primary results](reports/primary_conversion.csv), [all regions](reports/exploratory_regions.csv), [visits](reports/exploratory_visit.csv), [mean spend](reports/exploratory_spend.csv), and [bootstrap group means](reports/bootstrap_group_means.csv).
- [Original verification](reports/verification.json), [portable verification](reports/packaging_verification.json), and [history/preservation policy](docs/HISTORY.md).

Data attribution: [Kevin Hillstrom's original challenge](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html), accessed through the documented [scikit-uplift dataset mirror](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_hillstrom.html). No data redistribution license or new license for third-party material is asserted.
