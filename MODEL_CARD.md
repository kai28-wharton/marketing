# Review model 5.0 · current-export conditional scenarios

## Final R1–R8 retrospective · final-2.1

Final inputs are submissions 0–8 and `materials/round8`. Eight scored rounds plus
R0 produce nine financial snapshots. Score responses use R1–R8, not an invented
prior state for R0. Primary presentation: final equation, method and full-sample fit.

- **ln(MV in $) = −6.4717 + 1.5896 ln(EBIT in $) − 0.2275 WACC (%)
  − 0.4949 book debt weight**. Ridge λ=0.01; MAPE **2.44%**, log-value R²
  **0.9987**, dollar RMSE **$14.55M**. Fixed-specification hide-one MAPE
  **7.46%** is secondary. No market-value denominator is a predictor.
- **WACC (%) = 10.9222 − 3.7516 market debt weight
  + 4.8922 ln(EBIT/MV) + 2.0167 ln(EBIT in $M)**. Ridge λ=0.01;
  MAE **0.0628 pp**, R² **0.9936**, hide-one MAE **0.0986 pp**. These
  financing predictors are jointly determined, not causal decision effects.
  No old subset-search counts or search errors validate this refit.
- Score models use ridge λ=0.1. Service, online and shopping-experience positions
  each use prior position plus relative spending; carryover is bounded [0,1] and
  investment slopes are nonnegative. Analytics interacts with online and
  experience, never service alone. Outputs are clipped to [0,10]. Scores sum
  fitted positions, not observed positions. Brand uses shared quality, assortment
  and private mix. Low Price is modeled as the six-peer average plus a
  peer-relative deviation driven by the prior gap and lower/higher-cost markups
  relative to the same-round industry averages. Fitted score
  MAEs: **0.062 Brand / 0.030 Experience / 0.038 Low Price / 0.046 Frictionless**;
  R²: **0.990 / 0.996 / 0.669 / 0.976**. Low Price's 0.2-point observed range
  makes its R² unstable even though absolute error is small. Bounded service
  carryover is included in this full-sample fit; the earlier-only Frictionless
  audit excluded it and preferred persistence, so the two results answer
  different questions. Actual-versus-fitted scatters are shown for all four
  quadrants, alongside the value and WACC plots.

`final_models.py` uses fixed penalties, training-sample scaling, raw-unit equations
and fresh metrics. Fifteen inputs were screened, but eight scores cannot identify
fifteen independent effects; the full-input interpolation is not a final mechanism.
Comparisons and hide-one checks are optional, not external forecast validation.
Score timing, bounded capabilities and finance proxies are not verified simulator code.

`final_review.py` separates targeting from execution: Experience/Brand #1,
Frictionless below fair value, S3+S5 revenue mix down 3.21 pp despite growth.
Segment revenue and aggregate CLV are not profit, per-buyer CLV, acquisition ROI
or penetration. R3 is a descriptive checkpoint, not a treatment date. Missing R8
unit-share CSV is replaced explicitly by the reported scorecard. No workbook is
changed and no Round 9 budget is inferred.

## Historical Round 7 planning analysis · reproduce with `dataset(6)`

Observed data ends at Round 6. The confirmed Round 7 ceiling is **$83,151,028**,
not a recalculated slide budget. Fair value uses the exported per-round floors.
The decision workbook remains untouched. Cumulative financial exports recover
missing historical files using original labeled columns and source provenance.

`market_value_analysis.py` / `longitudinal_analysis.py` / `web/history_analysis.js` add:

- All four Kahn gap-to-fair-value histories and actual competitor ranks. Experience
  targets #1; Brand top two; Low Price and Frictionless meet reported fair value.
- Six-segment outcome, preference, CLV and population trends. Company spending
  and capability trends are context, not measured segment ROI.
- Experience ≈ shopping position + service position and Frictionless ≈ online
  position + service position, checked on **49 retailer-periods**, maximum
  absolute reconstruction error **0.1**. These are rounded output reconstructions,
  not verified simulator code or fitted input-to-score responses.
- Two direct Kahn fits (Brand and Low Price) and two two-stage position models
  (Experience and Frictionless). Decisions at R0–R5 explain ratings at R1–R6 for
  Brand and Low Price. Experience retains its older lagged position fit;
  Frictionless has a separate audited conditional diagnostic and timing sensitivity
  described below. Scores are reconstructed from reported positions, not verified
  simulator code. The workbook has 16 decision columns, but private and national
  quality are identical in every round, so there are 15 distinct input series.
  Fourteen enter at least one fitted score equation; retail coverage is retained
  in the matrix but is not a documented component of these ratings. All fitted
  equations use a fixed ridge penalty λ=0.1; scaling is recomputed in
  each fold. They use documented driver composites and position responses rather
  than 15 free coefficients, because six transitions cannot identify 15 separate
  effects. Brand uses Vendor Management and Customer Analytics separately; its
  assortment term remains the average of the four breadth/depth settings.
