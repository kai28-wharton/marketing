# Archived review model 4.0 · export-1 conditional sensitivity

Historical model documentation. Current context and limits: `../MODEL_CARD.md`.

## Evidence and intended use

One user-confirmed submitted workbook is linked to Round 1 results. Two financial
rounds and four Kahn/segment-history rounds are available. Sixteen inputs changed
as one bundle relative to an unverified screenshot reference; competitor behavior,
cost changes and time trends are confounded. There is **no identified causal
factor model, held-out forecast accuracy, intrinsic fair value or global optimum**.
The two supplied PDFs now take precedence over ambiguous older Markdown.
`simulation_rules.py` records page-cited rules; `SIMULATION_REVIEW.md` contains
the reconciliation. Private Brand is mix (MV p12); quality is separately
identified. A new store costs $1.75M and inventory has no holding expense
(MV p14). Numeric demand, retention, financing and valuation rules remain incomplete.

Use this model to inspect explicit assumptions and formulate simulator tests,
not to select a budget automatically. `prediction.py` retains the frozen v2
functional form/coefficients for reproducible historical comparison.

## Historical audit

V2 applied to the submitted workbook under Round 0 inputs modeled revenue
$376.62M, net loss $17.70M and Brand 6.464 with the latest workbook (lower-cost
depth 25, not the earlier 50). Round 1 observed revenue was $481.93M,
net income $8.40M and Brand 3.7. See `ROUND1_REVIEW.md` for all errors.

The three prior optimization objectives are re-run from the submitted plan using
Round 0 information. Their allocations, guardrails and modeled outputs are shown,
but their real simulator results are unknown. They do not establish superiority
over the team plan. The new current-model optimizer is a separate exhaustive
finite-grid scenario search, not a simulator-validated allocation engine.

## Re-anchoring, not fitting

### Brand structural-gap audit

`brand_impact.py` identifies an empirical position-to-Brand reconstruction:
`Brand ≈ .5*(lower depth + higher depth + lower private-brand + higher private-brand)`.
It matches all 14 available retailer-round rows within 0.05 points; it was
discovered and checked on the same rows, not held out. Getchell’s observed
changes reconstruct −1.00 −1.90 +0.15 +0.15 = −2.60, with no residual drift.
The current workbook has depth 25/10 at B4/B8. This supports depth as the primary
score-linked pathway, not a measured causal derivative of Excel inputs.

The old Brand equation has no depth term. Its exact per-parameter Shapley audit
therefore gives zero to depth, demonstrating model misspecification rather than
no real effect. The future input-to-position function is still unidentified; no
coefficient is fitted from this one bundle. When depth is changed prospectively,
`unresolved_model_channels` includes `brand_depth_response`; the UI suppresses
the incomplete Brand point forecast and the current optimizer blocks the result.
Other sensitivity outputs remain partial and explicitly omit that response.

Current inputs `p₀` are the actual submitted Column B values. Current outcomes are
observed Round 1. Unchanged inputs reproduce observed revenue, income and scores
exactly, retaining reported dollar rounding. This is true **by construction**.
The residual v2 error is not assigned to any particular decision or silently
added as repeated next-round growth.

`guided_prediction.py` replaces the active v2 score pathways, without changing
the frozen audit. It retains saturation/logistic numerical priors only on
compatible pathways: quality→Brand; online→Frictionless; service→Experience/
Frictionless; experience→Experience; vendor→Low Price; markup→Low Price.
Analytics has only online×analytics and experience×analytics terms—no independent
demand/Brand/Low Price term. Store count no longer changes preference scores.
Numeric weights, saturation scales and exposure weights are uncalibrated priors,
not the simulator's official response functions. Qualitative persistence is
documented, not simulated with invented retention rates. Missing assortment,
private-mix and store-access/financing channels block affected grid comparisons.

The current Kahn anchor is 3.7 Brand, 6.0 Experience, 3.3 Frictionless, 4.7 Low
Price. Intro p11 confirms a developer-generated 0–10 position scale; the local
logistic score response is still assumed. A change in score is not a measured
change in satisfaction, unit demand or profit.

## Earnings channel

For each cost tier:

