# Round 1: observed results and frozen model audit

> Historical export-1 audit under the earlier naming convention. Renamed workbooks do not rewrite this frozen backtest. The current dashboard compares exports 1 → 2 and plans Round 3; see `ROUND2_REVIEW.md`.

Submitted workbook: `decision_making/round_0/decision_making_team11_0.xlsx` (Column B). User confirms this plan produced Round 1.
SHA-256: `ce6b3482e2a472ae944b0bdaf8b8bd01c22bc42b2102d023ebe65be69dca0d87`

## Observed trade-off

Revenue $372,795,207 → $481,926,248; net income $-6,289,333 → $8,399,905.
Market value $93,198,802 → $248,965,528; Brand 6.3 → 3.7; Experience 5.8 → 6.0; Frictionless 3.4 → 3.3; Low Price 4.9 → 4.7.
Growth and profitability improved, but Brand deteriorated; higher equity market value does not establish improved strategic positioning.
Cash fell and inventory increased despite profit. Gross margin compressed; interest still absorbs most operating profit.

## Frozen v2 predictions for submitted plan

|Metric|v2 modeled|Round 1 observed|Modeled minus observed|
|---|---:|---:|---:|
|revenue|376,615,888.8390|481,926,248.0000|-105,310,359.1610|
|net_income|-17,698,965.4630|8,399,905.0000|-26,098,870.4630|
|BRAND|6.4636|3.7000|+2.7636|
|EXPERIENCE|5.9371|6.0000|-0.0629|
|FRICTIONLESS|3.7790|3.3000|+0.4790|
|LOW PRICE|5.1369|4.7000|+0.4369|

Retrospective one-transition error audit; not an out-of-sample validation suite. Alternatives were not simulated and have no observed outcomes.

## Model changes

- Re-anchor at observed Round 1 scores and financials, using the actual submitted workbook as decision reference.
- Use PDF-consistent direct pathways with uncalibrated numerical priors: analytics only multiplies online/experience; vendor does not directly raise Brand; stores change access, not preference.
- Apply quality/vendor unit-cost changes to both COGS and cost-plus selling prices under explicit scenario response rates.
- Separate capitalized investment, depreciation, inventory funding/financing and store capex/disposals. Holding expense is a documented zero; new stores cost $1.75M.
- Analytics is expensed. R1 online/experience expense fractions and service input ratios remain provisional scenario defaults.
- Unspecified economic coefficients are exposed as unresolved, never treated as verified zero effects by the new optimizer.
- Apply observed effective tax rate only to positive modeled pretax income.
- Retire fixed-P/E market-value projection. Document max(DCF, CLV/private-brand, liquidation); changed-plan value and market-value optimization are unavailable without the missing formulas.
- Show all sixteen factors with isolated plus/minus probes, prior-weight dependencies, unpriced changes and historical forecast errors.

## Evidence limits

- Private Brand is mix per MarketValue_Slides p12, superseding the duplicated Markdown definition; numeric response/exposures are still unknown.
- The national-brand-quality line is unlabeled in Markdown but confirmed by Intro p14.
- Slides specify $1.75M/store and no inventory holding expense; numeric response, financing, retention and valuation formulas remain incomplete.
- Input bounds and numerical response rates remain provisional; slides do not supply a fitted simulator formula.
- A reported-position Brand reconstruction links depth to Brand; its decision-input response is not identified. The old zero Brand depth coefficient is a structural omission, not evidence of no effect.
- Only one linked submitted plan and result; competitors, demand trends, costs and all decision changes are confounded.
- The prior reference plan was a screenshot assumption, not a verified Round 0 historical submission.
- Budget rule is max(14% prior revenue, inflation-adjusted prior budget). Prior actual budget/inflation are unknown; $69.814M is submitted spend, not a verified budget ceiling.
- Cash diagnostics omit receivables, payables and debt flows. Scenario rates are unestimated; valuation does not establish fair value.
- Segment revenue reconciles to company revenue within $1; it is not total addressable market.
- Intro p7 labels market size as consumers. Segment market population is not Getchell’s unique buyers; revenue mix is not penetration.
- Preference values are relative weights, not population percentages or estimated elasticities.
- Round 1 segment CLV is unavailable; Round 0 CLV is not carried forward as current.
- FAIR VALUE is a moving quadrant benchmark, not a retailer. Use its CSV values as the active floors; the conflicting 75% slide formula is audit-only. Ratios are approximately two-thirds, not an exact 67% replacement rule. Brand's active R1 gap is +0.20, not −0.20.
- Price is defined as cost plus markup. Pricing-file values match cost metrics; do not treat those file values as selling prices.

## Accounting checks

|Input|Submitted|Reported expense|Expense/input (provisional)|
|---|---:|---:|---:|
|online|6,500,000|2,600,000|0.4000|
|service|15,000,000|17,409,631|1.1606|
|experience|13,000,000|10,400,000|0.8000|
|vendor|27,000,000|27,000,000|1.0000|
|analytics|8,314,000|8,314,000|1.0000|

Neither Brand collapse nor market-value growth is assigned causally to a single decision. Optimizer alternatives have no observed simulation result.
