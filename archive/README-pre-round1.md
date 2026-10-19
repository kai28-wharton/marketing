# Getchell’s Decision Lab (archived pre-Round-1 documentation)

A local frontend and Python backend for financial analysis, Kahn positioning, decision planning, scenario comparison and constrained investment allocation.

## Run

Requires Python 3.9+; no packages, API keys, subscriptions or paid model calls are required by this application.

```sh
python3 app.py
```

Open **http://127.0.0.1:8000**. To select a different port: `PORT=8001 python3 app.py`.

The presentation-only vivid theme lives in `web/vivid.css`: dark navy navigation,
violet/blue accents, colorful metric cards and brighter segment/preference chart
palettes. Positive/negative changes retain consistent green/red sign semantics.
New offline Assortment Lab bundles embed the same theme; no numerical model or
decision inputs are changed by styling.

## Pages

- **Executive overview:** financial indicators, strategic priorities and positioning.
- **Marketing Intelligence:** all nine marketing source tables, six preference profiles and three-round histories, competitor offering/channel mixes, reported pricing and product positions, denominator-safe shares and reconciliation checks.
- **Decision studio:** all 16 screenshot decisions, live industry benchmarks and five-field spending budget.
- **Assortment Lab:** textbook breadth/depth explanations and four-only experiments around a locked team plan. Imports the team's XLSX by default; the remaining 12 inputs and model assumptions are read-only.
- **Kahn positioning:** correct product/experience × increase-pleasure/reduce-pain matrix, competitors, three-round history.
- **Financial health:** statements, ratios, operating scorecard and industry decision benchmarks.
- **Scenario lab:** save/load alternatives, compare assumptions and run a repeatable constrained allocation search. Locks are supported. Candidates require explicit adoption.
- **What-if & Year 2:** separate editable drafts, the $68M controlled-service/convenience example, a conditional brand-quality example, and side-by-side Round-0/Year-1/Year-2 financial and Kahn projections. Export the full projection or explicitly copy its decisions to the studio.
- **Ask the assistant:** a local, rule-based chatbot for application guidance, financial facts, Kahn comparisons, benchmarks, model explanations and simple one-factor what-if questions. Responses cite their sources and never change your working plan.
- **Model & sources:** editable sensitivity assumptions, complete formulas, provenance and missing-data warnings.

Decision briefs download as JSON, including all inputs, assumptions, sources and caveats. Scenarios are stored in `data/scenarios.sqlite3`. The working plan is in browser memory until saved; loading a page afresh restores the reference plan. Saved scenarios are shared by browser sessions on this machine, not a multi-user collaboration service.

## Important limitations

### Marketing evidence and customer segmentation

The Marketing Intelligence decision dashboard now includes five linked SVG
charts (no charting packages or external services):

1. **Revenue–CLV portfolio:** company revenue mix vs aggregate CLV mix; bubble
   area represents reported size. The diagonal is equal mix, not a target or ROI.
2. **Decision-lens ranking:** choose company revenue, aggregate CLV, reported
   size, latest revenue growth, or one of eight normalized preference emphases.
   Rankings are descriptive, not budget recommendations.
3. **Breadth/depth needs map:** compares normalized shares of each segment's
   preference sum, not assortment settings or population percentages.
4. **Selected-segment indexed history:** reported size, company segment revenue
   and segment CLV start at 100 in the first common source round. Three source
   points are shown; there is no forecast extension or inferred penetration.
5. **Preference composition:** explicitly normalized eight-attribute profiles;
   the original raw weights remain in the tables. Normalization can change ranks.

Click chart points/bars, use the segment buttons, or select a segment to update
every chart and the existing source drill-down together. SVG controls support
Enter/Space, and charts retain labels, accessible descriptions and source tables.
Small screens can scroll charts horizontally. A selected-segment decision brief
shows its needs, revenue/CLV mix gap, observed growth, a hypothesis to investigate
and the remaining evidence requirements. An expandable comparison links its main
need to reported product positions without equating those positions with Kahn.

Exported marketing JSON includes the selected segment/lens, rankings, indexed
series and mix gap alongside all nine raw tables. These chart selections do not
alter team decisions, model assumptions or financial/Kahn forecasts.
Implementation: `web/marketing_charts.js` and `web/marketing_charts.css`.

