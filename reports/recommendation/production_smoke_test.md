# PRODUCTION SMOKE TEST — NO OUTCOME METRICS

Run at the final available snapshot, `2015-09-18T02:59:47.788Z`, using the serialized all-history artifact. This is an operational check only. No target was constructed or inspected and no quality metric was calculated.

| Operational observation | Value |
|---|---:|
| Visitor scenarios scored | 4 |
| Recommendation rows | 80 |
| Complete popularity fallback rate | 25.00% |
| Partial-fill rate | 0.00% |
| Unique recommended items | 80 |
| Seen recommendation share | 31.25% |
| Novel recommendation share | 68.75% |
| Total scoring runtime | 15.973 s |
| Mean single-visitor latency | 3.993 s |
| Observed throughput | 0.250 visitors/s |

The scenarios were authentic rich-known visitor `1150086`, authentic visitor `13` with exactly two distinct known items, ordinary known visitor `0`, and unknown visitor `1407580`. Every list had 20 unique items and contiguous one-based ranks. The complete fallback belongs to the deliberately unknown visitor. Partial-known and new/unknown-history behavior is covered with controlled regression fixtures because those cases require history not represented by the final training catalog.

The latency includes revalidating and canonically sorting the full 2.76-million-row event table for each standalone call. A later API should validate/materialize its current snapshot once and reuse it across requests; this serving-state optimization does not change the frozen recommender.
