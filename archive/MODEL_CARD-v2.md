# Archived Kahn model v2 — decision sensitivity, not validated prediction

## Intended use and evidence

Compare directional effects of six investment/reach levers, examine interactions,
and challenge a marketing plan. **There is no demonstrated increase in predictive
accuracy:** no simulator formulas or paired historical decisions/outcomes are
available. No model has been causally fitted or validated out of sample.

Observed inputs:
- Round-0 Kahn scores anchor each quadrant; three Kahn rounds provide two score
  changes per quadrant, used only for stress floors.
- Industry decision averages set assumed capacity scales, not fitted optima.
- Online sales share (51.3%) weights channel exposure as a proxy.
- Vendor management and analytics scores (100%) reduce assumed upside headroom.
- Screenshot decisions are a planning reference, **not verified historical
  decisions that caused the Round-0 scores**.

Implementation and all coefficients: `prediction.py`. Financial propagation
remains illustrative in `app.py`; this upgrade does not validate revenue or profit
forecasts. All point estimates preserve the original anchor at unchanged inputs.

### Additional marketing evidence

The nine `materials/marketing/` CSVs now supply six raw preference profiles,
three-round segment size/revenue/CLV series, company offering/channel revenues,
reported pricing and product positions. `marketing.py` reconciles scope and
denominators; see `MARKETING_ANALYSIS.md` for findings. These observations improve
targeting context but are **not** paired decision-response data. Product positions
are not Kahn ratings, preferences are not population percentages, and pricing
values match reported cost metrics with an unresolved basis.

Assortment Lab's separate segment-alignment proxy normalizes preferences and
assumes equal cost-tier exposure because the purchase cross-tab is missing. It
does not feed into `prediction.py`, `app.evaluate()` or the financial forecast.
Neither scores nor profits are claimed to be newly calibrated from these files.

## Structural response

Capacity is `x / (x + h)` with `h` initially the industry average. This is a
bounded, diminishing-return assumption. Online uses investment; retail reach
uses store coverage. Service intensity is spending divided by assumed workload:
`online_share + (1-online_share) * stores/reference_stores`.

In-store quality uses experience dollars per store; its half-saturation is
industry experience spending divided by industry coverage. At zero stores its
physical experience capacity is zero. Increasing coverage can improve reach
while diluting service and store experience. This is a structural hypothesis,
not an estimated causal finding. Opening/closing costs remain **unknown** and
are excluded from spending and profit; retail changes stay explicitly unpriced.

For vendor and analytics capacity changes, positive changes are multiplied by
`1 − 0.85 * observed_operating_score` (scores expressed as fractions). At 100%,
15% of assumed positive response remains; cuts retain full downside. Neither
100% operating score nor this headroom prior proves actual incremental ROI.

Interactions are capacity products: online×analytics, vendor×analytics,
service×store quality, and analytics×store quality. Features are twice the
capacity change relative to the screenshot reference, weighted by channel mix
where relevant. Product/quality/markup inputs keep explicit, uncalibrated
coefficients. All weights are in `prediction.WEIGHTS` and shown in Model & sources.

A logistic response maps the weighted sum to an **assumed** 0–10 score range:

```
raw = score_response * sum(weight * feature)
scale = anchor * (1 - anchor/10)
score = 10 * sigmoid(logit(anchor/10) + raw/scale)
```

It preserves the anchor and has unit slope in raw score points there; it avoids
abrupt clipping plateaus. Numerical guards handle boundary anchors and extremes.

## Explainability and stress cases

- **Exact grouped Shapley attribution:** six levers plus a product-input group;
  all 128 subsets evaluated. Contributions allocate interactions and sum exactly
  to the final modeled score difference, before display rounding. Not real-world
  causal attribution.
- **Marginal sensitivities:** one-at-a-time ±$1M or ±25 stores, relative to the
  working plan. Bounds prevent impossible probes; budget-exceeding probes are
  explanatory only. No unknown store cost is invented.
- **Structural stress envelope:** 8 combinations of response strength ×0.6/1.4,
  half-saturation scales ×0.75/1.25, and online channel share ±10 percentage points.
  (2×2×2 combinations). Widened by the
  maximum absolute observed Getchell's historical score step per quadrant,
  minimum 0.08. The point is included in the envelope. This is **not** a confidence
  interval, estimated error bar, or calibrated prediction interval. It does not
  span all possible structural mistakes or future shocks.
- **Frozen-peer ranks:** compare scores and envelope endpoints to other retailers'
  observed Round-0 scores. Competitors are not predicted.
- **Extrapolation flags:** warn when a six-lever input lies outside observed
  industry min/max; these ranges are not hard simulator limits.

## Integration and versioning

`evaluate()` returns `model_version` and `kahn` diagnostics. Fast point-only
evaluation supports optimizer candidates; the final candidate gets a full report.
The chatbot, optimizer and Decision studio share this same model. Saved scenarios
keep their original model version/results. Legacy rows are labeled v1; loading
them recomputes under v2 without overwriting the stored snapshot.

## Required evidence to calibrate and validate

Collect by company and round: all actual decisions submitted, start/end Kahn
scores, revenue and segment volumes/prices, channel mix, operating scores,
store costs, and material competitor/environment changes. Keep the decision
timestamp and outcome round explicit. Simulator help/tooltips can supply actual
constraints and causal rules.

With enough paired observations: validate joins, hold out later rounds (avoid
leakage), compare against unchanged-score and trend baselines, report per-quadrant
MAE and bias, assess interval coverage, and only then revise coefficients or
claim measured prediction accuracy. Cross-sectional industry averages alone
cannot establish a decision-to-score relationship.