Open `/#marketing`. `marketing.py` reads the nine `materials/marketing/*-round0.csv`
files, matching segments by column **name** (some files reverse their order).
The original labels/values are retained in expandable raw tables and JSON export.
The executive overview, Decision studio and Kahn positioning pages now include
segment-informed context; no customer profile is inferred from a cost-tier label.

### Share Marketing Intelligence as one file

Click **Share page as HTML** on the Marketing Intelligence page (or open
`/marketing-report`) to get **`reports/getchells-marketing-intelligence.html`** —
the same five charts, segment buttons, decision briefs and nine source tables in a
single self-contained file with embedded data and styling. Teammates open it
locally with no server, installation, account or internet connection; there are no
external assets or tracking. Like the other exports it is a frozen snapshot;
regenerate it with `python3 marketing_report.py` after the source CSVs change.
Implementation: `marketing_report.py`, `offline/marketing.html` and
`offline/marketing.js` reuse `web/marketing_charts.js` and `web/marketing.js`.

Interpretation checks are prominent:

- `marketRevenue-round0.csv` sums to **$372,795,207**, exactly Getchell's financial
  revenue. Company-segment revenue scope is **inferred from reconciliation**;
  these amounts must not be used as total industry demand.
- Segment CLV sums to **$818,472,769**, $1 above the company scorecard. This is a
  reported total allocation, not per-customer CLV. The difference is retained.
- Segment-size units/universe are not defined; no unique-buyer penetration is
  calculated. Revenue mix is not penetration or proof of market size.
- Raw preference columns sum to **1.29–1.64**, not one. Raw values are relative
  preferences, not percentages of the population. Normalization is used only
  for the explicitly labeled diagnostic below.
- The offering-share file sums to **100.2%**, consistent with rounded inputs.
  Its component shares use a common all-market denominator. Separately derived
  within-offering shares use the seven reported companies' offering revenues;
  the two denominators are never conflated.
- `pricing-round0.csv` gives Getchell's 116.72/233.44, exactly matching the
  scorecard's product-cost metrics. Selling-price vs cost basis remains
  unresolved; financial prices/markups/elasticities are **not** recalibrated.
- Product-position values and Kahn quadrant ratings are separate scales.
  Numerical ranks are comparisons of reported values, not estimated investment
  returns. FAIR VALUE has no rows in the new operating-company tables; missing
  records are not filled with zero.

**Updated assortment interpretation:** protect the lower-cost sales core,
investigate breadth needs (particularly Segment 2), and do not automatically add
depth where Getchell's already has the highest reported depth positions. Segment
1 emphasizes online/service; Segments 3/5 emphasize shopping experience. These
are preference profiles, not demographic labels or verified higher-cost buyers.

The Assortment Lab and offline copy include a **segment-alignment diagnostic**.
For each segment: normalize its eight preferences by their sum; multiply breadth
and depth weights by the respective average two-offering index changes / 100;
display ×100 as alignment-index points. Equal cost-tier exposure is assumed
because segment-by-offering purchases are missing. Aggregations use reported
size, current company revenue and reported CLV shares separately. This proxy is
**not** a Kahn rating, probability, sales lift, market share or profit estimate.
It does not change the existing Kahn v2/financial forecasts or remove unknown
assortment costs. The data-readiness checklist now marks segment evidence as
Partial rather than absent; causal decision/outcome pairs are still missing.

If the marketing directory is absent/incomplete or cannot be interpreted, the
app reports that explicitly instead of inventing records. The rest of the
financial workspace remains available.

### Four-input Assortment Lab

Open `/#assortment`. If present, the page imports Column B of
`decision_making/decision_making_team11_0.xlsx` using only Python's standard
library. The workbook's column title is displayed rather than assumed to identify
verified historical decisions. Excel percentage-formatted markup/private-brand
values are converted to percentage points; breadth/depth remain 1–100 **indices**,
not verified percentages, SKU counts, or budget shares. Initial team draft values
are lower-cost breadth/depth **65/30**, higher-cost **40/40**. The imported five-field
spend is **$69.5M**, with **$314,000** known headroom before unknown costs.

