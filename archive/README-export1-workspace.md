# Archived export-1 workspace documentation

Historical snapshot. The current workspace is Round 3 planning using export-2 actuals; see `../README.md` and `../ROUND2_REVIEW.md`. Old paths and decision labels below describe the previous convention, not the current source mapping.

Local, dependency-free Python server and browser analysis workspace. No external
AI, paid API, tracking or network data sources. Python 3.10+ and a modern browser.

## Run

```sh
cd /Users/direwolf_kai/wemba/marketing
python3 app.py
```

Open **http://127.0.0.1:8000**. Stop with **Ctrl+C**. If port 8000 is already in
use, open the existing app or run `PORT=8001 python3 app.py`.

## Six pages

- **Executive overview** (`/#overview`): Round 1 actual revenue, earnings, market
  share and cash; Kahn changes; the earnings bridge; strategic trade-offs; and the
  frozen prior-model error audit.
- **Marketing Intelligence** (`/#marketing`): six segments, selectable ranking
  lenses, raw preference comparisons, four-round momentum, product positions,
  competitor revenue shares, equity market value and FAIR VALUE Kahn comparisons.
  It leads with Experience-first / Low Price-second positioning, an interactive
  target-needs bubble plot, observed two-quadrant trajectory and segment revenue
  versus market-consumer growth. Segment 6 is selected initially. Target policy
  is distinct from observed outcomes; no future score point or profit ranking is
  invented. The shareable HTML includes these plots and targeting evidence, not
  decision inputs or the conditional draft.
- **Financial health** (`/#financials`): full comparative statements and
  scorecard, gross/net margins, liquidity, financing, offering economics, net
  income bridge and decision-input versus expense reconciliation.
- **Decision Insights** (between Financial health and Decision studio):
  - `/#insights/brand`: focused, ranked diagnosis of the Brand loss: higher-cost
    depth −1.90 points, lower-cost depth −1.00, and private-brand offsets +0.30.
    Conclusions (left) and step-by-step supporting calculations (right) distinguish
    observed-position reconstruction from input-level causality, including the
    fitted ½ weight, gross-loss denominator and score-level residuals. Columns
    stack on mobile. Slide 14’s quality-to-Brand pathway
    is shown separately; hover, focus or tap underlined numbers for source notes.
    Quality settings are verified current values, not an assumed historical change.
    Planning stays in Decision studio.
  - `/#insights/finance`: reconciled gross-margin mix/rate decomposition,
    effective-markup explanation, balance-sheet cash bridge with proxy labels,
    liquidity/financing break-even thresholds and independent stresses.
  - `/#insights/segments`: team-selected **Experience first / Low Price second**
    strategy, source-checked STP, all six segment roles and raw needs. Segment 6
    is the primary acquisition candidate; Segment 4 is selective secondary;
    existing Segments 2/5 are defended. Experience “top 1” means our strongest
    quadrant, not #1 among retailers. Parity safeguards use the CSV FAIR VALUE
    benchmarks; the conflicting 75% slide rule is audit context only. Crosswalks remain optional diagnostics,
    not official customer utility or causal scores.
- **Decision studio** (`/#decisions`): all sixteen inputs grouped by strategic
  job, local Experience/Low Price policy checks and conditional financial/cash
  diagnostics. Assumptions, factor probes, finite-grid search and historical
  audits are collapsed by default. Search objectives do not encode the team's
  strategy; market-value forecasting remains unavailable. Nothing is adopted.
  Starts at Round 0 submitted inputs. A live top budget shows $1.608M extra
  allocation and remaining capacity against $71.422M as inputs change. Explicit
  recommendation-load buttons connect both pages and calculate the same proposed
  plan in the sandbox; per-factor reference/recommendation values remain visible.
  Predictions require recalculation; budget arithmetic updates immediately.
- **Round 1 decision recommendation** (`/#recommendations`): next Round 1
  submission → Round 2 outcomes, using current Round 1 evidence. All 16 inputs
  have reference/draft settings, reasons, source citations and adoption gates.
  The conditional draft allocates the user-confirmed **$71,422,000** budget:
  $1M extra Experience, $608k extra vendor capability, no service/analytics cuts,
  with both depths held at 25/10: Brand already clears the CSV floor by 0.20.
  The earlier automatic depth-repair draft is superseded. Shrinking the ZEPHARA
  Experience gap and improving Low Price are goals, not forecasts. Full
  Frictionless parity is explicitly deferred in R2; its game risk is retained.
  Depth inventory and financing still require separate cash/credit review.
  `strategy_analysis.py` separates team policy, reported evidence and selected
  test increments. No workbook, model coefficient or optimizer weight changes.

Assortment Lab, Scenario lab and What-if & Year 2 have been removed from active
navigation, scripts and API routes. Kahn and model/source disclosures now live
inside the six focused pages. The old chat/model/positioning pages are not part
of this workspace. Old hash URLs fall back to Executive overview.

