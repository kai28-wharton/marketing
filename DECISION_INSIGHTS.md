# Decision Insights · method and interpretation

> Historical export-1 analysis. Current dashboard: Round 3 planning using export-2 actuals and submitted decision 2. See `ROUND2_REVIEW.md` and `MODEL_CARD.md`. Earlier recommendations, budgets and “missing current CLV” statements below are not current-period claims.

New page between Financial health and Decision studio. It has three addressable
subtabs, keyboard-accessible tab controls, responsive charts and source-linked
disclosures. It does not alter any decision, model coefficient or optimizer input.

## 1. Diagnose the Brand loss

### Holistic review (current main view)

The page now leads with an integrated review from **all 33 supplied CSV/Markdown/PDF
files under materials**, both industry-decision exports and the current workbook.
`brand_holistic.py` covers every one of the sixteen inputs with its definition,
Brand mechanism, observed evidence, financial consequence and counterevidence.
It does not assert historical input changes using the old screenshot reference.
The complete generated analysis is **`BRAND_IMPACT.md`**. The new page-cited PDF
reconciliation is **`SIMULATION_REVIEW.md`**: the goal is simulated equity market
value through targeted customers, two differentiating quadrants and parity in
the others—not Brand alone. Analytics is a multiplier; vendor benefits persist;
Private Brand is mix; holding expense is zero; new-store cost is $1.75M.

The working hypothesis is a **wider but shallower proposition**, not a generic
collapse in experience, quality, sales or CLV. Sales grew 29.3%, higher-cost sales
66.1%, company CLV approximately 25%, and all six segments grew. All six actual
competitors improved Brand (+0.433 mean). FAIR VALUE is a benchmark, excluded
from competitor rankings and averages. This is not a causal control group.

Finance independently supports effective markups 54%/66% → 50%/52%, unlike most
prior decision inputs. Cost metrics and cost-plus arithmetic imply conditional
selling-price proxies $179.75 → $191.64 (lower-cost) and $387.51 → $375.39
(higher-cost). These are not observed transaction prices. Margin compressed;
within-offering changes hurt, while increased higher-cost mix helped.

Vendor/analytics expenses fell but their reported scores stayed at 100%; service
expense rose more slowly than revenue. These qualify possible execution/targeting
amplifiers rather than establish them as causes. Experience improved. Inventory
days improved even though absolute stock and funding needs increased; Brand
repairs must respect cash, contribution and financing capacity.

The source audit checks **376 overlapping historical cells and 96 auxiliary Kahn
cells**, with no conflicts between those repeated exports. The CSV FAIR VALUE
series now governs all working gaps and gates. The conflicting PDF 75%-leader
formula remains source-audit context only; no version/normalization explanation
or exact 67% replacement formula is invented. Repeated histories are not new
observations. Missing current segment CLV, churn, transaction prices and
segment × offering × channel data remain missing. The old-model Shapley table is
now a collapsed error audit, not the main sixteen-factor explanation.

### Observed-score reconstruction and legacy audit

The main diagnosis now links directly to the latest uploaded workbook, **B4 = 25
lower-cost depth** and **B8 = 10 higher-cost depth**. It supersedes the earlier
read of lower-cost depth 50. Cell provenance and the file hash identify the current
editable snapshot, not an immutable simulation execution log.

Across all seven available retailers in both rounds, the empirical reconstruction
`Brand ≈ .5*(lower depth position + higher depth position + lower private-brand
position + higher private-brand position)` matches reported Brand within 0.05.
These are product-position values, not Excel decision indices. This is discovery
and checking on the same 14 rows; it is not held-out validation or an official rule.

Getchell’s contributions are lower depth **−1.00**, higher depth **−1.90**, and
private-brand-position improvements **+0.15 each**. Net **−2.60** exactly matches
the observed change; the level residual remains −0.05 in both rounds. Higher-cost
depth is 65.5% of the 2.90-point gross adverse contribution, not a causal fraction
of the input-level treatment effect. Restoring observed depth positions implies
4.7 (lower only), 5.6 (higher only), or 6.6 (both), conditional on the reconstruction
and current residual. Changing Excel inputs is not guaranteed to restore positions.