Only `low_breadth`, `low_depth`, `high_breadth`, and `high_depth` can change in an
experiment. The backend reconstructs all other values from the locked baseline.
The page can explicitly replace that baseline with a current or saved studio
plan; it cannot edit the other 12 fields. Model assumptions are frozen too.
No workbook or studio decision is silently modified. Save alternatives to Scenario
lab or download a JSON comparison; saved scenarios retain the complete 16-input
plan and assumptions. Unsaved lab state survives navigation in the current page,
not a full reload. Reloading imports the team workbook again.

Live results compare **modeled locked-plan outcomes vs modeled test outcomes**,
not test outcomes vs observed Round 0. It includes Kahn deltas, segment/total
revenue and COGS, gross profit/margin, net income, exact four-factor attribution,
and ±10-point probes. Current Kahn v2 treats an equal lower/higher-segment index
change identically: breadth affects Brand/Experience and depth Frictionless.
Segment-specific preferences/costs are not identified. Financial uplift excludes
unknown assortment/inventory/markdown/implementation and working-capital costs;
unchanged known spending is not proof of affordability. There is deliberately no
automatic "optimal assortment" claim when those costs are missing.

**The layout is recommendation → sensitivity analysis → limitations/data gaps**
in both the web and offline labs. The recommendation is concise and conditional:
protect the lower-cost sales core, test selective higher-cost depth only with
demand evidence, and allocate incremental inventory dollars by return after
costs and cash needs. It cites observed revenue mix/margins, distinguishes those
from market size/penetration, and calculates a conditional GMROI turnover check
from the frozen plan's markups (not a forecast or optimized allocation).

The expanded, visible disclosure at the end of the page
explains the model's mechanical benefit from higher indices, excluded costs,
equal segment coefficients, uncertain index semantics, lack of calibration and
sign-based coloring. Current plan-specific warnings appear there too.

The final section distinguishes existing financial anchors (inventory, cash,
inventory days and WACC) from **Available / Partial / Missing / Team decision**
requirements. Each requirement states what is known, exactly what to collect,
where to find it and why it matters. It covers SKU/index definitions,
assortment-to-inventory mapping, incremental costs, segment response, cash/credit,
operating capacity and explicit team objectives. A marketing–finance checklist
sets out how a future model could optimize profit subject to Kahn, cash, inventory
and space constraints. It adds **no invented carrying rate, cost formula or new
optimizer**. Shared content is defined in `assortment_evidence.py` and rendered by
`web/assortment_readiness.js`; these assets are embedded in offline downloads.

Implementation: `assortment.py`, `web/assortment.js`, `web/assortment.css`. Formula
cells are rejected rather than evaluating or trusting potentially stale cached
Excel results. If the workbook is unavailable, the current studio snapshot is
used with an explicit source label.

#### Playable offline HTML for teammates

Send **`reports/getchells-assortment-lab-offline.html`** as an attachment. It is a
single interactive file—not just a report or link to localhost. Recipients
download it and open it in a full browser (Chrome, Edge, Firefox or Safari).
No server, Python, packages, login, internet or paid API is needed. Email/chat
previews may block JavaScript; open the downloaded file locally instead.

The file embeds the locked team plan, financial snapshot, model coefficients,
four editable controls, textbook explanations, financial/Kahn outputs, exact
four-factor attribution, sensitivity probes and stress calculations. Other 12
decisions and model assumptions stay fixed. Its numbers are snapshots and do not
auto-update from the workbook or application.
New downloads also embed the marketing snapshot and segment-alignment diagnostic.

- **Save playable HTML copy** downloads a new standalone file preserving the
  current four choices. Unsaved changes reset when the file is reopened.
- **Export comparison JSON** exports numeric results, not a playable interface.
- **Print / save PDF** creates a static printable copy.
- No workbook or teammate's copy is modified, and data is never transmitted.
  The HTML contains company financial data: share only with intended recipients.

To export a different locked plan or current lab experiment, click **Download
offline lab** in the online Assortment Lab. It snapshots the locked baseline,
model assumptions and current four values. Regenerate the ready-made team file
with `python3 offline_assortment.py`. It can also be viewed locally at
`http://127.0.0.1:8000/assortment-offline`; send the HTML file, not that localhost URL.