Historical backend modules, saved-scenario database and earlier standalone files
are retained for reproducibility, not exposed as active pages. No uploaded
workbook or simulation source was deleted. Earlier docs live in `archive/`.

## Sources and the submitted plan

- Actuals: `materials/round0/finance/`, `materials/round1/finance/`.
- Marketing/Kahn: `materials/round0/marketing/`, `materials/round1/marketing/`.
- Actual submitted plan found at
  **`decision_making/round_0/decision_making_team11_0.xlsx`**, Column B.
  Its worksheet cells and SHA-256 fingerprint are retained in the review payload.
- Industry benchmarks: `decision_making/round_0/industryDecisions-round0.csv` and
  `decision_making/round_1/industryDecisions-round1.csv`. These are observations,
  not verified input bounds or optimization targets.
- **`materials/decision_making_factors.md` is populated**. It confirms markup on
  cost, breadth/inventory, quality/cost, store capex/disposal, partial capitalization
  of online/experience investment, vendor cost/inventory effects, and expensed
  analytics. Numeric response rates and input bounds are still not supplied.
  Its duplicate Private Brand/quality definition is superseded by
  **`MarketValue_Slides.pdf` p12: Private Brand is mix**. Realized sales exposures
  and numeric mix effects are not supplied.
- **`materials/PivotOrPerish_Intro wemba.pdf`** and **`materials/MarketValue_Slides.pdf`**
  clarify STP, two-quadrant strategy/parity, the budget rule, three-route valuation,
  credit/WACC, persistence and investment mechanics. See **`SIMULATION_REVIEW.md`**.

The current workbook differs from the earlier draft: breadth 78/50, depth 25/10,
markups 50%/52%, private-brand shares 44%/70%, quality 6/6, coverage 200,
online $6.5M, service $15M, experience $13M, vendor $27M, analytics $8.314M.
Known input spending is exactly $69.814M. The user confirms this submission
produced the Round 1 results; the workbook itself is not an execution log.
The latest workbook now reads lower-cost depth **25 at Sheet1!B4**, replacing the
earlier read of 50; higher-cost depth is **10 at Sheet1!B8**. The live review
records a fingerprint of the current file instead of silently reusing old values.

Files are loaded locally. Dataset caching is invalidated when source file size
or modification time changes. No simulator is launched and no Excel file is
modified by using Decision studio. Edits are temporary browser-tab state.

## What changed in the engine

`round_review.py` ingests both rounds, imports the actual workbook, reconciles
source scopes and compares the frozen v2 prediction and optimizer alternatives
with observed Round 1 outcomes. See **[ROUND1_REVIEW.md](ROUND1_REVIEW.md)**.

`review_model.py` (`review-4.0`) anchors the conditional sensitivity model at
**Round 1 actuals and the submitted plan**, not the old screenshot assumptions.
`guided_prediction.py` uses only PDF-compatible direct pathways with explicit,
uncalibrated numerical priors; analytics only multiplies online/experience,
vendor has no direct Brand term, and stores change access—not preference.
It does not fit sixteen causal coefficients from one bundle. `decision_economics.py`
adds definition-supported quality/vendor unit-cost responses to **both COGS and
cost-plus selling prices**. Breadth/depth/vendor inventory effects are explicit
scenarios; inventory funding is not immediately charged as COGS. Holding expense
is fixed at zero (MV p14), financing remains a scenario. New stores cost $1.75M;
capitalized investment, depreciation, store openings, disposal cash and closure
write-offs are separate. Analytics is fully expensed; service uses the provisional
observed input ratio. The constant-P/E valuation shortcut is retired: changed-plan
value and market-value optimization are unavailable without DCF/CLV/floor rules.

In Decision studio, blank economic rates mean **unknown**, not zero. Changed
pathways with unknown coefficients are prominently labeled partial diagnostics.
An explicit zero is a user scenario assumption unless documented (holding expense
is a known zero). The 40%/80%
online/experience expense fractions are provisional defaults from Round 1;
the complementary capitalized amounts still consume cash.

`review_optimizer.py` performs an exhaustive finite grid (maximum 20,000 nodes).
It uses the **same current evaluator** as the studio and requires an explicit
budget, maximum incremental cash use, ranges and grid step. All non-spending
factors are locked; unspecified spending ranges or equal min/max lock those
spending factors. All four Kahn floors default to the starting modeled scores.
Unknown affected cost channels block the entire search. There is no automatic
adoption. A verified result is best only on that grid plus an eligible unchanged
incumbent under the supplied scenario—not a continuous/global optimum.

**This is not a calibrated forecast, proven optimum or intrinsic valuation.**
The large v2 misses remain visible. Matching the new baseline is by construction,
not predictive validation. Unspecified economic effects are omitted from partial
diagnostics and block affected optimization. Cash diagnostics omit receivables,
payables, debt flows and other cash movements; they are not ending cash. The next-round budget
uses max(14% previous revenue, inflation-adjusted previous budget). The revenue arm
is $67,469,674.72, but prior budget/inflation are missing. $69.814M is submitted
spend, not a verified ceiling or authorization.
Full equations and limitations: **[MODEL_CARD.md](MODEL_CARD.md)**.