- Experience is **customer-service position + shopping-experience position**;
  Frictionless is **online-investment position + customer-service position**.
  Both reconstructions hold across **49 retailer-periods** within **0.1** points.
  Spending is expressed relative to the exported industry average. Its exact
  membership is not independently verified. The relative-spend ratio is the industry
  benchmark; nominal dollars are not treated as capability.
- Customer Analytics is a documented multiplier of online and shopping-experience
  investment (Market Value slides p13), not standalone demand. Frictionless now
  uses an online × analytics interaction and no analytics term in service. The
  older Experience service/analytics equation remains an exploratory association,
  not a documented mechanism. The export has no separate analytics position.
- The page reports fitted equations or two-stage position equations in decision
  units, a right-hand vocabulary mapping model terms to actual workbook
  parameters, and R6 competitor comparisons. Frictionless shows all six named
  rivals, explicit mechanism constraints, both timing assumptions and earlier-only
  checks. Its coefficient terms are not ranked as investment importance.
- A non-circular log-market-value model: **ln(Market value) = −6.7419 +
  1.6120 × ln(EBIT) − 0.2364 × WACC − 0.5570 × book debt weight**. Book debt
  weight is debt / (debt + book equity); market debt weight is excluded because
  it mechanically contains reported market value in its denominator.
- Seven company-periods for the market-value fit, fixed ridge λ=0.01,
  unpenalized intercept and training-fold standardization. Actual/fitted/error,
  hide-one-period and R5–R6 earlier-period errors are reported. Evaluation uses
  observed same-period EBIT, WACC and book leverage; it is not a forecast of
  future financials/scores. No pre-outcome backtest or confidence interval is
  claimed.

`wacc_analysis.py` / the `/#wacc` page add a separate financing view. It maps all
16 inputs to documented pathways through margins, inventory, cash, credit ratios
and financing weights, and reports levels/change/next-period associations with
leave-one-transition-out ranges. These are descriptive: six transitions cannot
identify 16 partial effects, and several inputs move together.

The selected exploratory WACC equation is:

**WACC (%) = 11.0213 − 3.7763 × market debt weight + 4.8951 × ln(EBIT ÷ market value) + 1.9962 × ln(EBIT in $M)**

where market debt weight is debt / (debt + reported equity market value). Ridge
λ=0.03 is selected from a hide-one-round grid; scaling is refitted inside each
validation fold. The equation is centred on R6 in the report so it can be read as
deviations from observed values.

Market leverage captures financing mix. The earnings-yield term captures
valuation per dollar of operating profit. The EBIT-scale term distinguishes “more
earnings at a given valuation” from “a higher valuation at given earnings.” The
signs are locally interpretable but remain reduced-form associations, not a
structural cost-of-capital formula.

Mean absolute error is **0.06 pp fitted, 0.11 pp hide-one-round, 0.28 pp
earlier-period-only (R5–R6)**, versus **0.65 pp** for previous-round WACC
persistence. The previous two-feature equation had **0.23 / 0.39 / 0.54 pp**; the
earlier book-weight/coverage form had **0.88 / 1.27 / 2.45 pp** on the same
two-period test.

The specification search tested **377 feature combinations × 14 ridge penalties**.
The selected three-feature model scores **0.11 pp** under nested hide-one-round
selection. Letting the search choose a different feature set inside every fold
scores **0.51 pp**, and the best four-feature extension scores **0.12 pp**. So the
three-feature model is the best validated specification in the tested space, not
a proof of a global optimum. EBIT and market value are jointly determined with
WACC, so the coefficients are not causal returns or a reliable Round 7 forecast.
The page also provides hypothetical WACC reweighting arithmetic: it changes only
user-supplied rates/tax and a weights proxy, never actual simulator weights.

Kahn fit results (fitted / hide-one-transition / persistence MAE, score points):
Brand **0.05 / 0.28 / 0.68**, Experience two-stage **0.07 / 0.14 / 0.23**,
Low Price **0.02 / 0.15 / 0.10**. These are retrospective associations.

### Frictionless mechanism audit (supersedes the previous fit)

The former lagged model's **0.057 fitted / 0.114 hide-one MAE** did not validate
its mechanism. It incorrectly assigned standalone analytics to service and fitted
service carryover 0.728 despite documented little persistence. Its earlier-only
R4–R6 MAE is **0.158**, versus **0.067** for prior-score persistence.