The JavaScript calculation engine (`offline/assortment.js`) mirrors Kahn v2 and
the existing financial sensitivity model. It verifies embedded baseline/initial
values at startup; `tests/offline_smoke.py` compares 30 combinations with Python,
including bounds and fractional settings, in a browser with network access
disabled. Offline parity does **not** establish real-world predictive accuracy;
all existing model/cost limitations remain.

### Two-period what-if projections

Open **What-if & Year 2** (`/#whatif`). Planning convention: Round 0 is actual,
Year 1 is Round 1, and Year 2 is Round 2; these are not verified calendar-year
durations. The same nominal decisions and explicit spending repeat in both
periods. All preset comparisons share the same assumptions.

- Default market growth and unit-COGS inflation are zero. Benefits default to
  100% realization in Year 1; the Year-2 catch-up setting applies only to any
  remaining unrealized change. Therefore default Year-2 values equal Year 1,
  rather than automatically repeating the same decision improvement.
- Growth and COGS inflation, if supplied, compound from the observed anchor.
  Marketing effects are recomputed against that anchor, not compounded twice.
- Full incremental spending recurs even when modeled benefits are delayed.
  Operating costs otherwise stay at the Round-0 anchor; interest stays fixed;
  projected taxes are assumed zero. These are explicit assumptions, not an
  accounting forecast validated against simulation rules.
- No future cash balance, balance sheet, financing requirement or market share
  is invented. Quality/assortment/store costs remain unknown and excluded.
- Drafts and timing assumptions are separate from Decision studio. Valid edits
  survive navigation within the current loaded page, not a fresh page load.
  Export JSON to retain the full inputs, three-period outputs, comparisons and
  caveats. These projections are not saved to the Scenario lab database.
- **Shareable HTML report:** run the projection, then click **Shareable HTML
  report**. The downloaded file embeds its styling, checked six-input comparison,
  Kahn/financial results, Year-2 assumptions and limitations. It opens offline on
  another computer without the application. It includes the original controlled
  test, a fixed-safeguard Frictionless-first alternative, the unpriced brand-quality
  test and the submitted page draft. It does not claim a proven global optimum.
- Copying a submitted projection to Decision studio is explicit and transfers
  decisions and model assumptions only; market growth, inflation and benefit
  timing do not transfer to the studio's full-response sensitivity estimate.

Implementation: `forecast.py` and `web/whatif.js`. This remains an uncalibrated
scenario model, not measured next-round or Year-2 predictive accuracy.

A ready-to-share snapshot of the original recommendation is included at
`reports/getchells-marketing-decision-report.html`, also viewable at
`http://127.0.0.1:8000/team-report`. **Share the HTML file itself**, not the
localhost URL. Browser Print → Save as PDF also works. Regenerate that snapshot
from current source data with `python3 team_report.py`; export from the tab to
include a custom submitted draft instead. HTML exports are recalculated against
the source files at export time. No paid APIs or external assets are used.

### Chat assistant

Open **Ask the assistant** in the sidebar. Start with “Walk me through the entire app”, “Why are we making a loss?”, “How much budget is remaining?”, or “What if online investment were $5M?”. Simple what-if questions require one identifiable decision and an absolute target; multi-factor plans belong in Decision studio. The assistant may ask you to rephrase unsupported or ambiguous questions.

This is **not a general-purpose LLM or a ChatGPT integration**. `assistant.py` uses topic matching, source records and the existing analysis engine. It cannot browse, infer hidden simulator rules, or guarantee outcomes. It makes no network requests or paid model calls. Each answer uses the current working decisions and assumptions but remains a snapshot afterwards. Chat messages are held in the current browser tab’s session storage (subject to browser session restore behavior); Clear chat removes them. Do not enter secrets. Chat does not save scenarios or modify decisions.

### Analysis model

**Kahn model v2:** bounded, saturating investment effects, online/physical channel
exposure, service workload, spending per store, and explicit investment
interactions. Vendor/analytics gains are damped at their observed 100% operating
scores. Decision studio includes structural stress envelopes, frozen-peer ranks,
exact grouped score attribution, ±$1M/25-store sensitivity probes, and
extrapolation warnings. See **[MODEL_CARD.md](MODEL_CARD.md)** for full assumptions,
evidence limits, and calibration requirements. This is a structural upgrade,
**not a measured improvement in predictive accuracy**.