```
vendor_capacity_change = proposed_vendor/(proposed_vendor+h) - baseline_vendor/(baseline_vendor+h)
quality_change = average(private_quality_change, national_quality_change)
unit_cost_ratio = exp(quality_cost_per_point*quality_change
                      - vendor_cost_sensitivity*vendor_capacity_change)
price_ratio = unit_cost_ratio * (1 + proposed_markup/100) / (1 + submitted_markup/100)
weighted_score_change = .35*Brand + .35*Experience + .20*Frictionless + .10*LowPrice
unit_ratio = max(.1, 1 + demand_response*weighted_score_change
                         - price_elasticity*(price_ratio - 1))
revenue_change = R1_tier_revenue * (price_ratio*unit_ratio - 1)
COGS_change = R1_tier_COGS * (unit_cost_ratio*unit_ratio - 1)
gross_profit = observed_R1_gross_profit + revenue_change - COGS_change
```

Demand response .025, elasticity 1.2 and score strength .55 remain explicit prior
defaults, not fitted simulator rules. No per-segment elasticity is invented.
Pricing-file values still match cost metrics; actual selling-price definitions
are clarified as cost-plus by the supplied definition. The pricing file itself
still matches cost metrics, not selling prices. Quality cost sensitivity is an
explicit unestimated scenario coefficient. Equal private/national exposure is an
assumption, not a known sales exposure. Private-brand mix meaning is resolved,
but its margin/loyalty/valuation response rates remain unknown.

Online/experience expense shares default provisionally to .4/.8 from R1; their
remaining .6/.2 is capitalized, not free. Both fractions can be overridden as
scenario inputs. Additional capital generates depreciation only at an explicitly
specified same-period rate. Service expense uses 17,409,631/15,000,000; vendor and
analytics are fully expensed. These are **provisional local assumptions**, not
proven marginal/recurring-cost formulas. Other SGA and existing depreciation/
interest stay at observed levels; incremental costs are added separately. Positive pretax income is
taxed at the observed effective rate (~35%); nonpositive income receives no
modeled tax refund.

## Inventory, capital and cash pathways (4.0)

The R1 inventory pool is allocated to offerings by observed COGS shares, not
unverified customer or private-brand shares. Each tier's stock scales with modeled
unit cost and volume and an exponential scenario multiplier:

```
inventory_multiplier = exp(breadth_inventory_sensitivity * breadth_change/100
                         + depth_inventory_sensitivity * depth_change/100
                         - vendor_inventory_sensitivity * vendor_capacity_change)
```

Breadth, depth and vendor directions are supported by MV p12/13; their numeric
stock response rates remain scenarios. Inventory holding expense is fixed at
zero (MV p14), a documented zero rather than an unknown. Financing rates apply
to positive incremental stock only as a partial scenario—not automatic borrowing,
credit scoring or an estimated marginal interest schedule. Stock funding is
separate from COGS; there is no immediate double expense.

New-store capex is fixed at $1.75M/store from MV p14. Stores change access, not
preference. Automatic borrowing/fixed financing split and added working capital
are documented but their formulas are unavailable. Store changes are flagged
unmodeled, not ranked with zero access benefit. Closing requires scenario book
value/recovery and is not a way to expand the allocation budget. No selective
"bad store" closure is modeled: stores are identical in the simulation.

```
incremental_cash_delta = net_income_change + depreciation_change + closure_writeoff
                       - incremental_capitalized_spending - inventory_change
                       + disposal_proceeds
```

This is a difference from unchanged submitted inputs, **not ending cash or a full
cash-flow forecast**. Receivables, payables, debt financing and other flows are
excluded. Partial spending capitalization changes profit recognition, not the
cash cost of the full investment. Closure write-off deductibility follows the
same conditional positive-income tax convention; actual tax rules are unverified.

Unknown scenario coefficients are null. Diagnostic calculations use explicitly
labeled zero placeholders for affected unknown paths; the optimizer cannot
silently use them. Supplied zero coefficients are user assumptions, not learned
no-effect findings.

## Current optimizer and calculation validation

The current optimizer checks every point of an explicitly bounded spending grid
(at most 20,000 nodes) plus an in-range unchanged incumbent. All non-spending
factors are locked. It enforces the user-specified five-spending-input allocation
budget, separate from store capex/funding, maximum incremental cash use and all
four diagnostic score floors (default:
starting scores). Unresolved pathways anywhere in the grid block the whole search.
The selected result is recalculated and checked again before returning.

