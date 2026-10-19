# Archived Round 0 marketing analysis (superseded by Round 1 review)

Analysis of the nine Round-0 CSVs in `materials/marketing/`. Live calculations
and all raw tables are available in **Marketing Intelligence** (`/#marketing`).

## Source interpretation before strategy

| Source | Useful evidence | Important boundary |
|---|---|---|
| marketSize | Six reported sizes, Rounds −2/−1/0 | Units and unique-customer universe unverified |
| marketRevenue | Six revenue allocations, three rounds | Round 0 totals company revenue, not industry revenue |
| marketCLV | Six reported CLV allocations, three rounds | Aggregate totals, not per-customer CLV |
| preference | Eight raw preferences for each segment | Columns do not sum to 1; not population percentages |
| revenueByOffering | Company lower/higher-cost revenues | No customer-segment × offering cross-tab |
| revenueByAccessPoint | Company online/store revenues | No segment × channel cross-tab |
| revenueMarketShare | Rounded offering contributions to a common market total | Not share within each offering; sums to 100.2% |
| pricing | Reported comparative values | Getchell's values match scorecard cost metrics; selling-price basis unresolved |
| productPosition | Twelve comparative attribute positions | Different scale from Kahn; marginal response unverified |

Segment revenue sums to **$372,795,207**, exactly the financial income statement.
Segment CLV sums to **$818,472,769**, **$1** above the scorecard. The app labels
the company scope as an inference and retains the source differences. Size
figures sum to **13,463,824 reported units**, not a verified reachable-buyer count.

The seven reported companies' offering revenues total **$2,751,577,551**:
lower-cost **$1,924,684,695** and higher-cost **$826,892,856**. Getchell's derived
within-offering shares are approximately **14.71%** and **10.85%** respectively.
Those are not the source's **10.3% / 3.3%** all-market contribution shares and are
not customer penetration. Minor channel/offering dollar differences are shown in
the audit rather than silently corrected.

## Six different customer profiles

| Segment | Current company revenue | Three highest raw preferences | Practical question to test |
|---|---:|---|---|
| 1 | $64,993,892 | Online .27; low price .25; service .24 | Is discovery/convenience/service the constraint rather than more range? |
| 2 | $81,483,203 | Breadth .38; retail .30; depth .20 | Which unmet shopping missions justify an assortment/retail test? |
| 3 | $47,163,027 | Experience .40; brand .30; breadth .16 | Which differentiated proposition improves customer value? |
| 4 | $31,271,958 | Retail .28; online .24; low price .22 | How should physical and online access work together? |
| 5 | $84,144,376 | Experience .43; breadth .22; retail/service .19 (tie) | Is the experience supporting the assortment promise? |
| 6 | $63,738,751 | Retail .30; experience .25; breadth .24 | Would additional depth add value when depth preference is only .02? |

Segments **5 and 2 contribute about 44.4% of current company revenue**. This
does not establish their total addressable demand, buyer penetration, income or
cost-tier purchasing. Avoid invented demographic personas.

## Consequence for assortment choices

The original generic suggestion to test higher-cost depth should now be challenged:
Getchell's reported lower-cost depth position is **3.7** and higher-cost depth
**5.0**, both numerically highest among the seven companies. Lower-cost breadth
is **2.4**, behind Pricemart's **4.6**. Higher-cost breadth is already numerically
highest at **4.0**. These are descriptive positions, not proof that another point
of breadth/depth generates any particular return.

Updated hypothesis: **protect proven lower-cost availability; investigate
customer-specific breadth gaps before adding more depth**. Preserve the existing
Brand/Experience strategy, but route service/convenience investments to the
segments that value them. Do not infer that Segment 3/5 must buy higher-cost
products merely because they emphasize brand/experience.

Assortment Lab now shows who a change emphasizes through an explicit
preference-alignment proxy. It uses normalized preferences and equal exposure
across the two cost tiers because purchase affinity is missing. It is separate
from and does not recalibrate Kahn/financial predictions. Higher alignment is
not a validated sales response or financial benefit.

## Still required for a defensible optimizer

- Segment-specific purchases/units and revenue **by cost tier and channel**.
- Definitions for market-size units, buyer counts and penetration denominators.
- Actual selling-price vs product-cost definitions.
- Paired submitted decisions and next-round outcomes for causal response checks.
- Assortment-to-SKU/inventory rules, incremental handling/markdown/holding costs,
  financing timing and physical capacity constraints.
- Team-approved marketing targets and profit/cash/risk constraints.

No new causal coefficients or inventory costs have been invented from the new
tables. Recommendations and diagnostics are now better informed; measured
forecast accuracy and an optimal assortment remain unestablished.

## Use the decision charts

The live Marketing Intelligence dashboard offers a revenue/CLV portfolio map,
decision-lens rankings, a breadth/depth preference map, selected-segment indexed
history and normalized preference composition. Select a segment in any view to
update the decision brief and source drill-down. Compare objectives explicitly:
Segment 5 leads current company revenue; Segment 2 leads aggregate CLV; Segment 1
has the largest reported size. Under normalized experience emphasis, Segment 3
ranks above Segment 5 even though Segment 5 has the higher raw experience weight;
this illustrates the normalization assumption, not a discovered response rate.

Use the charts to formulate a targeted experiment and identify the evidence
needed to fund it—not to infer a segment's profit, penetration or optimal budget.

## Share the analysis

`python3 marketing_report.py` writes
**`reports/getchells-marketing-intelligence.html`**, a single self-contained file
with the same charts, segment selectors, decision briefs and nine source tables.
It opens offline (no server, install, account or internet) and can be sent
directly; `GET /marketing-report` serves the same snapshot, and the live page's
**Share page as HTML** button downloads it. It is a frozen copy of the round it was
generated from, so regenerate it after the source CSVs change.
