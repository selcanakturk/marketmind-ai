# Customer Return Risk — Final Model-Family Selection

## Frozen problem

The prediction unit remains a Complete Journey 2.0 grocery-retail household at snapshot `T`. Positive class `return_risk_target=1` means zero distinct baskets in `(T,T+28 days]`; it is not contractual churn. Eligibility, April–August training, September/October validation, and the exact 16 point-in-time features are unchanged.

> **NOVEMBER LOCKBOX REMAINS UNTOUCHED.** The notebook constructs April–October only and asserts that November 30 is absent. No November outcome was labeled, scored, or inspected.

## Existing baselines and final-challenger rationale

The frozen heuristic leads the initial ranking baselines at pooled PR-AUC 0.4688. HGB-1 reached 0.4672 PR-AUC, 0.8574 ROC-AUC, 0.0913 Brier, and 0.2932 log loss, narrowly failing the heuristic gate. One final sklearn challenger was justified because Extra Trees offers randomized nonlinear partitions distinct from boosting while retaining a lightweight dependency contract.

The experiment is deliberately narrow: exactly three Extra Trees configurations, raw frozen features, no class weighting, no scaling, no feature additions, no resampling, and no further family search. The heuristic remains a legitimate final policy rather than a hurdle to bypass through metric chasing.

## Extra Trees candidates and temporal results

| Candidate | Configuration summary | September PR-AUC | October PR-AUC | Pooled PR-AUC | Pooled ROC-AUC | Brier | Log loss |
|---|---|---:|---:|---:|---:|---:|---:|
| ET-1 | 300 trees; unlimited depth; leaf 5; sqrt features | 0.4906 | 0.4764 | 0.4817 | **0.8592** | **0.0904** | **0.2910** |
| **ET-2** | **300 trees; depth 12; leaf 10; sqrt features** | **0.4989** | 0.4695 | **0.4827** | 0.8576 | 0.0916 | 0.2944 |
| ET-3 | 300 trees; depth 12; leaf 5; 0.8 features | 0.4786 | 0.4695 | 0.4715 | 0.8571 | 0.0910 | 0.2930 |

All three exceed the 0.4688 heuristic gate, and none shows severe temporal instability. ET-2 has the highest pooled and September PR-AUC. Its September→October change is −0.02942 PR-AUC and −0.01406 ROC-AUC; October remains fully included.

ET-2 and ET-1 differ by only 0.21% relative pooled PR-AUC, invoking the within-1% policy. ET-2 is selected because its October PR-AUC is only 0.00693 below ET-1 while its September advantage is 0.00829, giving the strongest pooled primary metric; it is also depth-bounded and approximately one quarter ET-1’s artifact size. ET-1 has slightly better Brier/log loss and ROC-AUC, but not enough to override the primary metric and bounded production behavior.

## Final comparison

| Approach | Pooled PR-AUC | ROC-AUC | Brier | Log loss | Status |
|---|---:|---:|---:|---:|---|
| Recency-frequency heuristic | 0.4688 | 0.8459 | not applicable | not applicable | final simple benchmark |
| HGB-1 | 0.4672 | 0.8574 | 0.0913 | 0.2932 | learned research reference |
| **ET-2** | **0.4827** | **0.8576** | 0.0916 | 0.2944 | selected learned ranking approach |

ET-2 improves on the heuristic by **0.013871 absolute PR-AUC** and **2.959% relative**. It improves on HGB-1 by 0.015456 absolute PR-AUC (3.31% relative) and 0.000249 ROC-AUC. HGB-1 retains slightly better Brier/log loss, but learned candidates differ by more than 1% relative PR-AUC, so the tie-break hierarchy is not needed between them.

## Household-clustered bootstrap

Three hundred deterministic household-cluster resamples give ET-2:

- PR-AUC 95% interval `[0.4313,0.5261]`;
- ROC-AUC 95% interval `[0.8408,0.8714]`.

Repeated household snapshots remain together during resampling. The interval communicates development uncertainty; selection still follows the predeclared observed-metric policy.

## Capacity metrics

| Model | Capacity | Precision | Recall |
|---|---:|---:|---:|
| Heuristic | 5% | **0.5947** | **0.2160** |
| HGB-1 | 5% | 0.5639 | 0.2048 |
| ET-2 | 5% | 0.5903 | 0.2144 |
| Heuristic | 10% | **0.5408** | **0.3920** |
| HGB-1 | 10% | 0.5210 | 0.3776 |
| ET-2 | 10% | 0.5364 | 0.3888 |
| Heuristic | 20% | 0.4183 | 0.6064 |
| HGB-1 | 20% | **0.4294** | **0.6224** |
| ET-2 | 20% | 0.4249 | 0.6160 |

