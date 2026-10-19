# PDF-grounded simulation review

> Rules and historical export-1 audit snapshot. Current outcomes, CSV fair values and timeline are in `ROUND2_REVIEW.md`; current model context is in `MODEL_CARD.md`. Do not reuse the old budget or strategy readout below as a Round 3 recommendation.

Increase simulated equity market value through targeted customer value, two credible differentiating quadrants and fair value in the other two—not Brand, profit or a weighted score alone.

Sources: Intro = `materials/PivotOrPerish_Intro wemba.pdf`; MV = `materials/MarketValue_Slides.pdf`. Page numbers are PDF pages. Demo data/access information is not exported.

## Corrections to the earlier analysis

- FAIR VALUE is a moving benchmark, not an eighth retailer. Use the CSV FAIR VALUE values as the working floors; Intro p15’s conflicting 75% rule is source-audit context only.
- MV p12 resolves Private Brand as mix, superseding the duplicated Markdown quality definition; realized brand-type sales exposures and numeric effects remain unavailable.
- MV p14 specifies no inventory holding costs and $1.75M per store. Inventory funding/interest and reinvestment still matter.
- Intro p14 provides direct quadrant pathways. MV p13 says analytics has no standalone demand term; vendor benefits persist and compound.

## Brand hypothesis and strategy

Depth remains the leading observed score-linked symptom, but the PDFs prioritize high-quality brand/mix, retained assortment, targeted customers and two-quadrant coherence. Depth alone is not an adequate repair strategy or a verified causal formula.
Team-selected strategy: Experience first, Low Price second; Brand is a parity safeguard, not the recovery objective. Segment 6 is the primary acquisition candidate, Segment 4 a selective secondary target; defend existing Segments 2 and 5. Experience should remain our strongest quadrant, not necessarily #1 among retailers. This is team policy, not an inferred optimum.
Using CSV fair value, Brand is already 0.20 above its 3.50 floor; Experience is 1.70 above 4.30, Low Price 1.10 above 3.60, and Frictionless 1.80 below 5.10. Preserve Brand parity rather than spend to repair a nonexistent current shortfall. Full Frictionless parity remains a deferred R2 team goal, not a removed game risk.

|Candidate two-quadrant strategy|Slide-aligned segments|What must be tested|
|---|---|---|
|Brand + Experience|3; selective 4|Builds on historical Brand leadership and current strong Experience. Requires Brand recovery and Frictionless parity; not just more quality spending.|
|Low Price + Experience|6; selective 4|Current scores are 85%/94% of their leaders, closer than Brand. Needs vendor-led efficiency and differentiated value without destructive markup cuts; Frictionless and Brand parity still need attention.|
|Frictionless + Experience|5|Matches the slide profile, but Frictionless is only 43% of the current leader. Requires substantial online/analytics capability; Brand parity cannot be abandoned.|

The winning valuation route is unobserved. Market value rose despite WACC rising 7.8% → 7.9%; the observed increase cannot be attributed to a lower discount rate. Earnings/CLV improvements may offset strategy deterioration, but the contribution of each route is not supplied.

## Fair value: CSV benchmarks govern the analysis

Use the reported FAIR VALUE for each quadrant and round from kahn-round1.csv. Approximately two-thirds of the displayed leader is a descriptive ratio, not a replacement formula. The slide 75% rule is retained for source audit only.

|Round|Quadrant|Getchell’s|Leader|CSV fair value|Active gap|CSV floor / leader|
|---|---|---:|---|---:|---:|---:|
|0|BRAND|6.30|GETCHELL'S 6.30|4.20|+2.10|66.67%|
|0|EXPERIENCE|5.80|ZEPHARA 6.50|4.30|+1.50|66.15%|
|0|FRICTIONLESS|3.40|CADABRA 7.80|5.20|-1.80|66.67%|
|0|LOW PRICE|4.90|AIM 5.40|3.60|+1.30|66.67%|
|1|BRAND|3.70|ZEPHARA 5.20|3.50|+0.20|67.31%|
|1|EXPERIENCE|6.00|ZEPHARA 6.40|4.30|+1.70|67.19%|
|1|FRICTIONLESS|3.30|CADABRA 7.60|5.10|-1.80|67.11%|
|1|LOW PRICE|4.70|AIM 5.50|3.60|+1.10|65.45%|

## All sixteen pathways

