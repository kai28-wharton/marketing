# Review model 5.0 · current-export conditional scenarios

## Current evidence and chronology

- Latest submitted decision: **2**, from `decision_making/round_2/decision_making_team11_round2.xlsx`.
- User-confirmed observed outcome package: **`materials/round2`**.
- Latest comparison: export **1 → 2**; current planning period: **3**.
- Prior renamed workbook: `decision_making/round_1/decision_making_team11_round1.xlsx`.
- Segment CLV is now reported, including backfilled historical rows. Segment
  contribution, affinity and measured segment-specific Kahn scores remain absent.
- Latest industry aggregate available is export 1, explicitly labeled as stale
  context rather than treated as export-2 competitor decisions.

## Baseline and model scope

All sixteen studio inputs start at actual submitted decision-2 values. Financials
and scores anchor at observed export 2. No earlier suggested plan substitutes for
the submission. Unchanged inputs reproduce observed current actuals by construction;
this is not a calibrated Round 3 business-as-usual forecast.

The same uncalibrated PDF-compatible local priors are retained: quality → Brand;
experience/service and analytics interaction → Experience; online/service and
analytics interaction → Frictionless; vendor/markup → Low Price. These pathways
are qualitative mechanisms, not learned simulator coefficients. No coefficients
are fitted from two simultaneous decision bundles or competitor outcomes.

Depth, breadth, private mix and store response channels remain unestimated. A
changed assortment/mix scenario labels Brand **Partial**, exposes the modeled
component, and leaves the full forecast null. The component is not a lower bound.
Such missing channels continue to block optimization. No fresh pre-outcome frozen
forecast was supplied for decision 2: stress intervals are null, not fabricated.

## Strategy and segment scope

Team intent is **Experience leadership + very competitive Brand**, with Low Price
and Frictionless held at reported CSV fair value. Experience leadership means
**#1 among actual retailers**, not merely Getchell’s strongest quadrant. Current
scores are Experience 5.8 (#2, ZEPHARA 6.5), Brand 4.1 (#4, BESTCO 4.9), Low Price
4.6 (#7, floor 3.6) and Frictionless 3.1 (#5, floor 5.0). The −1.9 Frictionless
gap is a required safeguard, not a deferred goal.

Segment 3 is the recommended core because its explicit Brand/Experience profile
and raw intensities (Brand 0.30, Shopping Experience 0.40) best match the chosen
proposition. Segment 5 is a larger, higher-aggregate-CLV secondary Experience
pool, but its Frictionless need gates broad acquisition until parity is restored.
Segment 4 remains a selective reserve; Segments 2 and 6 are defended. Reported
segment CLV is aggregate customer equity, not per-buyer value, margin or a
profitability ranking. No segment contribution, acquisition cost, elasticity,
utility score or causal score response is estimated.

The focus is a **tiered group, not a single segment** (the decks’ “one” rule is
one Kahn quadrant, not one segment): **WIN** Segments 3 + 5 with Brand +
Experience, **DEFEND** Segments 2 + 6 at fair value, keep Segment 4 as a
selective reserve, and **SERVE** Segment 1 without acquisition priority. Segment
3’s aggregate CLV is 5th of 6 and its population is the smallest. The data do not
establish how much of its CLV rank is caused by size. CLV divided by total market
consumers is not per-buyer value; Segment 5 supplies a larger population pool,
not a demonstrated acquisition return.

### Customer segmentation decision

`segment_decision.py` supplies the new `/#segmentation` page. Source measures
stay separate: population, population growth, company segment revenue/growth,
aggregate CLV/growth and all eight raw needs. Transparent single-metric lenses
replace a fabricated composite utility or profit score. The Experience lens
orders the debated segments 5 > 6 > 4 > 2; aggregate CLV orders 2 > 6 > 5 > 4.
This distinguishes growth fit from existing-equity defense. Segment 6 receives
an explicit challenger case rather than being ruled out merely for low Brand.

Financial constraints include cash, income, interest cover, inventory, WACC and
the unconfirmed Round 3 ceiling. Named rivals are slide profiles, not observed
segment ownership; current company Kahn scores and product positions permit
relative-capability comparisons, not competitor-by-segment share estimates.
Group selection adds observed totals and a qualitative one-liner only; it does
not edit policy, decisions or the spending draft. Segment 4 population growth
is 5.0%, below S6 (5.4%) and S1 (6.9%), correcting the earlier fastest-growth
wording. The page is also available inside the offline Marketing Intelligence
HTML, without exporting editable decision inputs.

### MarketValue-grounded strategy verdict

The choice of Experience + Brand is justified against the MarketValue deck as a
documented sweet-spot shape (two differentiators, parity on the other two, MV p8),
a fit match (Segment 3 is the only segment whose top-two raw needs are exactly
Shopping Experience and Brand), capital efficiency (mostly expensed levers,
MV pp12–13) and the CLV/brand-adjusted valuation route (MV pp6, 11). Two binding
conditions are recorded: Brand must become genuinely competitive, and Frictionless
parity must be restored. Low Price + Experience is rejected (immediate, non-
persistent markup cuts; BESTCO owns Segment 6); Frictionless + Experience is not
chosen now (weakest quadrant, partly capitalized online build). Each segment’s
already-targeting rival (Intro p8) is shown so competition is treated as a
first-order input. This is a source-grounded judgment, not a calibrated forecast.

## Finance, fair value and funding

Quality/vendor costs affect both COGS and cost-plus price under explicit scenario
rates. Capitalized spending, depreciation, inventory funding, store capex and
financing are separate. Blank rates mean unknown, not verified zero. Current
expense/input ratios supply provisional capitalization defaults. The unchanged
net-income anchor preserves the $1 reported rounding residual rather than
replacing source net income with pretax minus tax.

Use CSV FAIR VALUE, not 75% or exactly 67% of the leader. Export-2 floors are
Brand **3.3**, Experience **4.3**, Frictionless **5.0**, Low Price **3.6**. Current
gaps are **+0.8 / +1.5 / −1.9 / +1.0** in that order. Refresh from later exports.

The $71.422M decision-2 budget is historical. Round 3's allocation ceiling remains
unconfirmed. The known revenue arm is $78,579,215.96; the inflation allowance for
the other arm is missing. A studio scenario ceiling is not approval, ending cash
or inventory funding. The segment focus is a recommendation; no new 16-factor
allocation or budget is automatically adopted.

Market value follows the documented max(DCF, CLV/private-brand-adjusted,
liquidation) mechanism; numerical reproduction is incomplete. Changed-plan equity
value remains null. Unchanged inputs show the reported $255,271,438 reference,
not a revaluation under edited economic assumptions.

## Reproducibility

`round_review.dataset()` loads the latest package. `dataset(1)` preserves the
older analysis for regression tests. Workbook source, header, cells and SHA-256
are retained. Source exports and workbooks are never rewritten. The archived
export-1 model card and reports are historical, not current recommendations.