Saved scenario comparisons display model versions; legacy results are preserved,
and loading a scenario recomputes it using the current model. Re-save under a new
name if you want to keep that new estimate.

**This is not a calibrated simulator or a reliable prediction of next-round results.** It is a transparent what-if tool. All response coefficients are explicitly illustrative; unchanged reference decisions reproduce the Round-0 financial anchor by construction. The source files cannot identify causal decision returns.

The image displays Round 1 despite the round0 filename. Its **five** explicit spending fields total $67,000,000, leaving $2,814,000 from a $69,814,000 budget. There is no available cost formula for changes in assortment, quality, private-brand share or retail coverage. These changes are flagged, and their unknown costs are excluded—not treated as truly free. Industry min/max values are observations, not verified simulator constraints. Some form bounds and the 0–10 Kahn display ceiling are planning assumptions.

The optimizer changes only five explicit spending fields; it preserves starting modeled Brand/Experience scores and uses documented planning floors and user locks. It is a deterministic local heuristic, **not a guaranteed global optimum** or a recommendation supported by causal evidence. Re-run it after changing assumptions.

`materials/company.md` and `materials/competitors.md` were empty at implementation time. Add their contents and refresh the app to see them under Model & sources. CSV files are read from disk for each analysis request. Screenshot values are manually transcribed constants in `app.py`; replacing the image does not automatically update those values. Back up saved scenarios before replacing data. Historical saved estimates keep their original values; loading a scenario re-evaluates its inputs against current source data.

The server binds only to localhost and does not serve raw project files. It has no authentication or deployment hardening. Do not expose it publicly or use it as a production service without adding authentication, authorization, TLS, concurrency controls and operational monitoring. No payment system, hosting, or cloud services are provisioned.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Optional real-browser workflow check (requires Google Chrome on macOS; uses a disposable database and profile):

```sh
python3 tests/browser_smoke.py
```

Offline file and numerical-parity check (Google Chrome on macOS, no app server):

```sh
python3 tests/offline_smoke.py
```

Regenerate the static shareable snapshots after changing source data:

```sh
python3 marketing_report.py   # reports/getchells-marketing-intelligence.html
python3 offline_assortment.py # reports/getchells-assortment-lab-offline.html
python3 team_report.py        # reports/getchells-marketing-decision-report.html
```

## API

- `GET /api/data`: imported records, baseline decisions, benchmark ranges, sources.
- `GET /api/assortment/team`: parsed and validated team workbook snapshot, percentage normalization and cell provenance (or an explicit missing-file notice).
- `POST /api/assortment`: `{baseline, changes, assumptions?}` → locked-plan comparison, per-segment financials, attribution and probes; `changes` must contain exactly the four breadth/depth fields.
- `POST /api/assortment/offline`: the same inputs plus optional `source` → `{html, filename}` for a standalone, interactive offline lab.
- `GET /assortment-offline`: ready-made offline team lab in `reports/`.
- `GET /marketing-report`: ready-made, self-contained Marketing Intelligence snapshot in `reports/` (regenerate with `python3 marketing_report.py`).
- `POST /api/evaluate`: `{decisions, assumptions}` → transparent estimate and budget checks.
- `POST /api/project`: `{decisions, assumptions, planning?}` → three-period financial/Kahn projections plus reference, controlled and conditional-brand comparisons. Planning fields: `market_growth` (−0.2–0.2), `cogs_inflation` (−0.1–0.3), `year1_realization` (0–1), `year2_catchup` (0–1); rates are fractions, not percentages.
- `POST /api/report`: the same inputs as `/api/project` → `{html, filename}` for a self-contained learning-team report, recalculated at export time.
- `GET /team-report`: ready-to-share static report snapshot in `reports/`.
- `POST /api/optimize`: `{decisions, assumptions, goal, locked}` → candidate allocation; goal is `balanced`, `positioning`, or `profit`.
- `POST /api/chat`: `{question, decisions, assumptions, context?}` → cited local answers and a topic for simple follow-ups. Questions are limited to 2,000 characters.
- `GET /api/scenarios`: saved scenarios.
- `POST /api/scenarios`: `{name, decisions, assumptions}` → saved local scenario.
