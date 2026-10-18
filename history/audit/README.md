# Hillstrom Email Experiment — Local Audit

**Status: audit complete; treatment-effect analysis awaits user review.**

This project audits the Hillstrom three-arm email experiment and evaluates sample support under fixed hypothetical effect scenarios. It does not yet estimate campaign effects or declare a winning campaign.

- 64,000 rows; allocation approximately 1:1:1; global sample-ratio mismatch p=0.903693.
- No missing cells or flagged domain/outcome consistency violations. Pretreatment maximum absolute standardized difference: 0.0169.
- 7,634 rows belong to 1,072 identical full-row patterns. All are retained. Without customer IDs these are not proven duplicate people, and independence cannot be verified.
- At a hypothetical 1% control rate, the current overall sample has approximately 11% power for a +0.10 percentage-point effect. The 80%-power MDE is approximately +0.32 percentage points; regional precision is lower.
- No effect differences, effect significance tests or observed-effect post-hoc power are computed. Group purchase counts are exposed for sparse-cell auditing; subsequent work is not blinded.

[中文说明](README.zh-CN.md) · [Audit report](reports/Hillstrom数据审计.html) · [Frozen plan](docs/PLAN_v1.md) · [Methods](docs/AUDIT_METHODS.md) · [Verification](reports/verification.json)

## Reproduce locally

Python 3.12 on Windows was tested in a fresh virtual environment with pinned dependencies. No Google Cloud or account is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_data.py
.\.venv\Scripts\python.exe scripts/run_offline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Installation and initial download need ordinary internet access. The download command validates an existing cache instead of fetching again. With the environment and data present, double-click `Run_audit.cmd`; the audit runner disables Python connection/DNS calls and builds CSV, JSON and HTML reports without network access. This is not an operating-system firewall guarantee. The HTML itself has no remote asset dependencies and can be opened directly in a browser.

The existing environment on this machine is already installed. Open `reports/Hillstrom数据审计.html` to read without rerunning. Do not copy `.venv` between machines; recreate it.

## Layout

```text
config/plan.json                 Fixed statistical choices and scenario grid
docs/PLAN_v1.md                  User-approved scope, frozen before downloading
docs/AUDIT_METHODS.md            Operational definitions and power formula
data/raw/                       Unmodified source, compressed copy and provenance
scripts/download_data.py        Explicit download/cache step
scripts/audit.py                Quality, allocation, balance and scenario planning
scripts/build_report.py         Deterministic Chinese HTML report
scripts/run_offline.py           Audit/report with Python networking disabled
scripts/verify_reproduction.py  Independent-directory rebuild and test evidence
tests/test_audit.py              Semantic, census and planning validation
reports/                        All audit tables, narrative and verification
```

## Data provenance and limits

The original [MineThatData description](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) describes randomized groups and two-week outcomes. Its CSV endpoint failed certificate validation in this environment. We used the [scikit-uplift documented copy](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_hillstrom.html), verified its published compressed MD5, and recorded SHA-256 hashes. We did **not** establish byte equality with the author's original file. See `data/raw/source_manifest.json`.

The raw regional spelling `Surburban` is mapped to `Suburban` only in a derived reporting field. No data rows are deleted or imputed. Source customer IDs, assignment/delivery logs and timestamps are absent, so original roster completeness, unique identities, compliance and individual observation windows cannot be independently checked. Sample planning assumes independent customers and can overstate precision if rows repeat actual people. Urbanicity is not a city or cultural-preference measure.

This is a retrospective analysis of publicly available experimental data, not a newly conducted experiment or pristine preregistration. The +0.10 percentage-point benchmark is a scenario, not a demonstrated profitability threshold. Public data availability is not a verified redistribution license; raw data remain local and are ignored by Git. Nothing has been published.