|Input|Documented pathway / mechanism|Source|
|---|---|---|
|low_markup|LOW PRICE: Immediate margin/demand trade-off; no persistence.|MV 12; Intro 14|
|high_markup|LOW PRICE: Immediate margin/demand trade-off; no persistence.|MV 12; Intro 14|
|low_breadth|Assortment / loyalty: Retained; supports appeal/basket size and ties up working capital, with financing costs.|MV 12|
|high_breadth|Assortment / loyalty: Retained; monitor capital efficiency rather than maximizing categories.|MV 12|
|low_depth|Assortment / loyalty: Retained within-category choice; stock funding and interest matter.|MV 12|
|high_depth|Assortment / loyalty: Retained within-category choice; the observed Brand identity is still not an official formula.|MV 12|
|low_private|BRAND / valuation: Private-brand MIX supports differentiation, loyalty, margins and the CLV/brand valuation route; coefficients/exposure rules absent.|MV 6, 12|
|high_private|BRAND / valuation: Mix meaning is now supported; 70% is a decision setting, not measured sales share.|MV 6, 12|
|private_quality|BRAND: Higher quality supports willingness to pay, raises COGS and needs vendor/cost discipline.|Intro 14; MV 12|
|national_quality|BRAND: High-quality national brands support Brand; unit-cost and willingness-to-pay rates remain unknown.|Intro 14; MV 12|
|coverage|Access / capital / debt: Stores change access, not preferences/retention. Identical stores; $1.75M per new store; financing split and marginal access response unspecified.|Intro 13; MV 10–11, 14|
|online|FRICTIONLESS: Partly capitalized; amplified by analytics; debt-funded growth needs proportional cash-flow gains.|Intro 14; MV 12–13|
|service|FRICTIONLESS / EXPERIENCE: Immediate, fully expensed, little persistence; tactical satisfaction, not a standalone durable advantage.|Intro 14; MV 13|
|experience|EXPERIENCE: Medium-term persistence, mostly expensed, amplified by analytics; diminishing returns.|Intro 14; MV 13|
|vendor|LOW PRICE / structural costs: Fully expensed but highly retained: compounds COGS improvements over time; can reduce financing risk.|Intro 14; MV 13|
|analytics|Multiplier, not standalone demand: Amplifies online and experience; expensed, no separate capital asset or independent demand term.|Intro 14; MV 13|

## Valuation model correction and forecast horizon

max(DCF equity value, CLV/private-brand-adjusted value, liquidation value)
FCF_t = operating cash generation less reinvestment; PV = Σ FCF_t/(1+WACC)^t + terminal PV; apply the simulator equity bridge, then compare the three methods.
Mechanism documented; exact simulator forecast, floors and adjustments unavailable. Constant P/E is not the valuation rule.
MV pp3/14 say stronger/stable strategy earns shorter forecast T, while p8 describes a one-dimensional weak strategy as low T. Do not equate longer T with greater durability or invent a monotonic mapping.

Missing inputs required for numerical reproduction:
- Revenue/margin/SG&A/reinvestment forecast rules
- Strategy-to-T mapping (6–12 years stated)
- Terminal cash flow, growth and equity-bridge conventions
- CLV/private-brand valuation coefficients
- Liquidation recovery rates
- AAA rate, credit-ratio breakpoints, debt-rate schedule and financing weights
- Store debt/cash financing split and automatic borrowing mechanics

The active model no longer presents fixed-P/E sensitivity as simulated market value. Changed-plan valuation and the market-value optimizer are blocked rather than inventing DCF/floor parameters. The frozen v2 engine remains an error audit only.

## ROIC, WACC and funding

|Round|Pre-tax ROIC proxy|Reported WACC|Spread (pp)|
|---|---:|---:|---:|
|0|6.84%|7.80%|-0.96|
|1|11.94%|7.90%|+4.04|

Budget rule (Intro p16): max(14% of previous revenue, previous budget with inflation allowance). R1 revenue arm for the next budget is $67,469,674.72. Exact next budget is unavailable; Revenue arm is computable; actual prior budget and inflation allowance are not supplied. The $69.814M submitted spend is not proof of the prior budget. Demo slide screenshots are not this team’s budget.

## Segmentation (Intro pp7–10)

- SEGMENT 1: Frictionless / Low Price; online; competitors CADABRA
- SEGMENT 2: Low Price / Frictionless; in-store; competitors AIM, PRICEMART
- SEGMENT 3: Brand / Experience; competitors ZEPHARA
- SEGMENT 4: Mixed needs; in-store; competitors AIM, ZEPHARA, KTBENNEY
- SEGMENT 5: Frictionless / Experience; competitors ZEPHARA
- SEGMENT 6: Low Price / Experience; in-store; competitors BESTCO

## Remaining boundaries and conflicts

- CSV FAIR VALUE is the active benchmark. Its ratios to displayed R1 leaders range from 65.5% to 67.3%, so do not recalculate every floor as exactly 67% or two-thirds. The conflicting 75%-of-leader slide rule is retained only as an audit note.
- Slides describe mechanisms and qualitative persistence, not calibrated elasticities, retention rates or next-round coefficients. The local model is still not a replica.
- ROIC uses EBIT / (debt + book equity − cash) at period end, a pre-tax proxy—not the simulator’s verified capital definition or store-level profitability. Comparing it to WACC is a teaching diagnostic, not conclusive economic profit.
- MV p11 cautions against idle accumulating cash; this team’s cash fell and liquidity is weak. Fund positive-return investments rather than either hoarding or spending indiscriminately.
- The one Round 1 undo in Intro p24 is a limited learning opportunity, not evidence of unlimited resettable experiments. Design tests before using it; no live submission is authorized.