ET-2 nearly matches the heuristic at 5%/10% and lies between the heuristic and HGB at 20%. Pooled PR-AUC improvement does not imply dominance at every intervention capacity. These are ranked-capacity diagnostics, not business impact or a threshold decision.

## Ranking agreement

Overlap is calculated on the prediction entity `(household_id,snapshot_at)`.

| Capacity | Pair | Intersection | Jaccard |
|---:|---|---:|---:|
| 5% | Heuristic / HGB-1 | 153/227 | 0.508 |
| 5% | Heuristic / ET-2 | 191/227 | 0.726 |
| 5% | HGB-1 / ET-2 | 168/227 | 0.587 |
| 10% | Heuristic / HGB-1 | 343/453 | 0.609 |
| 10% | Heuristic / ET-2 | 373/453 | 0.700 |
| 10% | HGB-1 / ET-2 | 374/453 | 0.703 |
| 20% | Heuristic / HGB-1 | 733/906 | 0.679 |
| 20% | Heuristic / ET-2 | 789/906 | 0.771 |
| 20% | HGB-1 / ET-2 | 806/906 | 0.801 |

ET-2 is closer to the heuristic than HGB at the narrowest capacities and converges strongly with both learned/behavioral rankings by 20%. It refines rather than replaces the central inactivity signal.

## Calibration diagnostics

ET-2’s pooled Brier 0.0916 and log loss 0.2944 are slightly worse than HGB-1 but better than unweighted Logistic’s 0.0929/0.2980. ET-2’s decile estimates are compressed: its highest bin averages 0.4386 while 0.5364 are observed, and several middle-high bins also underestimate observed risk. HGB’s upper bin slightly overestimates and Logistic’s upper bin also modestly overestimates.

ET-2 therefore supplies useful ranking but is not calibrated. No calibrator was fitted. The heuristic was correctly excluded from probability calibration because it is only a ranking score.

## Error analysis

At the diagnostic—not selected—0.5 cutoff, ET-2 yields 64 true positives and 561 false negatives, compared with HGB-1’s 182 and 443. ET-2 false negatives have median recency 20 days, 16 lifetime baskets, one recent basket, and recent spend 8.71; HGB false negatives have median recency 13 days and recent spend 20.30. ET-2’s compressed estimates make 0.5 especially unsuitable as an operating cutoff.

Only two HGB false negatives become ET-2 true positives at 0.5, while HGB recovers 120 ET-2 false negatives. Thus Extra Trees does not resolve the partially-active false-negative group at this arbitrary cutoff. Its advantage is ranking across the full score distribution, consistent with PR-AUC—not threshold-0.5 classification. No features are added from this analysis.

## Computational profile

| Approach | Fit time | Prediction time, 4,529 rows | Serialized size |
|---|---:|---:|---:|
| Heuristic | negligible | negligible arithmetic | ~0.1 KiB parameters |
| HGB-1 | ~0.52 s | ~0.0085 s | 290.6 KiB |
| ET-1 | 0.42 s | 0.050 s | 31.84 MiB |
| **ET-2** | **0.28 s** | **~0.04 s** | **8.20 MiB** |
| ET-3 | 0.39 s | 0.039 s | 18.31 MiB |

ET-2 is much larger and slower than HGB/heuristic but remains operationally small in absolute terms. Its depth bound and much smaller footprint than ET-1 support the final choice; size did not override its primary-metric improvement.

## Final model-family decision

**Extra Trees is frozen as the selected learned family, using ET-2 as the selected development configuration.** It passes the heuristic gate with stable-enough forward performance and clearly exceeds HGB-1 on primary PR-AUC. The recency-frequency heuristic remains the mandatory simple benchmark and fallback, while HGB-1 remains a research reference.

The final ranking approach is learned ET-2. Until calibration is evaluated, its output is an **uncalibrated return-risk score / uncalibrated probability estimate** used for ranking. It must not be called a calibrated probability, confidence, or observed business impact. No threshold is frozen.

## Known limitations and next step

Complete Journey is a short grocery-household panel with repeated rows and limited seasonality. Development metrics and feature relationships are non-causal. ET-2 is selected from a deliberately narrow family search, not claimed globally optimal.

The current model-family search is closed. No further classifier family or feature search should be started absent a methodological defect. The next step may design development-only calibration and threshold/capacity governance for ET-2, with all choices frozen before any one-time lockbox evaluation.
