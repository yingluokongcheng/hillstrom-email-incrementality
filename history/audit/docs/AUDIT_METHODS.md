# Audit implementation notes

These operational details implement the approved plan; they do not change the outcomes or hypothesis family.

- Source download failed TLS verification at the author's CSV URL. We did not disable certificate validation. The documented scikit-uplift mirror was downloaded and its compressed MD5 matched `a68a81291f53a14f4e29002629803ba3`. SHA-256 is recorded separately. This verifies the mirror artifact, not equality with inaccessible author bytes.
- The file spells the region `Surburban`. A derived display field maps only this spelling to `Suburban`; the raw CSV remains unchanged. No rows are removed.
- Completely identical rows are listed with file line numbers. These numbers identify file positions, not customers. Without customer identifiers, identical values do not establish duplicate people.
- Balance uses all three pairwise combinations of assignment groups, restricted to pretreatment variables. SMD is the mean difference divided by the square root of the average sample variance; category levels are indicators. |SMD| > 0.1 is a descriptive warning, not a randomization test or deletion rule.
- History band checks use inclusive displayed endpoints because rounding/boundary conventions were not supplied. Other checks cover numeric/finite/binary values, recency 1–12, missingness, negative amounts and logical outcome inconsistencies.
- Regional counts are not separately subjected to multiple SRM hypothesis tests. The global SRM and region baseline SMD cover allocation diagnostics. Regional counts and sparse cells are reported in full.
- Planning power uses p1=p0+delta, pooled expected probability q=(n1*p1+n0*p0)/(n1+n0); V0=q(1-q)(1/n1+1/n0)*N/(N-1); V1=p1(1-p1)/n1+p0(1-p0)/n0. With c=z(1-alpha/2)*sqrt(V0), power is P[N(delta,V1)>c]+P[N(delta,V1)<-c]. Root solving yields MDE and equal-arm sample requirements. Values are normal approximations; not exact finite-sample score power.
- Scenario baseline rates and effects are fixed in config/plan.json. Actual purchase rates/differences are never supplied to this calculation. Regional planning uses alpha=0.025 for a common conservative reference; regional analyses remain exploratory, not six confirmatory tests. Per-comparison power is not the probability both comparisons succeed.
- Published methods reference: https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.power_proportions_2indep.html (pooled null/nonpooled alternative planning). Our finite-n factor is explicit above.
- No observed effect difference, effect p-value, effect confidence interval, winner ranking, bootstrap effect estimate or model is computed in this audit.
