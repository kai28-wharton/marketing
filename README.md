# Getchell’s Decision Lab · Round 3 workspace

The dashboard uses **submitted decision 2** and observed results in
**`materials/round2`**, compared with export 1. **Round 3 is the current planning
period**, not an observed outcome. No workbook or simulation submission is edited.

## Run

```sh
python3 app.py
```

Open **http://127.0.0.1:8000**. Restart a running server after this update, then
refresh. Python 3.10+ and a modern browser; no paid services required.

## Source naming and timeline

- Submitted baseline: `decision_making/round_2/decision_making_team11_round2.xlsx`, Column B.
- Historical renamed workbook: `decision_making/round_1/decision_making_team11_round1.xlsx`.
- User-confirmed association: decision 2 generated outcomes in `materials/round2`.
  Original export row/column labels are retained, not shifted.
- Current statements and marketing: `materials/round2/{finance,marketing}`.
- Latest supplied industry aggregate is **export 1**, in
  `decision_making/round_2/industryDecisions-round1.csv`. Renaming the folder does
  not make those rows current-period benchmarks.
- Current segment CLV is **available** in `marketCLV-round2.csv`. Historical rows
  backfill values missing from the earlier export-1 package.

## Pages

**New: Customer segmentation decision** — open `/#segmentation` from the sidebar.
Compare all six segments on market size, aggregate CLV, all eight preference
intensities, financing capacity and current competitor strengths. Change the
ranking lens or select a discussion group to see its one-line strategic
implication. Segment 3 stays the fit anchor; 5 versus 6 is the main growth debate,
while 2 leads existing-equity protection. Controls do not adopt a plan or allocate
spend. The shareable Marketing Intelligence HTML now includes this page too.

1. **Executive overview** — export 2 versus export 1, current CSV fair values,
   financials and actual submitted input changes.
2. **Marketing Intelligence** — new Experience-leadership / competitive-Brand
   strategy, segment size/CLV/preference decision, strategic trajectory,
   competitors and complete source tables. **Segment 3 is the primary target**,
   chosen for its Brand/Experience fit; **Segment 5 is a conditional secondary**
   gated on Frictionless parity; Segment 4 is a selective reserve; existing
   Segments 2/6 are defended. Low Price and Frictionless are fair-value
   safeguards.
3. **Financial health** — current statements, ratios, financing and cash-movement
   proxies. Source rounding is retained.
4. **Decision Insights** — latest Brand/strategy direction, finance and STP.
   Brand improved; the old Brand-loss narrative is not relabeled as current.
5. **Decision studio** — starts at **all 16 actual decision-2 values**, anchored
   at export-2 actuals. Budget arithmetic updates live; predictions require
   recalculation. Missing responses remain unknown.
6. **Round 3 planning status** — the segment focus is recommended; the
   16-factor allocation and budget have not been generated or confirmed. The
   old recommendation is not reused.

## Budget and prediction boundaries

Decision-2 spending totals **$71,422,000**. It is a historical allocation,
**not a confirmed Round 3 ceiling**. The computable revenue-based budget arm is
14% × $561,280,114 = **$78,579,215.96**; the inflation-adjusted arm remains unknown.
The studio accepts an explicit scenario ceiling, including the revenue arm, but
does not mark it as approval. Inventory, store capital and financing require a
separate cash/credit review.

Fair value uses each round’s **CSV FAIR VALUE** values, not the conflicting 75%
slide formula or an exact two-thirds ratio. No causal coefficients are fitted
from submitted bundles. No frozen pre-outcome prediction for decision 2 was
supplied, so no new backtest accuracy or confidence interval is invented.

## Implementation and history

- `round_review.dataset()` selects the latest observed export; `dataset(1)`
  retains the historical export-1 analysis for regression tests.
- `current_review.py` imports submissions/exports and records period provenance.
- `web/current.js` renders the current workspace; `web/review.js` retains shared
  utilities, API handlers and the historical renderer.
- `review_model.py` / `decision_economics.py` anchor at the dataset’s current
  export. Unchanged inputs reproduce reported actuals by construction, including
  rounding—not a prediction that the next period repeats.
- `MODEL_CARD.md` gives current limits; `ROUND2_REVIEW.md` summarizes latest
  outcomes. Earlier review documents are historical snapshots.

## Offline Marketing Intelligence

Download from the page, or regenerate:

```sh
python3 marketing_report.py
```

Share `reports/getchells-marketing-intelligence.html`. It works offline with
current charts/CLV and no editable decisions, external assets or network calls.
Older downloads do not automatically update.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/browser_smoke.py
```

Browser checks require Google Chrome on macOS: all current pages, timeline,
actuals, CLV, mobile/deep links, budget scenarios, prediction/reset and offline
opening. Historical backend fixtures explicitly select export 1.
`tests/round1_browser_smoke.py` is the archived previous browser workflow.