`frictionless_analysis.py` fits service only from relative service spending.
Online has prior online position, relative online spend and the interaction
relative online × relative analytics. Slopes are constrained nonnegative and
online carryover to [0,1], using exact active-set ridge with training-fold scaling,
fixed λ=0.1 and a free intercept. These bounds are assumptions, not discovered
positive effects. Each output is clipped to [0,10]; no standalone analytics term
or service carryover is permitted. The sum reconstructs Frictionless within rounding.

Every workbook's online spend matches that same round's online expense at 40%.
This is accounting alignment, not proof of position timing. The diagnostic uses
same-round inputs with prior online position; the lagged version is also reported.
Same-round fitted / hide-one MAE is **0.089 / 0.197**. Earlier-only R4–R6 MAE
is **0.214**, lagged sensitivity **0.290**, persistence **0.067** on those same
three periods. **Persistence is preferred; this is not decision-ready.**

Earlier-only checks exclude all later outcomes from training, but same-round
spending and benchmarks are observed inputs, not pre-round forecasts. All
specifications were reviewed using this history. Only six scored periods and three
earlier-only checks exist. Analytics amplification and timing remain unidentified;
no causal effects, forecast interval, rival-specific reaction, or Round 7 optimum
are claimed. The old pooled 18-position check imposes common slopes across unlike
capabilities and is not validation of Frictionless. Experience remains separately
labeled as the older unaudited association.

Market-value errors: **1.9% fitted / 7.1% hide-one-period / 8.0% R5–R6**, versus
**36.5%** for previous-period persistence. The finance-only comparison is
**5.0% / 9.3% / 9.7%**; finance plus strategy deficit is **4.8% / 11.4% /
10.3%**; finance plus unit share is **2.5% / 6.9% / 10.0%**; finance plus service
intensity is **1.4% / 4.0% / 4.2%**. The service-intensity specification has the
lowest raw errors, but it is a decision proxy. The selected finance specification
is retained because it is interpretable, uses only EBIT, the reported WACC and
book leverage, and does not include a market-value-derived ratio. Trends,
decisions, competitors and persistence still confound coefficients. These models
cannot identify causal score premiums or optimize all 16 decision inputs. The
existing studio's local priors remain separate, conditional and uncalibrated.

The reported market value remains the outcome of max(DCF, CLV/private-brand,
liquidation); raw CLV is not itself the simulator's adjusted valuation floor.

## Archived Round 4 workspace notes below

The following describes the earlier evidence package and historical scenario
model, not the current data availability, budget or Round 7 recommendations.

### Historical evidence and chronology

- Latest submitted decision: **3**, from `decision_making/round_3/decision_making_team11_round3.xlsx`.
- Latest marketing outcome package: **`materials/round3/marketing`**.
- Latest comparison: export **2 → 3**; current planning period: **4**.
- Previous submitted workbook: `decision_making/round_2/decision_making_team11_round2.xlsx`.
- Round 3 finance is missing. Financial context remains explicitly Round 2;
  current profit, cash, WACC and market value are unknown. No historical finance
  is copied into the Round 3 record. Predictions and optimization are blocked.
- Segment CLV is now reported, including backfilled historical rows. Segment
  contribution, affinity and measured segment-specific Kahn scores remain absent.
- Latest industry aggregate available is export 3. Historical datasets exclude
  later submission folders and future export rows.

## Baseline and model scope

All sixteen studio inputs start at actual submitted decision-3 values. Scores
come from export 3; current financial outcomes are unavailable. Manual budget
arithmetic and editing remain available. No earlier suggested plan substitutes
for the submission. With complete financial exports, unchanged inputs reproduce
observed actuals by construction—not a calibrated next-round forecast.

The same uncalibrated PDF-compatible local priors are retained: quality → Brand;
experience/service and analytics interaction → Experience; online/service and
analytics interaction → Frictionless; vendor/markup → Low Price. These pathways
are qualitative mechanisms, not learned simulator coefficients. No coefficients
are fitted from simultaneous decision bundles or competitor outcomes.

Depth, breadth, private mix and store response channels remain unestimated. A
changed assortment/mix scenario labels Brand **Partial**, exposes the modeled
component, and leaves the full forecast null. The component is not a lower bound.
Such missing channels continue to block optimization. No fresh pre-outcome frozen
forecast was supplied for the actual decision 3: stress intervals are null, not fabricated.

## Strategy and segment scope

