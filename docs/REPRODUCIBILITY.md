# Data provenance and reproduction

Use the commands in the [README](../README.md#run-locally). The first install and explicit data download require internet access. With the pinned environment and verified data cache present, the analysis runner and static reports work offline. Only Windows with Python 3.12 has been exercised here; an isolated directory rerun uses the existing pinned runtime, not an independently installed machine.

## Source

- Author: [Kevin Hillstrom's 2008 challenge](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html).
- Documented mirror: [scikit-uplift fetch_hillstrom](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_hillstrom.html).
- Frozen download URL and metadata: [source_manifest.json](../data/raw/source_manifest.json).
- Gzip SHA-256: `bab6578f60db5d792f1c2372c502f029152a5249cf5ea84390f3b7f885d7234f`.
- Decoded CSV SHA-256: `00a6a868e05a9ffe7382da51629f6d6dce88c5acfc945e79d314ebc78fd3a2c0`.

The original author endpoint failed TLS validation. No TLS checks were bypassed. The mirror matches the recorded hashes and documented compressed MD5, but equality to the author's original bytes was not established. Data redistribution permission was not established, so raw rows and the row-level duplicate extract are excluded from the public repository bundle. Source attribution is not a license grant.

`scripts/download_data.py` restores these five generated files, checks exact content, and refuses changed caches:

```text
data/raw/hillstrom.csv
data/raw/hillstrom.source.csv.gz
history/audit/data/raw/hillstrom.csv
history/audit/data/raw/hillstrom.source.csv.gz
history/audit/reports/identical_rows.csv
```

The last file is regenerated from source and checked against the original audit hash. Historical source metadata is left unchanged. Archived audit links to that extract become available after this step. All aggregate results and all reported regions are included without downloading data. No secret or cloud account is needed.

## Verification

Run `scripts/verify_reproduction.py --destination <new-folder>` after data restoration. It checks eight tests, independently validates ten score intervals, performs a separate CSV census, checks all 38 archived audit files against hashes, reruns analysis with Python socket/DNS disabled and compares all seven generated outputs byte for byte. It writes `reports/packaging_verification.json` and `reports/packaging_test_results.txt`; original verification records remain unchanged.

The seven deterministic files are primary, regional, visit and spend CSVs; bootstrap group means; results JSON; and Chinese effect HTML. Verification timestamps and run paths are evidence metadata and are not deterministic analysis output. The archived audit scripts preserve historical local assumptions; use the root verifier for portability.

The [pre-run freeze](pre_run_freeze.json) checks the original scientific code, plan, dependency requirements and tests. A mismatch stops analysis. Do not rewrite hashes merely to bypass this guard.

If data download fails, retry the explicit download once connectivity is restored; do not substitute another dataset or disable TLS. If a checksum or statistical check fails, retain the failure and inspect it before interpreting results. Run normal Python without `-O`, since audit assertions enforce these checks.
