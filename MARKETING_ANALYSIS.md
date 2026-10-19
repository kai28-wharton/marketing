# Round 1 · customers, positioning and value

> Historical export-1 snapshot. Current marketing uses export 2, including reported segment CLV; see `ROUND2_REVIEW.md`. The current planning period is Round 3. The saved Marketing Intelligence HTML is regenerated from current data separately.

## Business improved, positioning diverged

- Revenue: **$481,926,248**, +29.3% versus Round 0.
- Net income: **$8,399,905**, from a $6,289,333 loss.
- Equity market value: **$248,965,528**, +167.1%.
- Kahn: Brand **6.3 → 3.7**, Experience **5.8 → 6.0**, Frictionless **3.4 → 3.3**,
  Low Price **4.9 → 4.7**. An equity-value rise is not proof of stronger positioning.

## Segment choices

At export 1 the team used an **Experience first / Low Price second** strategy,
with Segment 6 as primary acquisition candidate and Segment 4 selective
secondary. **This was superseded for Round 3 planning**: the team now targets
Experience leadership plus a very competitive Brand, with Segment 3 as primary
and Segment 5 conditional secondary (see `ROUND2_REVIEW.md`). Under the new
strategy, “Experience top 1” means competitive rank #1, not merely our strongest
quadrant, and Low Price / Frictionless are fair-value safeguards.

Segment 2 now leads company revenue ($104.24M); Segment 5 remains important
($99.63M). Segment 4 has the fastest revenue growth (~46.3%), but is smaller
($45.77M). Segment 1 has the largest reported size; those units are not verified
unique buyers. Company revenue by segment is not the industry's segment demand.

The page defaults to Segment 6 and links segment selection, ranking lenses, raw
preference changes and indexed size/revenue histories. Three strategy plots lead:

- **Needs/target bubble plot:** R1 raw LOW PRICE on x, SHOPPING EXPERIENCE on y;
  larger bubbles indicate more current company segment revenue (not market size
  or profit). S6/S4 are acquisition/development roles, S5/S2 defended business.
  Click or keyboard-select a bubble to inspect the segment. The two displayed
  attributes are not a complete segment utility model or an allocation formula.
- **Experience × Low Price trajectory:** actual company Kahn scores, Getchell's
  R0 → R1 arrow, six other retailers at R1 only. The actual direction is up/left
  (4.9, 5.8) → (4.7, 6.0). The intended direction is to strengthen Experience
  while moving right on Low Price; no invented future endpoint is plotted.
- **Growth context:** R0 → R1 company segment revenue growth versus growth in
  total market-segment consumers, ordered by strategic role. These percentages
  have different underlying measures; divergence does not identify acquisition,
  penetration, price effects or causal returns.

CSV fair-value benchmarks are shown beside these plots. Shared HTML embeds the
targeting policy and segment evidence, but no editable plan or recommendation
draft. Its plots remain interactive offline. Existing downloaded snapshots must
be regenerated to acquire the changes. Targeting roles remain distinct:

- Segment 1: online, value and service.
- Segment 2: breadth and retail access.
- Segment 3: brand and experience.
- Segment 4: coordinated retail/online access and value.
- Segment 5: experience and breadth.
- Segment 6: retail/experience, with very low raw depth preference (0.03).

No segment-specific profit, offering/channel affinity, elasticity or customer
penetration is inferred. Round 1 segment CLV is **missing**; company CLV
($1.023B) cannot be allocated using historical shares without inventing evidence.

## Product positions and the Brand problem

Lower-cost breadth position rose 2.4 → 3.9 while lower-cost depth fell 3.7 → 1.7.
Higher-cost depth fell 5.0 → 1.2. Higher-cost breadth stayed at 4.0. Service slipped
3.4 → 3.2 and experience rose 2.4 → 2.8. Product-position scales are not Kahn
scales, and these movements do not isolate a causal decision coefficient.

The current workbook has higher-cost depth 10, private-brand shares 44%/70%, and
quality 6/6. The bundle coincides with Brand deterioration, but a single transition
cannot identify whether mix, pricing, competitors, relative positioning or another
simulator mechanism drove it. The old model incorrectly predicted rising Brand;
that miss remains visible rather than being explained away.

## Market value versus FAIR VALUE

Market Value is observed **equity** value. The supplied slides document
max(DCF, CLV/private-brand-adjusted, liquidation), not constant P/E. Model 4.0
retires the P/E shortcut; exact forecast/horizon/credit/floor rules are unavailable,
so changed-plan values and market-value optimization are unquantified/blocked.

FAIR VALUE is a quadrant benchmark, **not an eighth retailer**. Use the exact
CSV values: Brand **3.5**, Experience **4.3**, Frictionless **5.1**, Low Price **3.6**.
Working gaps are **+0.2 / +1.7 / −1.8 / +1.1**. Brand is already above parity;
automatic depth expansion is no longer recommended to repair a false deficit.
Frictionless remains below parity; the team defers full recovery in R2. The
observed floor/leader ratios are 67.31% / 67.19% / 67.11% / 65.45%, respectively.
Do not replace the CSV with an exact 67% formula. The slide's conflicting 75%
rule remains audit context only; no version/normalization explanation is invented.

## Next evidence to collect

MV p12 resolves the duplicated Private Brand definition as **mix**; Intro p14
confirms national/private quality. Model 4.0 also uses the documented no-holding-
expense and $1.75M/store rules, multiplier-only analytics and direct quadrant
pathways. Numeric response, retention, credit and valuation rules are still
needed. Obtain customer purchases by segment × offering × channel, and
multiple submitted decisions linked to outcomes. Use controlled simulator tests
to distinguish pathways before replacing the provisional response coefficients.

PDF reconciliation: `SIMULATION_REVIEW.md`. Full audit: `ROUND1_REVIEW.md`.
Model boundaries: `MODEL_CARD.md`. Share the current
page via `python3 marketing_report.py` → `reports/getchells-marketing-intelligence.html`.
