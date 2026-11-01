# Getchell’s Decision Lab · Final eight-round review

The dashboard uses **actual submitted decisions 0–8** and financial/marketing
histories through **`materials/round8`**. R1–R8 are the eight scored rounds;
R0 is the baseline (nine financial snapshots). The analysis is a final
retrospective, not a new-round recommendation. No workbook is edited and no
next-round budget is inferred.
Missing standalone historical finance files (including Round 3) are recovered
from explicitly labeled Round-N columns in later exports, without looking beyond
the selected dataset’s observed period.

## Run

```sh
python3 app.py
```

Open **http://127.0.0.1:8000**. Restart a running server after this update, then
refresh. Python 3.10+ and a modern browser; no paid services required.

## Final pages and models

- **Executive overview:** marketing-led verdict, final objectives, S3+S5 delivery
  and financial recovery. Experience/Brand finish #1; Frictionless misses parity.
  Includes an eight-round objective-delivery heatmap, target revenue/CLV mix
  trends, starting-weight versus growth-contribution bars and separate actual
  market-value, net-income, debt and WACC charts (no dual axes or fitted forecasts).
- **STP decision** (`/#stp`): between the overview and segmentation outcome audit.
  Explains S3 → S5 → supporting S2/S4/S6 using R0 need intensities, population,
  revenue and aggregate CLV. Adds a fit/population bubble map, population versus
  company revenue/CLV mix chart, seven-retailer positioning map and full needs
  heatmap. The initial rationale is kept separate from R8
  outcomes; the stated order is not claimed to be a proven profit optimum.
- **Market value:** final equation, method and full-sample fit first; extra
  diagnostics are optional. Log-linear ridge on EBIT, WACC and book leverage,
  λ=0.01: MAPE **2.44%**, log-value R² **0.9987**.
- **WACC impact:** updated financing equation, actual/fitted/errors and grouped
  decision pathways. Ridge λ=0.01: MAE **0.063 pp**, R² **0.9936**.
- **Score models:** Experience **0.030 MAE / 0.996 R²**, Frictionless
  **0.046 / 0.976**, Brand **0.062 / 0.990**, Low Price **0.038 / 0.669**.
  Low Price is fitted as a peer-relative deviation; capability models include
  bounded service/online/experience carryover. The service carryover is a
  full-sample persistence assumption; the earlier-only audit excluded it and
  preferred persistence. Actual-versus-fitted scatters are shown for every
  quadrant.
- **Customer segmentation:** original S3+S5 strategy evaluated with revenue,
  aggregate CLV, mix and late recovery. Targets finish at **$235.31M revenue**,
  **32.0%** of company revenue, down **3.21 pp** of mix from R0. The page adds a
  priority-ordered audit (S3 → S5 → supporting S2/S4/S6), mix-change trajectories,
  portfolio revenue/CLV contributions, per-round growth by execution window and
  submitted spending versus delivered-capability plots. Needs and population are
  secondary evidence. S5 accounts for **85.7%** of target mix loss; S2 defense is
  distinguished from S4/S6 mix gains. These are descriptive, not segment ROI.

Full-sample fits are descriptive, not causal returns or forecasts. Financial
models use R0–R8; score models use R1–R8. See `ROUND8_REVIEW.md` for the final
conclusions and `MODEL_CARD.md` for equations and limitations.

## Source naming and timeline

- Final submission: `decision_making/round_8/decision_making_team11_round8.xlsx`, Column B.
- All submitted workbooks are read-only inputs; no new allocation is generated.
- User-supplied chronology: decisions and results through Round 8.
  Original export row/column labels are retained, not shifted.
- Current marketing and finance: `materials/round8/{marketing,finance}`.
- Latest industry aggregate is **export 8**, in
  `decision_making/round_8/industryDecisions-round8.csv`. Historical datasets exclude
  industry sources from future submission folders.
- Current segment CLV is reported in `marketCLV-round8.csv`.
- The R8 unit-share CSV is absent. Final unit share comes explicitly from the
  R8 scorecard, not stale R6 offering shares.

## Historical R6 page guide (reproduce with `dataset(6)`)

1. **Executive overview** — all four Kahn trajectories, with each round’s exported
   fair value as zero baseline, peer leadership/top-two thresholds, and finance
   trends. Goals: Experience #1, Brand top two, Low Price/Frictionless at fair value.
