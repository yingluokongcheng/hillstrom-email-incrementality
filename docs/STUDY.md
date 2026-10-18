# Fixed study design and complete interpretation

## Population and estimand

The source describes 64,000 customers assigned to men's merchandise email, women's merchandise email or no email, with a two-week follow-up. Analyze all rows as assigned, including identical rows and zero spend. This is an assignment-based, intention-to-treat-style comparison conditional on the original source's design claims; identities, assignment logs and compliance cannot be independently checked.

Primary outcome: binary recorded conversion. Estimand: treatment purchase rate minus no-email purchase rate. No email is the shared control; no direct men-versus-women comparison is included.

## Fixed inference

Two two-sided primary comparisons form one family. MN-corrected score tests and inverted 97.5% intervals use the restricted binomial MLE under each proposed risk difference and the N/(N−1) variance correction. Report adjusted p = min(2 × raw p, 1). Bonferroni does not require independence of the two shared-control comparisons.

The practical scenario is +0.10 pp (0.001 probability, or 10 additional purchasers per 10,000 assigned). Compare the adjusted interval with this benchmark, not just the point estimate. This benchmark contains no cost or margin information.

The constrained likelihood implementation is checked against an independent corrected polynomial reference. A nonzero-null coefficient issue in installed statsmodels was found on synthetic tests before effect estimation. The [execution record](EXECUTION_SCOPE.md) retains the failed validation history and resolution; the actual-data method and tolerances were not selected for favorable outcomes.

## Overall results

| Arm | N | Purchases | Rate |
|---|---:|---:|---:|
| Men's merchandise | 21,307 | 267 | 1.2531% |
| Women's merchandise | 21,387 | 189 | 0.8837% |
| No email | 21,306 | 122 | 0.5726% |

| Contrast vs no email | Difference (pp) | 97.5% interval (pp) | Adjusted p |
|---|---:|---:|---:|
| Men's merchandise | +0.6805 | [+0.4771, +0.8922] | 3.0484e-13 |
| Women's merchandise | +0.3111 | [+0.1277, +0.4992] | 0.0003143 |

Both are statistically distinguishable from zero after correction and both lower bounds exceed +0.10 pp under the stated assumptions. The latter means the compatible effect range clears the scenario benchmark; it is not a profitability finding. Roughly 68.1 and 31.1 extra purchasers per 10,000 assigned are estimated, respectively. No direct campaign superiority was tested.

## All regional results: exploratory only

The data's raw `Surburban` label is mapped to `Suburban` only in derived presentation. These are urbanicity groups, not cities or cultural-preference variables. Each interval is nominal 95%, without adjustment across six comparisons. There are no regional p-values, interaction tests, simultaneous-coverage claims or subgroup winner selection.

| Region | Campaign | Difference (pp) | Nominal 95% interval (pp) |
|---|---|---:|---:|
| Urban | Men's | +0.6643 | [+0.3871, +0.9570] |
| Urban | Women's | +0.3614 | [+0.1056, +0.6274] |
| Suburban | Men's | +0.7433 | [+0.4856, +1.0175] |
| Suburban | Women's | +0.2578 | [+0.0353, +0.4878] |
| Rural | Men's | +0.5285 | [+0.0178, +1.0615] |
| Rural | Women's | +0.3349 | [−0.1599, +0.8464] |

Rural women's-email uncertainty spans negative, zero and positive effects. A result significant in one subgroup and uncertain in another is not evidence that the effects differ. Regional estimates are retained to illustrate precision limits, not justify targeting.

## Secondary outcomes: exploratory only

| Outcome | Men's vs no email | Women's vs no email |
|---|---|---|
| Visit-rate difference (pp) | +7.659; 95% CI [6.996, 8.323] | +4.523; 95% CI [3.890, 5.158] |
| Mean spend difference per assigned customer (USD) | +0.7698; 95% CI [0.4875, 1.0598] | +0.4244; 95% CI [0.1701, 0.6824] |

Mean-spend estimation includes every assigned row, zeros and large values. The fixed 20,000-draw within-arm bootstrap uses seed 20261017 and percentile intervals with linear quantiles, sharing control draws across the contrasts. Multinomial sampling of distinct values is equivalent to the empirical row bootstrap. These secondary intervals are not multiplicity-adjusted and do not establish profit.

## Audit and limitations

No missing or predefined invalid fields were detected. Allocation-ratio p=0.9037 and maximum baseline absolute SMD≈0.0169 did not flag imbalance; they do not prove randomization. 7,634 rows belong to 1,072 identical patterns, all retained because no ID establishes duplicate people. If they actually repeat customers, independence-based uncertainty is understated.

The original audit's hypothetical 1% baseline scenario had only about 11% power for +0.10 pp, with approximately +0.32 pp 80%-power MDE overall. This describes limited sensitivity to small effects, not a reason to reject larger observed effects. Do not substitute observed-effect post-hoc power.

Missing allocation/delivery logs, customer IDs and follow-up timestamps limit causal verification. Missing cost, margin, unsubscribe and long-term outcomes prevent profit and retention conclusions. The mirror was checksum-verified but not compared with the author's inaccessible original endpoint. Outcomes were visible during audit, so the project is retrospective and not blinded. No further experiments or favorable-region selection were added.

Full precision and denominators: [results JSON](../reports/effects_results.json). Original audit: [audit JSON](../history/audit/reports/audit_results.json).