Team intent is **Experience leadership + very competitive Brand**, with Low Price
and Frictionless held at reported CSV fair value. Experience leadership means
**#1 among actual retailers**, not merely Getchell’s strongest quadrant. Current
scores are Experience 5.3 (#2, ZEPHARA 6.7), Brand 4.9 (tied #1 with BESTCO), Low Price
4.6 (#7, floor 3.6) and Frictionless 2.7 (#5, floor 5.1). The −2.4 Frictionless
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

The interactive debate lab (`web/segmentation_lab.js`) adds reversible group
selection (including removal of S3 in a counterfactual), any-two-segment raw or
normalized needs, and explicit company-wide rival benchmarks. Brand/Experience
needs concentration is their two raw weights divided by all eight raw weights;
it is not measured utility or a customer percentage. Group totals describe
existing business represented, not expected gains/losses from targeting.

Financial alternatives calculate period incremental contribution as observed
segment revenue × assumed incremental lift × assumed contribution margin minus
incremental spending. Defaults ($1M, 20%, 5%) are illustrative, not estimated
segment economics or recommendations. Zero margin with positive spending has
no finite break-even; zero spending has no defined spending ROI. Blank or
out-of-range inputs suppress numerical comparison. Alternatives are independent;
no additive portfolio return, CLV change, tax, financing, inventory/capex,
cannibalization or simulator response is estimated. No budget is approved.

The HTML download preserves the current group, lens, comparison, assumptions
and escaped team note in an inert JSON payload. Its controls run offline and
can re-export a new snapshot, without decision inputs or a server connection.
`/customer-segmentation-report` serves a default snapshot opening directly on
segmentation; `/marketing-report` retains its original landing page.

`segment_decision.py` supplies the new `/#segmentation` page. Source measures
stay separate: population, population growth, company segment revenue/growth,
aggregate CLV/growth and all eight raw needs. Transparent single-metric lenses
replace a fabricated composite utility or profit score. The Experience lens
orders the debated segments 5 > 6 > 4 > 2; aggregate CLV orders 2 > 6 > 5 > 4.
This distinguishes growth fit from existing-equity defense. Segment 6 receives
an explicit challenger case rather than being ruled out merely for low Brand.

Financial constraints include historical Round 2 cash, income, interest cover,
inventory and WACC. Round 4 budget approval and current financing capacity are
unconfirmed. Named rivals are slide profiles, not observed
segment ownership; current company Kahn scores and product positions permit
relative-capability comparisons, not competitor-by-segment share estimates.
Group selection adds observed totals and a qualitative one-liner only; it does
not edit policy, decisions or the spending draft. Segment 4 population growth
is 5.1%, below S6 (5.5%) and S1 (6.5%), correcting the earlier fastest-growth
wording. The page is also available inside the offline Marketing Intelligence
HTML, without exporting editable decision inputs.

### MarketValue-grounded strategy verdict

The choice of Experience + Brand is justified against the MarketValue deck as a
documented sweet-spot shape (two differentiators, parity on the other two, MV p8),
a fit match (Segment 3 is the only segment whose top-two raw needs are exactly
Shopping Experience and Brand), capital efficiency (mostly expensed levers,
MV pp12–13) and the CLV/brand-adjusted valuation route (MV pp6, 11). Two binding
conditions are recorded: defend competitive Brand, restore Experience leadership
and recover Frictionless parity. Low Price + Experience is not the chosen policy
(immediate, non-persistent markup cuts; BESTCO is a named rival, not a measured
segment owner); Frictionless + Experience is not
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

Use CSV FAIR VALUE, not 75% or exactly 67% of the leader. Export-3 floors are
Brand **3.3**, Experience **4.4**, Frictionless **5.1**, Low Price **3.6**. Current
gaps are **+1.6 / +0.9 / −2.4 / +1.0** in that order. Refresh from later exports.

Actual decision-3 strategic spend totals $74,631,166. That matches the historical
Round 3 ceiling, not a new Round 4 approval. The computable Round 4 revenue arm is
$79,174,036.20 from marketing offering revenue; the inflation-adjusted arm and
actual next ceiling remain unknown. A studio scenario ceiling is not approval,
ending cash or inventory funding. `round3_planning.py` remains a historical
recommendation accessible through `dataset(2)`, not the actual Round 3 submission
or a new Round 4 allocation.

Market value follows the documented max(DCF, CLV/private-brand-adjusted,
liquidation) mechanism; numerical reproduction is incomplete. Changed-plan equity
value remains null. Round 3 reported market value is unavailable. Historical
export-2 scenarios may show the reported $255,271,438 reference, not a current
revaluation under edited economic assumptions.

## Reproducibility

`round_review.dataset()` loads the latest package. `dataset(1)` preserves the
older analysis for regression tests. Workbook source, header, cells and SHA-256
are retained. Source exports and workbooks are never rewritten. The archived
export-1 model card and reports are historical, not current recommendations.
