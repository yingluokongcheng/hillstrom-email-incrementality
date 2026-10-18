# Project structure and code guide

```text
hillstrom-email-incrementality/
├── README.md                     # English homepage
├── README.zh-CN.md               # Chinese explanation
├── requirements.txt             # Frozen Python dependencies
├── Run_analysis.cmd             # Windows convenience launcher
├── config/                      # Original plan + execution settings
├── data/raw/source_manifest.json # Source URL and expected hashes
├── docs/                        # Design, provenance, freeze, history
├── scripts/                     # Download, analysis, report, verification
├── tests/test_inference.py       # Eight numerical/statistical tests
├── reports/                     # All results, HTML, screenshots, checks
└── history/
    ├── audit/                   # Original audit snapshot
    └── effects-v1/              # Replaced original presentation/utility files
```

| File | Responsibility |
|---|---|
| `scripts/download_data.py` | Fetch or reuse the exact hash-verified source; restore both analysis and audit caches and the row-level audit extract. |
| `scripts/analyze.py` | Validate frozen settings; estimate primary effects, all six regional effects, visits and bootstrap mean-spend uncertainty. |
| `scripts/build_report.py` | Render the static Chinese HTML report from result tables. |
| `scripts/run_offline.py` | Run analysis and reporting with Python socket/DNS calls disabled. |
| `scripts/verify_reproduction.py` | Run tests, reproduce in a new folder, compare seven outputs, check ten intervals against independent equations and verify the audit snapshot. |
| `tests/test_inference.py` | Synthetic checks, sparse-cell behavior, null symmetry and an independent corrected polynomial reference. |

Start with [study and results](STUDY.md), then read the scientific execution record in [EXECUTION_SCOPE.md](EXECUTION_SCOPE.md). Historical audit scripts retain their original context; use the current root reproduction entry points for a standalone checkout.
