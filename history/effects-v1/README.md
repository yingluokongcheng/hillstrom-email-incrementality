# Hillstrom Email Incrementality — Fixed Analysis v1

Local retrospective analysis of the public three-arm Hillstrom email experiment. **No GitHub publication.** All 64,000 rows are retained, including 7,634 rows belonging to identical record patterns.

[中文说明](README.zh-CN.md) · [Results report](reports/Hillstrom总体效果与地区探索.html) · [Full results](reports/effects_results.json) · [Original audit](history/audit/reports/Hillstrom数据审计.html)

## Primary results

Two-week purchase-rate differences versus no email, using MN-corrected score inference. Bonferroni controls the two-comparison family at alpha=0.05; each interval is 97.5%.

| Campaign | Difference (percentage points) | Adjusted interval | Adjusted p |
|---|---:|---:|---:|
| Men's merchandise email | +0.6805 | [+0.4771, +0.8922] | 3.0484e-13 |
| Women's merchandise email | +0.3111 | [+0.1277, +0.4992] | 0.0003143 |

Both lower bounds exceed the pre-agreed +0.10 percentage-point scenario benchmark, conditional on the data and independence assumptions. This is not a profitability result. The women's-email lower bound is close to the benchmark. No direct campaign superiority test was performed.

All six urbanicity comparisons are retained as exploratory nominal 95% intervals, without regional p-values, simultaneous-coverage claims, interaction tests or winner selection. The rural women's-email interval spans negative and positive effects: approximately [-0.160, +0.846] percentage points. This does not establish no effect or differences between regions. Secondary visit and all-customer mean-spend results are also exploratory.

## Reproduce

Python 3.12 was tested in a dedicated virtual environment. From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/run_offline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

This local deliverable includes the audited data cache and source metadata. Do not publish raw data without establishing redistribution permission. For source download logic see `history/audit/scripts/download_data.py`; it is intentionally separate from the offline runner. Downloading to the archived audit path does not update the analysis data automatically: any replacement must match `data/raw/source_manifest.json` exactly.

The installed environment is ready on this machine: double-click `Run_analysis.cmd`. It does not install, fetch, publish or run additional models. Python socket connection/DNS calls are blocked during the analysis; this is not an OS-level firewall test. Initial installation needs network access; analysis and the static report work locally thereafter.

## Methods and provenance

- `docs/APPROVED_PLAN_v1.md`: original fixed plan; the historical audit-only gate was explicitly cleared by the user.
- `docs/EXECUTION_SCOPE.md`: authorization, frozen implementation details and pre-analysis validation history.
- `docs/pre_run_freeze.json`: hashes saved before real effect computation.
- `config/execution.json`: outcome, comparisons, alpha, benchmark, bootstrap seed/count.
- `scripts/analyze.py`: constrained-likelihood MN score statistic and inversion; within-group empirical bootstrap.
- `scripts/build_report.py`: complete Chinese report.
- `reports/`: all primary/exploratory results and bootstrap group means, plus validation.
- `history/audit/`: unchanged copy of all 38 original audit files; the original sibling audit project is also preserved.

The primary method uses the restricted binomial maximum likelihood estimate under each null difference and the N/(N-1) variance correction. Brent root finding inverts the score statistic at the normal critical values. Synthetic validation revealed the known nonzero-null coefficient bug in installed statsmodels 0.14.4 and 0.15.0; neither package is used for nonzero-null interval construction. The direct score-equation solver is checked against an independently corrected polynomial formulation, and zero-null tests are checked against statsmodels. The method and test tolerances were not changed to improve results. See [upstream issue #10269](https://github.com/statsmodels/statsmodels/issues/10269).

Mean spend includes all zeros and uses 20,000 within-group bootstrap draws, seed 20261017, percentile intervals and a shared control draw sequence. Resampling multinomial counts over distinct spend values is equivalent to the ordinary row bootstrap. No trimming, imputation, deduplication or covariate adjustment was performed.

## Limitations

The original CSV endpoint was inaccessible with valid TLS verification; the documented scikit-uplift mirror checksum was verified instead. No customer IDs, allocation/delivery logs or individual timestamps are available. Identical rows cannot establish duplicate people, but independent identities also cannot be verified; actual duplicate customers would overstate precision. Original randomization, roster completeness and compliance remain source-based assumptions. Urbanicity is not a city or cultural-preference measure. No costs, margins, unsubscribe or long-term outcomes are available. Public outcome counts had already been viewed during audit, so this is not blinded or pristine preregistered research. All findings concern this historical dataset under its assumptions, not demonstrated live business uplift.