The collapsed all-sixteen-parameter legacy table audits the old model with one-at-a-time,
leave-one-out and exact Shapley effects. They explain its mathematical prediction,
not the real loss. Depth’s zero Brand effect in that model is a structural omission.
Prospective depth changes now flag unknown Brand response and block optimization.
The recommended experiments are separate higher-depth 10 → 15 and lower-depth
25 → 30 tests with the other fifteen inputs held fixed, tracking positions, Brand,
margin, inventory and cash. No automatic adoption or optimal depth is claimed.

Brand fell **6.3 → 3.7** (−2.6 points, −41.3%), with rank **#1 → #5 of 7**.
The equal-weighted six-competitor mean rose ~0.433 points. Getchell’s gap
to that mean deteriorated ~3.033 points. This is not a controlled causal estimate.

Frozen v2 expected **+0.164 points**; actual minus modeled is **−2.764**:
`6.3 + 0.164 − 2.764 = 3.7`. This residual quantifies model failure; it is not a
measured competitor effect or an attribution to quality/mix/depth.

The page shows all twelve reported product-position changes and all submitted
inputs against the **unverified old screenshot reference**. Higher-cost depth
position 5.0 → 1.2 (−76%), lower-cost depth 3.7 → 1.7, breadth 2.4 → 3.9 and
service 3.4 → 3.2 motivate specific controlled tests. Experience rose 5.8 → 6.0,
so a blanket claim that all experience deteriorated is inconsistent with the data.

No causal percentage of the loss is assigned to an individual input. The PDF
resolves Private Brand as mix but not its numeric response; the position/score
transformation remains unidentified. One simultaneous bundle cannot identify it.

## 2. Financial risk and resilience

### Margin: the offering mix helped, but within-offering margins fell

Use offering-revenue totals for weights (financial totals retain a $1 rounding
difference). With mix `w` and offering margin `m`:

```
change = Σ w1*(m1-m0) + Σ (w1-w0)*m0 + source-rounding residual
```

Within-offering rate effect is ~**−2.912 pp**, while mix helps **+0.322 pp**;
net reported gross-margin change is **−2.590 pp**, to **33.605%**. Higher-cost
margin fell 39.759% → 34.211%; lower-cost 35.065% → 33.333%. Effective markups
`revenue/COGS − 1` contracted **54% → 50%** and **66% → 52%** respectively.
Current effective markups match submitted inputs within rounding, consistent with
the definition `margin = markup/(1+markup)`. This reconciles the price/cost spread;
it does not identify quantity response or attribute unit-cost changes to vendors,
quality, inflation or category mix. Absolute gross profit still rose **$27.02M**.

### Cash: a consistent proxy bridge, not an observed cash-flow statement

Cash fell **$4,598,444**. The bridge uses net income + depreciation − gross-P&E
increase − receivables increase − inventory increase + payables increase + debt
balance changes. It reconciles within **$1**. Inventory absorbed **$12.22M** and
receivables **$4.48M**; gross-P&E increase is a **$31.94M capital-movement proxy**.
It is not verified cash capex: disposals, noncash assets, timing and reclassifications
are unobserved. Matching a balance-sheet identity does not prove cash classifications.

### Liquidity, financing and conditional stresses

Current ratio improved **0.563 → 0.612×**, but quick ratio slipped
**0.242 → 0.234×**. Working capital improved yet remains **−$72.99M**. Stock is
~61.7% of current assets; converting stock to cash at book value changes quick
liquidity but not the current ratio. Receivable collection has the same composition
distinction. Reclassification/refinancing can change liquidity without creating wealth.