2. **Marketing Intelligence** — new Experience-leadership / competitive-Brand
   strategy, segment size/CLV/preference decision, strategic trajectory,
   competitors and complete source tables. **Segment 3 is the primary target**,
   chosen for its Brand/Experience fit; **Segment 5 is a conditional secondary**
   gated on Frictionless parity; Segment 4 is a selective reserve; existing
   Segments 2/6 are defended. Low Price and Frictionless are fair-value
   safeguards.
3. **Customer segmentation analysis** (`/#segmentation`) replaces the current
   decision/debate page with measured outcomes across all six segments: revenue,
   CLV, mix, population, needs drift, investment/capability and volume-share trends.
   No segment-specific causal ROI is invented.
4. **Market value analysis** (`/#marketvalue`) fits Brand and Low Price from
   the six lagged decision→rating transitions, and fits Experience and
   Frictionless with position diagnostics: relative spending → reported
   position → score reconstruction. Frictionless has a separate mechanism and
   timing audit, earlier-only checks and a persistence-preferred warning.
   It then fits reported market value with actual,
   fitted and error tables. Each two-stage model shows both position equations,
   the scores they sum to, an R6 competitor comparison and actual/fitted/error
   checks. Each quadrant shows its equation in decision units, a right-hand
   vocabulary mapping every model term to the actual workbook parameters, and
   its top contributors. It also keeps the reported-position reconstruction
   check across 49 retailer-periods.
5. **WACC impact analysis** (`/#wacc`) traces all 16 decision inputs through
   margins, inventory, cash, credit and financing mix, with documented pathways,
   observed associations and an explicitly exploratory WACC equation.
6. **Financial health** — current statements, ratios, financing and cash proxies.
7. **Decision Insights** — latest Brand/strategy direction, finance and STP.
   Brand improved; the old Brand-loss narrative is not relabeled as current.
8. **Decision studio** — starts at **all 16 actual decision-6 values**, not the blank
   Round 7 workbook. Budget arithmetic defaults to the confirmed ceiling; local
   model sensitivities remain uncalibrated. Reset restores the actual submission.
9. **Round 7 decision making page** — current strategy goals, all 16 actual
   submitted values, funding requirements and release gates. No previous analyst
   recommendation is presented as the submitted plan or a new allocation.

## Historical R6 budget and model notes

These notes describe the preserved R6 snapshot, not the final models above.

**WACC impact analysis** (`/#wacc`, download `/wacc-report`) links all 16 inputs to
documented financing pathways, reports seven-level/six-change/five-lag-pair
associations and includes a hypothetical financing-weight calculator. Its
selected equation is WACC (%) = 11.0213 − 3.7763 × market debt weight
+ 4.8951 × ln(EBIT ÷ market value) + 1.9962 × ln(EBIT in $M), with ridge λ=0.03
chosen by a hide-one-round grid search. Fitted / hide-one-round / R5–R6
earlier-period MAE is **0.06 / 0.11 / 0.28 pp**, versus 0.23 / 0.39 / 0.54 pp
for the previous two-feature form and 0.65 pp for previous-round persistence.
A 377-subset search scored worse under nested selection (0.51 pp), and adding a
fourth feature did not improve it (0.12 pp). The three-feature model is the best
validated specification in the tested space, not a global optimum. EBIT and
market value are jointly determined, so this remains an exploratory association.
Six transitions cannot identify 16 partial effects.

Decision-6 strategic spending totals **$81,549,510**. Round 7's confirmed
simulation ceiling is **$83,151,028**; it is not replaced by a slide revenue
formula. Inventory, store capital and financing require separate cash/credit checks.

Fair value uses each round’s **CSV FAIR VALUE** values, not the conflicting 75%
slide formula or an exact two-thirds ratio. The market-value page now reports:

- **Kahn fits:** decisions at R0–R5 explain ratings at R1–R6 for Brand and Low
  Price. Experience retains its older lagged two-stage association. Frictionless
  now has a separate source-aligned conditional diagnostic and timing sensitivity.
  The workbook has 16 decision columns, but private and national quality are
  identical in every round, so there are 15 distinct input series. Fourteen
  enter at least one fitted score equation; retail coverage is shown but is not
  a documented component of these ratings. All fitted equations use fixed ridge
  λ=0.1. Fitted / hide-one-transition / persistence
  MAE is Brand **0.05 / 0.28 / 0.68**, Experience **0.07 / 0.14 / 0.23**,
  Low Price **0.02 / 0.15 / 0.10**. Low
  Price is nearly flat, so persistence is the more accurate description there.
  The older Experience service/analytics association is not verified mechanics.
