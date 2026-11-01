# Round 6 review · Round 7 analysis, not an allocation

Sources: `materials/round6/{marketing,finance}` cumulative histories and actual
workbooks in `decision_making/round_0` through `round_6`. Current planning budget:
**$83,151,028**, confirmed from the simulation and labeled in the Round 7 workbook.
No decision workbook or simulator submission has been changed.

| Quadrant | R0 | R6 | R6 CSV floor | R6 rank | Gap to current team target |
|---|---:|---:|---:|---:|---:|
| Brand | 6.3 | 5.0 | 3.4 | 1 | 0, top two met |
| Experience | 5.8 | 4.8 | 4.7 | 3 | 2.2 to leader |
| Low Price | 4.9 | 4.7 | 3.7 | 6 | 0, floor met |
| Frictionless | 3.4 | 2.9 | 4.7 | 5 | 1.8 below floor |

## Execution diagnosis

Getchell’s service position fell **3.4→1.5**. Shopping-experience position improved
**2.4→3.3** and online position **0.0→1.3**, but those gains did not compensate for
service deterioration. Across 49 retailer-round observations, Experience is
approximately shopping-experience position + service, and Frictionless is online
position + service (maximum error 0.1). This is evidence about reported outputs,
not proof of the simulator formula or a calibrated dollar-to-score response.

Service input fell $15M→$13.079M while company revenue grew; spending per store
also declined from $75,000 to roughly $68,838 despite closures. The source slides
describe service as low-persistence and analytics as a multiplier, not standalone
demand. These support investigating service capacity; they do not isolate its
causal return, competitor effects or the optimum spending level.

## Finance and segment outcomes

Market value rose **$93.20M→$798.72M**, net income **−$6.29M→$66.28M**, and debt fell
**$286.92M→$119.74M**. Gross margin improved, but WACC is **10.3%**, versus **7.8%**
at R0. Rounded product-row unit share fell **13.0%→11.9%**. Financial recovery and
strategic/customer-execution success must not be treated as synonymous.

All six segments increased revenue and aggregate CLV from R0. Their growth rates,
mix shifts and changing needs differ; Segment 1 now has the largest aggregate
CLV. Historical target roles must not override current observations. Aggregate
CLV, market population and company revenue have different denominators. No
segment contribution, acquisition cost, retention or spending attribution is
available, so causal segment ROI is unknown.

## Empirical valuation diagnostics

Six lagged transitions and fifteen distinct input series support direct fits for
Brand and Low Price, plus two-stage position models for Experience and
Frictionless. Fitted / hide-one-transition / persistence MAE is Brand **0.05 /
0.28 / 0.68**, Experience **0.07 / 0.14 / 0.23**, Low Price **0.02 / 0.15 /
0.10**. Low Price is nearly flat, so persistence is more accurate there. Experience is
**customer-service position + shopping-experience position**; Frictionless is
**online position + customer-service position** (maximum difference 0.1 points),
so both components enter positively in the reconstruction. This is not verified
simulator code or a causal spending response.

**Frictionless audit supersedes the old 0.06 / 0.11 fit.** That model misplaced
analytics as standalone service demand and estimated substantial service carryover.
The revised conditional diagnostic has no service carryover, service spending
only, and an online × analytics interaction with nonnegative slopes. Same-round
expense alignment is verified, but score timing remains uncertain; both timing
alignments are shown. Current fitted / hide-one MAE is **0.089 / 0.197**.
Earlier-only R4–R6 MAE is **0.214** (lagged sensitivity **0.290**) versus
**0.067** persistence; the former model scores **0.158** on those same checks.
Persistence wins. No Round 7 budget optimization is justified. The small positive
interaction coefficient is constrained, not evidence of a calibrated analytics
return. The old pooled position check does not validate this mechanism. Experience
retains its older lagged service/analytics association, explicitly not verified
mechanics. All earlier-only checks remain retrospective and conditional on
observed inputs, not frozen pre-outcome forecasts.

For market value, the selected non-circular finance model is ln(Market value) =
−6.7419 + 1.6120 × ln(EBIT) − 0.2364 × WACC − 0.5570 × book debt weight. Fitted /
hide-one-period / R5–R6 MAPE is **1.9% / 7.1% / 8.0%**, versus **36.5%** for
previous-period persistence. Book debt weight avoids the mechanical circularity
of market debt weight. A service-intensity specification has lower raw error,
but it is a decision proxy. Evaluation-period inputs are observed, not forecast.
Neither model reproduces the simulator valuation rules or supports a near-optimal
16-factor allocation.

## Decision factors and WACC

Reported WACC is **10.3%** at R6 versus **7.8%** at R0, even though debt fell from
**$286.92M to $119.74M** and interest coverage improved. This rules out a simple
“less debt always lowers WACC” reading. All 16 inputs act on WACC indirectly:

- markup → gross-profit dollars and cash generation versus volume loss;
- breadth/depth → customer benefit versus inventory and working-capital funding;
- private mix/quality → differentiation and CLV versus cost, stock and execution;
- stores/online → capital, access and financing needs;
- service/experience/analytics → near-term EBIT versus demand, retention and
  paired-investment returns;
- vendor → retained cost and inventory efficiency versus current expense.

The selected exploratory financing association is
**WACC (%) = 11.0213 − 3.7763 × market debt weight + 4.8951 × ln(EBIT ÷ market value) + 1.9962 × ln(EBIT in $M)**.
Ridge λ=0.03 is chosen by a hide-one-round grid search. Errors improve to
**0.06 pp fitted, 0.11 pp hide-one-round and 0.28 pp earlier-period-only (R5–R6)**,
versus 0.23 / 0.39 / 0.54 pp for the previous two-feature form, 0.88 / 1.27 /
2.45 pp for the earlier book-weight/coverage form, and 0.65 pp for persistence.
A 377-subset search scored worse under nested selection (0.51 pp), and adding a
fourth feature did not improve it (0.12 pp), so the three-feature model is the
best validated specification in the tested space—not a global optimum. The signs
are locally coherent—higher market leverage lowers WACC in this sample, while a
higher earnings yield and larger EBIT scale accompany a higher WACC—but EBIT and
market value are jointly determined. It should not be used to rank or optimize
the 16 factors. Private and national quality inputs have both been fixed at 8
since R3 and cannot be separately identified.

The defensible Round 7 test is contribution-based: evaluate gross-profit dollars
after volume response, stock/inventory funding, liquidity and coverage together;
compare incremental ROIC against financing cost; and keep the confirmed
**$83,151,028** ceiling. Lower WACC is not itself the objective.
