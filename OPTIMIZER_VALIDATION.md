# Definition-aware engine and optimizer validation

## What can and cannot be assured

`review-4.0` incorporates page-cited PDF rules and the still-compatible definitions
from `materials/decision_making_factors.md`. Tests verify arithmetic, accounting
separation and optimization constraints. **Simulator prediction accuracy cannot
be assured**: only one linked submitted plan/result exists, coefficients are not
identified, and the prior engine's large historical misses remain visible.

Baseline reproduction is an identity, not a held-out accuracy result. No new
coefficient has been fitted to explain away the Brand collapse.

## Model corrections checked

- Markup is on product cost. Explicit quality/vendor cost responses affect both
  selling price and COGS; markup changes alone do not change unit cost.
- Higher breadth increases stock under a positive user-specified response.
  Stock funding is not expensed in full as COGS. Holding expense is a documented
  zero (MV p14); financing requires explicit scenario rates.
- Vendor cost and stock-management channels remain active even when the Kahn
  operating score is saturated; cost directions do not identify magnitudes.
- Online/experience capitalized fractions consume cash, are not immediately
  expensed, and add depreciation only under the specified rate. The provisional
  40%/80% expense fractions are disclosed, not asserted as simulator formulas.
- Analytics is expensed and has only multiplier terms with online/experience.
  Stores cost $1.75M each, change access not preference, and require unknown
  financing/access rules; closure proceeds and write-offs are not conflated.
- All economic scenarios reproduce unchanged R1 earnings, scores and equity
  value exactly and produce zero incremental cash movement at the reference.
- Private Brand is now documented as mix. Its unquantified loyalty/margin/
  valuation responses—not an unresolved field definition—block comparisons.
- The new empirical Brand reconstruction exposes the old missing depth channel.
  Changed depth inputs now flag `brand_depth_response`, suppress the UI's incomplete
  Brand forecast, and block optimization until a controlled input-to-position
  response or simulator rule is supplied. Observed score reconstruction is not
  silently substituted for an input-level causal coefficient.

## Optimizer checks

The frozen v2 heuristic in `app.py` is used **only for the historical audit**.
`review_optimizer.py` is the current optimizer, exposed by `/api/optimize` and
inside Decision studio—not by restoring the removed Scenario lab.

The new optimizer enumerates an explicit grid (maximum 20,000 points), evaluates
the same model and economic assumptions as the studio, checks a separately
eligible unchanged incumbent, and re-evaluates the chosen candidate. It requires
an explicit scenario budget and maximum incremental cash use. All non-spending
factors and omitted/equal-range spending factors remain locked. All Kahn floors
default to the starting modeled scores.

Tests independently enumerate small grids and compare the exact best objective,
feasible count and constraints. They also verify determinism, no mutation,
cash/budget/floor rejection, missing-rate blocking, invalid/nonfinite parameters,
bounded grid size, and blocking market-value optimization rather than treating
fixed-P/E/profit ranking as simulated market value.
Browser tests exercise a blocked search, explicit scenario entry, recalculation
and a successful verified-grid result with no automatic adoption.

**Guarantee:** best only on the explicitly checked grid plus eligible starting
incumbent, under the entered assumptions. This is neither a continuous/global
optimum nor an assured simulation result. No feasible candidate is a promise of
cash sufficiency: cash diagnostics omit receivables, payables and debt flows.
Allocation budget covers the five spending inputs, not store closure proceeds
or capex. The exact budget max-rule inputs are still incomplete. Policy-weighted
positioning and one-period profit are diagnostic objectives, not the game's
two-quadrant, parity and multiperiod valuation objective.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
python3 tests/browser_smoke.py
```

Core independent checks: `tests/test_definition_economics.py`. Current endpoint
checks: `tests/test_app.py`. Historical miss preservation and current baseline:
`tests/test_round_review.py`. No user workbook/source files are modified.