- **Frictionless audit:** `frictionless_analysis.py` removes standalone analytics
  from service and excludes service carryover (Market Value slides p13).
  Online uses prior position, relative online spend and online × analytics;
  nonnegative slopes and carryover in [0,1] are explicit assumptions. Positions
  are clipped to [0,10]. Same-round expense alignment supports examining
  same-round spending, but does not prove score timing; both alignments are shown.
  Current diagnostic fitted / hide-one MAE is **0.089 / 0.197**. Earlier-only
  R4–R6 MAE is **0.214**, versus **0.067** persistence; the lagged sensitivity
  scores **0.290**. The superseded model's earlier-only MAE is **0.158** despite
  its attractive 0.114 hide-one MAE. Persistence is preferred. Analytics strength,
  score timing and individual rivals' spending responses are not identified;
  do not optimize Round 7 with these coefficients. Same-round checks condition
  on observed inputs, not inputs forecast before the round. Specification review
  used this history, so even the earlier-only checks are retrospective diagnostics.
- **Market value:** ln(Market value) = −6.7419 + 1.6120 × ln(EBIT) − 0.2364 ×
  WACC − 0.5570 × book debt weight, with fixed ridge λ=0.01. Fitted /
  hide-one-period / R5–R6 MAPE is **1.9% / 7.1% / 8.0%**, versus **36.5%** for
  previous-period persistence. Book debt weight is used instead of market debt
  weight because the latter contains reported market value in its denominator.
  A service-intensity specification has lower raw error, but it is a decision
  proxy; the finance specification is retained for interpretability.

Neither fit is a causal response, frozen simulator forecast or near-optimal
decision engine. Leave-one-out is retrospective; the R5–R6 estimate trains on
earlier periods only but uses observed evaluation-period inputs. No forecast
confidence interval is invented.

## Implementation and history

- `round_review.dataset()` selects the latest observed export; `dataset(1)` and
  `dataset(2)` retain historical analyses for regression tests.
- `current_review.py` imports submissions/exports and records period provenance.
- `longitudinal_analysis.py` constructs observed history, component checks,
  segment outcomes and validation-tested empirical association models.
- `market_value_analysis.py` builds the lagged Kahn fits and position models, the non-circular
  market-value fit and their validation outputs.
- `final_models.py` fits the completed-simulation models. `final_review.py`
  reconciles the original strategy with segment and financial outcomes.
- `web/final_analysis.js` renders the four concise final pages, while older
  datasets retain their historical views.
- `web/history_analysis.js` renders the three new analysis views.
- `web/current.js` renders the current workspace; `web/review.js` retains shared
  utilities, API handlers and the historical renderer.
- `review_model.py` / `decision_economics.py` require complete current financial
  exports. No previous-period financials are substituted into a new-period forecast.
- `MODEL_CARD.md` gives current limits; `ROUND8_REVIEW.md` summarizes final
  outcomes. Earlier review documents are historical snapshots.

## Offline Marketing Intelligence

Download from the page, or regenerate:

```sh
python3 marketing_report.py
```

Share `reports/getchells-final-report.html` for the one-file combined review
(executive overview, STP decision, customer segmentation, market value, WACC and second-chance lessons), or download
it from `/final-report`. All offline files work without a server, external assets
or network calls; older downloads do not update automatically. Standalone pages
are also available as `reports/getchells-customer-segmentation-analysis.html`,
`reports/getchells-market-value-analysis.html` and
`reports/getchells-wacc-impact-analysis.html`, or via
`/customer-segmentation-analysis`, `/market-value-report` and `/wacc-report`. The
old segmentation report URL/file remains a compatibility alias, not a second
current decision page.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/analysis_browser_smoke.py
```

Browser checks require Google Chrome on macOS: all current pages, timeline,
actuals, charts, mobile/deep links, analysis controls, offline navigation and an
unchanged submitted workbooks. Historical backend fixtures select explicit periods.
`tests/round3_browser_smoke.py` preserves the prior workspace browser workflow.