Tests compare against an independent brute-force enumeration; check budget, cash,
floors, fixed inputs, repeatability, invalid inputs, unknown economics, finite-grid
limits and accounting identities. This establishes **calculation/constraint checks**,
not simulator predictive accuracy. Exact finite-grid optimality is not continuous
or global optimality. The profit/weighted-position objectives are one-period
diagnostics, not the two-quadrant game strategy or a multiperiod value optimum.
The market-value objective is blocked because exact valuation rules are absent.

## Valuation: the fixed-P/E shortcut is retired

MV pp2–6/14 describe `max(DCF, CLV/private-brand-adjusted, liquidation)`.
DCF projects cash flows/reinvestment, discounts at WACC, includes terminal value
and applies an equity bridge. Credit risk follows current ratio, interest cover
and debt/equity; equity rate is AAA +6 percentage points. Exact credit breakpoints,
AAA rate, financing weights, forecasts, terminal rules and valuation floors are
not supplied. No constant P/E or WACC-as-equity-rate substitution is used.

Unchanged inputs show **reported R1 value only**, not a revaluation (including if
economic assumptions are edited). Changed-plan `market_value` and its delta are
null, with missing formulas listed. Market-value optimization returns `blocked`.
P/E and market/book remain descriptive financial outputs.

FAIR VALUE is a quadrant threshold, not an eighth retailer. **Use the CSV's
reported FAIR VALUE values** for active analysis and policy checks, not the
conflicting 75%-leader slide formula. R1 floors: Brand 3.5, Experience 4.3,
Frictionless 5.1, Low Price 3.6; active gaps: +0.2, +1.7, −1.8, +1.1.
The floor/leader ratios range from 65.5% to 67.3%; approximately two-thirds is
descriptive, not a verified universal formula. Brand already meets parity, so
the recommendation no longer automatically increases depth to repair it.
The 75% comparison is retained in source-audit metadata only. No source CSV is
overwritten. The slides also conflict about horizon T
(MV pp3/14 vs p8); no monotonic T-to-strategy coefficient is invented.

ROIC is an explicitly labeled pre-tax period-end proxy: EBIT / (debt + book
equity − cash), 6.84%→11.94%, versus WACC 7.8%→7.9%. This is not verified
simulator/store-level ROIC. Positive proxy spread does not establish expansion ROI.

## Sixteen-factor coverage and stress

For each factor, isolated probes increase/decrease the last calculated plan by:
$1M for spending, 25 stores for coverage, 5 percentage points for markup/private
share, 5 index points for breadth/depth and 1 point for quality. Bounds can suppress
one direction. Tables show partial Kahn/earnings/cash changes, unavailable
changed-plan market value, and flag
unpriced implementation. Isolated probes need not add up because of interactions;
they are neither causal contributions to Round 1 nor an optimization result.

Kahn stress bounds are proposed scores ± the absolute frozen v2 error for the
single observed transition, clipped to 0–10. This exposes the historical miss;
it is **not a confidence interval, calibrated uncertainty or evidence of coverage**.

## Financial and data boundaries

- Inventory, capex, stores and funding are conditional diagnostics only where
  scenario rates are specified. No complete cash or competitor-reaction forecast.
  Positive earnings do not mean sufficient cash.
- Next budget = max(14% previous revenue, inflation-adjusted previous budget).
  The revenue arm is $67,469,674.72; actual prior budget/inflation are unknown.
  $69.814M is submitted spend, not a verified budget ceiling. Unspecified effects
  are omitted from partial diagnostics
  and block affected optimization.
- Round 1 segment CLV is missing; no carry-forward or invented allocation.
- Segment revenue is company revenue; Intro p7 labels market size as consumers,
  not this company's buyers or penetration. Raw preferences are not population shares.
- Ratio diagnostics use explicit statement definitions and end-period balances;
  simulator-specific ROA/turnover values are retained separately, not rewritten.
- Definitions must be supplied, costs clarified and multiple decision/outcome
  rounds collected before recalibrating coefficients or claiming predictive gains.
