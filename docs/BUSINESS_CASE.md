# Do merchandise emails increase purchases?

HILLSTROM EMAIL EXPERIMENT · EXPERIMENTATION & INFERENCE

Experimental design principles · Confidence intervals · Multiplicity · Python

[Project overview](../README.md) · [Printable one-page HTML](business-case.html) (download and open locally)

## Problem

Do merchandise emails increase two-week purchase rates versus no email, and does the uncertainty range clear a **+0.10 percentage-point scenario benchmark**? This retrospective analysis of a public three-arm experiment separates overall evidence from exploratory regional differences.

## Method

Retained all **64,000 assigned rows**, including identical records. Audited allocation ratios, missingness, outcome logic and baseline balance. Defined purchase rate over everyone assigned to each arm, rather than conditioning on visits or responses. Fixed the two email-versus-control comparisons and analysis settings before effect estimation; outcome counts had already been visible during audit.

Estimated absolute rate differences using corrected score inference. Applied Bonferroni correction across the two primary comparisons, giving each interval 97.5% confidence. Regional and secondary outcomes remained exploratory. Eight tests and ten independent interval checks passed; offline reproduction matched all seven generated outputs byte for byte.

## Results

Purchase rates were **1.2531%** for men's-merchandise email, **0.8837%** for women's-merchandise email and **0.5726%** for no email. Campaign names identify merchandise, not customer gender.

| Email vs. no email | Effect (pp) | Adjusted interval (pp) | Adjusted p |
| --- | --- | --- | --- |
| Men's merchandise | +0.6805 | [+0.4771, +0.8922] | 3.05 × 10<sup>−13</sup> |
| Women's merchandise | +0.3111 | [+0.1277, +0.4992] | 0.0003143 |

pp = percentage points. Each interval is 97.5%; the two-comparison family error rate is controlled at 5%.

Both adjusted intervals exclude zero and exceed +0.10 pp at their lower bounds, conditional on the data assumptions. The women's-email lower bound is close to the benchmark. The rural women's-email exploratory 95% interval spans **−0.1599 to +0.8464 pp**; it establishes neither no effect nor regional heterogeneity.

## Recommendations

*Proposed; not a rollout decision*

**Use the overall evidence to motivate a new, cost-aware validation experiment.** Define the assignment unit, minimum worthwhile effect, sample size and stopping rule before launch; measure contribution margin and unsubscribe outcomes alongside purchases. Treat +0.10 pp as a scenario until costs and margins justify a decision threshold. Preserve a no-email control and avoid regional targeting from these exploratory results. A campaign-choice decision would require a planned direct comparison.

## Limits

No customer IDs or assignment/delivery logs independently verify the source's randomization and independence claims. Identical rows do not prove duplicate people, but unrecognized repeat customers could make intervals too narrow. This was not blinded research. Costs, margins and long-term outcomes are absent; the results do not establish profitability, campaign superiority or deployed business uplift.

Published business case · 18 Oct 2026. Analysis and historical results remain in the project repository.