EBIT is **$42.99M**, interest **$30.06M**, cover **1.43×**, pretax buffer
**$12.92M**. At fixed revenue/opex/interest, margin headroom to pretax break-even
is ~**2.682 pp**, and sales headroom at the same margin is ~**7.98%**. An illustrative
2× cover target requires ~$17.14M extra EBIT; this is not a simulator constraint.

Independent scenarios show −1pp margin, −5% revenue at unchanged margin, +1pp
borrowing cost on period-end debt, and ten extra inventory days at COGS/365. They
are not forecasts, combined stresses, or the simulator's documented DOI rule.
Observed effective tax is applied only to positive income, with no loss refund.

## 3. Customer segments and the Kahn matrix

At export 1 the main view followed the **team's then-current Experience-first /
Low Price-second strategy**, not a presumed Brand recovery objective. **The
Round 3 strategy has since shifted to Experience leadership + very competitive
Brand, with Segment 3 primary and Segment 5 conditional secondary** (see
`ROUND2_REVIEW.md`). The historical analysis below is retained as an export-1
diagnosis; team intent never established causality or proof that the last
decision bundle worked.

STP is checked against Intro pp7–10 and current raw preferences. Segment 6 is the
clearest primary acquisition candidate (Low Price / Experience / in-store);
Segment 4 is selective secondary with mixed and omnichannel needs. Segment 5's
large Experience-led business and Segment 2's leading revenue pool are defended.
Segment 3 retains credible Brand parity, not a renewed leadership spending goal.
Intro p9's illustrative segment examples do not replace p8's explicit profiles.
Market consumers, our revenue/mix, raw intensity and missing CLV/contribution are
kept distinct; no market penetration or segment profitability is inferred.

Low Price is operational efficiency plus credible selling prices—not the
lower-cost offering label. Vendor management is the documented structural lever;
Experience, analytics and sufficient service must be protected. A separate
50% → 48% markup test implies a 1.33% price reduction and a 4.17% unit increase
to preserve gross-profit dollars at unchanged unit cost, excluding other costs.
At fixed cost-plus markup, lower unit costs also lower prices and gross-profit
dollars per unit; margin percentage remains m/(1+m). Savings do not automatically
fund more Experience.

Working fair value is the CSV FAIR VALUE series: Brand 3.50, Experience 4.30,
Frictionless 5.10 and Low Price 3.60. Gaps are +0.20, +1.70, −1.80 and +1.10.
Brand already meets parity; Frictionless does not. These are reported benchmarks,
not floors recalculated using 75% or exactly 67% of the displayed leader.
Refresh them from the next resolved round; the slide discrepancy is audit-only.

### Optional historical diagnostics

No segment-specific Kahn scores or response rates are supplied. The analysis
maps all eight raw preferences once to four quadrants, normalizes by each
segment’s preference sum, then forms a descriptive index of the **same observed
company scores**. It is not measured satisfaction, utility or purchasing causality.

Two crosswalks expose assumption sensitivity:

- **Convenience:** Brand ← BRAND; Experience ← SERVICE + SHOPPING EXPERIENCE;
  Frictionless ← ONLINE + RETAIL + BREADTH + DEPTH; Low Price ← LOW PRICE.
- **Product benefits:** assign BREADTH + DEPTH to Brand instead, keeping all
  other assignments unchanged. Neither map is asserted as the simulator rule.

For each segment: `I = Σ normalized_weight[q] * company_Kahn[q]`.

```
ΔI = Σ weight1*(score1-score0) + Σ (weight1-weight0)*score0
```

The first term is descriptive exposure to company score changes; the second is
preference drift. It is not a causal decomposition of segment purchases. Weighting
indices by company segment-revenue shares yields a portfolio index with an exact
within/mix decomposition using the same R1-weight/R0-index convention.

Segment 3 is most Brand-sensitive under both maps, but the largest
**revenue-weighted Brand exposure index** changes from Segment 3 (convenience map)
to Segment 2 (product map). That index is not revenue at risk. Missing segment
profit, cost-tier/channel affinity, satisfaction and controlled outcomes are
explicitly disclosed. No automatic budget allocation follows from these rankings.