The Brand diagnosis now reconstructs reported Brand within 0.05 points across
all 14 supplied retailer-round rows as half the sum of both depth positions and
both private-brand positions. Getchell’s position changes contribute **−1.00**
lower-cost depth, **−1.90** higher-cost depth, and **+0.30** private-brand positions:
net **−2.60**. This is a same-data empirical scoring reconstruction, not a verified
input-to-score formula or independently validated causal model. The old Brand
model omitted depth; prospective depth changes now display **unquantified Brand
response** and block optimization rather than treating that missing effect as zero.
See `brand_impact.py`, `BRAND_IMPACT.md`, and the Brand subtab.

`brand_holistic.py` connects every workbook cell to definition-supported Brand
mechanisms, actual finance/marketing evidence, financial trade-offs and explicit
counterevidence. It checks overlapping histories rather than counting re-exported
rows as new observations. Regenerate the holistic report with:

```bash
python3 -c "from round_review import dataset; from brand_holistic import write_report; write_report(dataset(), 'BRAND_IMPACT.md')"
```

## Market value, fair value and segment value

- Market Value is observed **equity** value, not cash. The documented rule is
  max(DCF, CLV/private-brand-adjusted, liquidation); P/E is an output, not the rule.
  Unchanged plans display the reported R1 reference; changed-plan value is null.
- **FAIR VALUE** is a moving quadrant benchmark, **not an eighth retailer**.
  Use the CSV FAIR VALUE column for working gaps, recommendations and studio
  checks. Brand is +0.20 above its floor; Frictionless is −1.80 below. Approximate
  two-thirds ratios are not an exact formula; the conflicting 75% slide rule is audit-only.
- **Numerical valuation reproduction is unavailable**. Forecasts, terminal rules,
  credit/WACC and alternative-valuation coefficients are incomplete; the slides
  conflict about how strategy sets T. No missing formula is invented.
- Round 1 has **no segment CLV file**. Company CLV is not allocated to segments
  and old segment CLV is not presented as current. Segment revenue sums to
  $481,926,247, $1 below financial revenue; the difference is retained.
- Preferences are relative measures; Intro p7 identifies size as segment consumers,
  not company buyers. Penetration remains unverified, and
  company segment revenue is not whole-market demand or penetration.

## Share only Marketing Intelligence

Click **Share Marketing Intelligence HTML**, or run:

```sh
python3 marketing_report.py
```

Send **`reports/getchells-marketing-intelligence.html`** itself. It is an
interactive, vivid single-file snapshot that opens offline in a full browser.
It has no decision controls or other app pages, no external resources, and a
content-security policy that disallows network connections. Reopening resets
segment selections. Regenerate after source changes; downloaded files do not
auto-update. The live `/marketing-report` download is built from current data.

## Tests

```sh
python3 -m unittest discover -s tests -v
python3 tests/browser_smoke.py
```

The browser smoke test requires Google Chrome on macOS, uses a temporary local
server/profile, checks all six pages and three Insights subtabs (including
keyboard navigation, deep links and mobile layouts), edits/resets the studio,
and opens the shared HTML with network disabled. Legacy backend regression tests
remain to keep the frozen v2 audit reproducible. `tests/legacy_browser_smoke.py`
is the archived ten-page workflow and reusable CDP helper, not the current suite.

## Current API

- `GET /api/data`: both rounds, actual submitted plan/provenance, segment and
  competitor data, financial ratios, frozen v2 audit/optimizer alternatives,
  Round-1-anchored baseline, all sixteen factor probes and reconciled Decision
  Insights diagnostics (`decision_insights.py`). See `DECISION_INSIGHTS.md`.
- `POST /api/impact`: `{decisions, assumptions?, economics?}`; all sixteen finite, bounded
  numeric fields required. Returns `{result, probes}` without persistence or
  simulator execution. All probes use the same requested score and economic assumptions.
- `POST /api/optimize`: `{decisions, assumptions?, economics?, ranges, step, budget,
  max_cash_use, objective?, score_floors?}`. Objective: `profit`, `market_value`,
  or `positioning`. Response status: `verified_grid`, `blocked` (missing pathways),
  or `infeasible`. `market_value` is always blocked pending the exact valuation
  rules. Profit/weighted positioning are one-period diagnostic objectives only.
- `GET /marketing-report`: downloadable current standalone marketing HTML.

Removed legacy APIs return 404, including assortment, scenarios, projections,
chat and optimizer adoption. The old v2 heuristic is retained only for the explicit
retrospective comparison. The server binds to localhost and is not hardened for
public deployment; do not expose it to the internet as-is.