## 4. Round 1 recommendation and Decision studio

`/#recommendations` covers all 16 workbook inputs for the next Round 1 submission,
leading to Round 2 outcomes. It is not a retrospective rewrite of Round 1 actuals.
The user has now confirmed the Round 1 allocation budget: **$71,422,000**.
This supersedes the earlier unknown-budget/budget-neutral draft. Proposed spend:
online $6.5M, service $15M, experience $14M, vendor $27.608M, analytics $8.314M.
Total $71.422M; unallocated budget $0. The $1.608M increase over prior spending
goes to Experience (+$1M selected test increment) and vendor (+$608k residual),
without cutting service or analytics. These are not fitted optimum amounts.
Depth is now **held at lower 25 / higher 10**: the earlier 25→30 / 10→15 repair
draft used a superseded threshold. Brand is already above CSV fair value by 0.20.
Only investigate increases if the buffer erodes or customer evidence justifies
them; the input-to-position response and inventory cash cost remain unknown.

Updated objectives: Brand ≥ CSV fair value (R1 reference 3.50, buffer +0.20);
shrink ZEPHARA minus Getchell's Experience below the current 0.40 gap using both
R2 scores; improve Low Price above 4.70; preserve Frictionless with a 3.30
monitoring reference while explicitly deferring full parity in R2. This last
choice accepts risk; it does not amend the game's documented parity rule.
Budget compliance does not establish cash/credit feasibility. The draft remains
not submission-ready until inventory, financing and outcome checks are reviewed.

Decision studio groups all inputs by strategic job and checks Experience ≥6.0,
Experience above our other scores, shrinking fixed-peer Experience gap as a
proxy, Low Price >4.7, Brand CSV parity, Frictionless preservation (not a
hard R2 parity gate), and the confirmed budget. These are local diagnostics only;
the actual competitive gap requires observed R2 scores for both companies.
The studio starts at the actual **Round 0 submitted workbook values** (not the
old screenshot reference). Its top live budget shows submitted spend $69.814M,
extra allocation $1.608M, current draft spend and remaining $71.422M capacity.
Editing a spending input updates the budget without a prediction request; blank
or invalid spending fields suppress the total, and overspending is flagged.
The recommendation and studio share the same 16-value draft. Explicit **Load
recommendation & predict** buttons on both pages copy it into the sandbox and
request a conditional prediction. Per-factor recommended values and a comparison
table make deviations visible. Reset returns to Round 0 submitted inputs.
Predictions use the last calculated inputs and are marked stale after editing;
unchanged inputs reproduce observed Round 1 by construction, not a Round 2
business-as-usual forecast. Budget headroom is not free cash or inventory funding.
Brand no longer displays an unexplained `?` when depth/breadth/mix changes.
The matrix shows the numeric modeled component with a **Partial** badge and
identifies the changed inputs. `score_diagnostics.BRAND.full_prediction` is null
when these response channels are missing; the numeric component includes only
the R1 anchor plus modeled quality response. It is neither a full forecast nor a
lower bound. For scenarios that change depth/breadth/mix, full Brand parity
remains unknown and optimization remains blocked. The current recommendation
holds those inputs, so this missing-channel condition is not triggered by loading it.
Assumptions, factor probes, grid search and historical audits remain available
but collapsed. The optimizer's old diagnostic weights do not encode team policy;
its result is never automatically adopted or described as a game optimum.

## Validation

`tests/test_decision_insights.py` checks Brand changes/ranks, margin and cash
reconciliations, independent stress formulas, normalization and index identities,
crosswalk sensitivity and non-mutation. Browser smoke checks all three tabs,
direct reloads, keyboard focus, segment/crosswalk controls, mobile charts and no
changes to Decision studio state. `tests/test_strategy_analysis.py` checks the
16-factor coverage, round horizon, STP evidence, arithmetic, funding and
non-mutation; browser checks include the recommendation route and studio policy
checks. Run the standard suite in `README.md`.
