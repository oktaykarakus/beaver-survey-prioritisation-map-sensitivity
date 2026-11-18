# P2-C3 experimental freeze, v1.0

**Written for:** reviewers and the project lead. It fixes every analysis decision of the national experiment before any national score, ranking or allocation is computed or inspected.

**Status: FROZEN** — `2026-11-17 23:22 UTC, after preflight run 2 PASS and before any national overlay tile beyond the 14 preflight tiles, score, ranking or allocation was computed`. The preflight passed (`P2C3_PREFLIGHT_REPORT.md`). Changes after this point are allowed only as a recorded, versioned amendment (§14). No amendment may be motivated by an outcome.

## 1. Inputs and checksums

| Item | Value |
|---|---|
| Eligible network (P2-C1) | `05_Experiments/BHSI_v2_P2C/c1/p2c1_eligible_network.gpkg`, sha256 `7a8beaa04483d3ad647f09ddeaddc682dd79351c9d04862077273aa187eacc25`. Content hash `85e07e56…7472`. 76,082 fragments, 71,629.864 km, 105 reportable catchments |
| Excluded network (used only for water sub-typing lines) | `p2c1_excluded_network.gpkg`, sha256 `d7cdca00…a5990` |
| CORINE 2018, recovered (P2-A) | `clc2018_eea_recovered_3035.gpkg`, sha256 `bb68d31d…6f1` |
| Living England Phase IV (P2-B) | extracted GeoPackage sha256 `ae47a170…1c7f` (download zip `72a23cce…3101f`) |
| Frozen class table | `class_treatment_table_FROZEN.csv`, sha256 `c44dcdac…89f0`, generated from `P2B_ECOLOGICAL_CROSSWALK.csv` (sha256 `097d48c9…31c6`) |
| Code | `04_BHSI_v2_Development/p2c3/` (overlay code hash `23f5dbbad31e4c9129f1db0d0c1938225c754b5317ffbefa0814786cd42c82b7`; the hash is stored in every tile output); allocation library `p2c3_alloc.py`, sha256 `2faf517d23af98716c4107bf2090d31a5ad78e73214ccc3a536e51b2146ead2e` |

The 71,629.9 km is a reconciliation reference: the national reach table must sum to it to 1e-6 km. It is not a target that any step adjusts towards.

## 2. Reach units and riparian zone

- **Primary unit:** the P2-C1 eligible fragment (an OS Open Rivers piece clipped to England), with a 40 m buffer on the centreline. Every quantity is length-weighted.
- **Sensitivity units:** 20 m and 100 m buffers; standardised segments (fragments longer than 1 km, and 500 m, are cut into ⌈L/len⌉ equal parts, with a 40 m buffer). Each segment inherits its fragment's catchment.
- **Raster support:** common 10 m grid aligned at (0, 0). National processing is in 50 km tiles. Each tile has a margin of 3 km beyond the furthest buffer of any reach assigned to it; a reach is assigned to the tile containing its bounding-box centre. The preflight showed that tiled and untiled results agree within tolerance.

## 3. Representations (D-2)

| Arm | Role | Definition |
|---|---|---|
| **C** | primary | Recovered CORINE 2018, native classes → frozen categories |
| **LEg** | primary | Living England IV with the P2-C2 grain control: 10 m raster; per-class disk opening, radius 5 px (objects ≥110 m wide kept), removed pixels filled from the nearest kept pixel; GDAL sieve 2,500 px (25 ha), 8-connected; repeated until <0.01% of domain pixels change, at most 5 cycles |
| **LEn** | diagnostic | Living England IV, native 10 m rasterisation. Used only to measure grain sensitivity (C vs LEn and LEn vs LEg); no primary hypothesis rests on it |

## 4. Composition, water, unknown and score (K1 only; D-1)

- **Water (R-W):** water classes are removed from both numerator and denominator in every arm.
- **Unknown:** LE Unclassified, plus any pixel with no source polygon, is kept in the land denominator. It takes score 0 at A-lo and 1 at A-hi (frozen bounds [0, 1], as in P2-C2).
  - Sensitivity "conditional": unknown is removed from the denominator.
- **Score:** s = Σ (land share of category × K1 value), with K1 values BLW 1.0; CON, SCR, heath (RGH), WET 0.5; ARB 0.1; URB, MIN, COA, BARE 0.0.
- **Interval categories:** GRS [0.1, 0.5], AGM [0.1, 0.5], URBVEG [0.0, 0.5], LE Bracken [0.1, 0.5].
  - **A-lo** takes every interval at its lower end; **A-hi** takes every interval at its upper end.
  - No midpoint is used. No new score is introduced. K2 is excluded.
- **F-Z, zero-land reaches** (no land left after removing water): the score is undefined and is reported.
  - For selection and evaluation such a reach counts as value 0 in that arm.
  - Sensitivity: reaches with zero land in any arm are dropped from every scenario jointly, and the budget is re-based on the remaining length.
- **Woody share** (reference R2) = (BLW + CON + SCR) / land, computed in each arm from its own composition only. It is the same at both endpoints.
- **Gradient:** not in any score and not used as a filter. The Phase 1 parent-piece `gradient_pct` and `gradient_score` are attached as a diagnostic and reported for selected reaches.

## 5. Scenarios

| Set | Scenarios |
|---|---|
| **Core (4)** | C-lo, C-hi, LEg-lo, LEg-hi |
| Diagnostic (2) | LEn-lo, LEn-hi |
| References | R1 random (national; catchment-stratified); R2 woody share (C, LEg, LEn); O_j scenario optimum |

## 6. Budgets and allocation strategies

- **Budgets:** B = f × 71,629.864 km for f = 1%, **5% (primary)** and 10%, i.e. 716.299, 3,581.493 and 7,162.986 km.
  - The same national B and the same eligible pool apply to every representation.
  - Accounting tolerance: |Σ x·L − B| < 1e-6 km, asserted for every allocation.
- **Partial reaches:** the first reach that would exceed B is taken pro rata (x ∈ [0, 1]). Each A1, A2 and R1 allocation has at most one partial reach; A3 has at most one per catchment.
- **Tie-breaking:** order = (descending score, then rank in a seeded permutation of reaches sorted by `fragment_id`). Seed 20261117. Catchment ties use a seeded permutation of sorted CaBA_IDs, seed 20261118.
  - Tie sensitivity: 200 replicate permutations, seeds 1–200.

| ID | Rule |
|---|---|
| **A1 reach** | Take reaches in score order until B |
| **A2 catchment** | Rank catchments by their length-weighted mean reach score (eligible reaches only) and survey whole catchments in order. The marginal catchment is filled in the seeded random reach order, ignoring score |
| **A3 stratified** | In every catchment, f × its eligible length, with reaches taken in score order inside the catchment |
| **R1 random** | Seeded random reach order until B. 1,000 replicates (seeds 10001–11000). Stratified variant: f per catchment (seeds 20001–21000) |
| **R2 woody** | A1 applied to the woody share of one arm (C, LEg or LEn) |
| **O_j** | A1 on scenario j's own score. This is the exact optimum of the fractional-budget problem: a linear programme with one length constraint, so greedy by score per km is optimal (unit-tested against an LP solver). It is a model-based ceiling, not ecological truth |

## 7. Evaluation metrics

Notation: L_r is the length of reach r; x and y are allocations (the selected fraction of each reach); s_j is scenario j's score (with F-Z applied); f is the budget fraction.

- **Value.** V_j(x) = Σ x_r · L_r · s_rj.
- **Random expectation.** E_j = f · Σ L_r · s_rj.
- **Capture.** C_{i→j} = [V_j(S_i) − E_j] / [V_j(O_j) − E_j].
  - Capture is undefined (reported as NaN) if V_j(O_j) − E_j < 1e-9.
  - It may be negative (worse than random), which gives a normalised regret above 1.
- **Normalised regret.** 1 − C_{i→j}. This is the primary measure and is reported **off-diagonal** for A1 allocations.
- **Alternative normalisations.**
  - Proportional regret: 1 − V_j(S_i) / V_j(O_j).
  - Absolute regret: V_j(O_j) − V_j(S_i), in score-weighted km.
- **Overlap.** I = Σ min(x, y) · L.
  - Replaced fraction = 1 − I/B.
  - Jaccard = I / (2B − I).
- **Catchment redistribution** = ½ Σ_c |km_x(c) − km_y(c)| / B: the share of the budget that sits in different catchments.
- **Concentration:** top-5 catchment share, effective number of catchments exp(H), Gini coefficient, and number of catchments receiving any effort.
- **Robust core:** Σ min over the 4 core A1 allocations of x·L, as a share of B. Also reported: the number of catchments holding 50% of the core.
- **Rank agreement** between scenarios:
  - reach level: Spearman ρ and Kendall τ_b (unweighted);
  - catchment level: Spearman ρ of catchment means, and overlap of the top 10 catchments.
- **Factor contrasts** (mean replaced fraction over pairs that differ in one factor only):
  - D_R = mean[(C-lo, LEg-lo), (C-hi, LEg-hi)];
  - D_A = mean[(C-lo, C-hi), (LEg-lo, LEg-hi)];
  - interaction R×A = D_R(lo) − D_R(hi);
  - D_G = mean[(LEn-e, LEg-e)];
  - D_RN = mean[(C-e, LEn-e)];
  - grain-persistence share = D_R / D_RN.
  - These are computed for A1, A2 and A3. Rank distances are not a variance decomposition and are not presented as one.

## 8. Descriptive representation reporting (D-3)

- **Pooled pixels.** Pixel statistics use the union of all eligible 40 m buffers, counting each pixel once. Each pixel takes the catchment of the CaBA polygon that contains it.
- **What is reported:**
  - category agreement and κ for C–LEn, C–LEg and LEn–LEg;
  - woody share;
  - the grain partition (AGREE_NATIVE, GRAIN_RESOLVED, GRAIN_INTRODUCED, RESID_STRUCTURAL, RESID_OTHER) and the net share explained by the grain control, as defined in the P2-C2 evaluation;
  - interval-category land share and interval width;
  - water sub-types (geometric rule of P2-C2);
  - R-W flags (water fraction > 0.75) against the 2% trigger;
  - zero-land length and unknown share.
- **Reach and catchment level:** length-weighted reach statistics, score distributions, and the between-catchment share of reach-score variance (length-weighted one-way decomposition) are reported nationally and by catchment.
- **Interpretation:** unattributed disagreement is reported as mapping disagreement. It is not ecological variation.

## 9. Null and reference models

| Null | Construction | Question |
|---|---|---|
| Random R1 | above | Overlap and capture with no information (expected replaced fraction about 1 − f) |
| Rank-copula | For a pair of scenarios, draw synthetic scores with the same marginals and the observed reach-level Spearman ρ (Gaussian copula), then apply A1 to both. 200 replicates (seeds 30001–30200) | How much turnover the observed rank correlation alone implies (arithmetic of top-f selection) |
| Within-catchment shuffle | Permute scenario j's scores among reaches of the same catchment, apply A1, and evaluate under the true s_j. 200 replicates (seeds 40001–40200) | Capture available from catchment-level information alone. This is the ceiling of what a catchment-level description can carry |
| Within-10 km-cell shuffle | As above, but within 10 km grid cells (reach midpoint). Seeds 50001–50200 | Capture carried by structure coarser than 10 km |
| Global shuffle | Permute all scores, apply A1, measure concentration. Seeds 60001–60200 | Concentration expected with no spatial structure |
| Tie-breaking | 200 permutations | Share of each allocation fixed only by ties |

## 10. Statistical design

- **What the data are.** The reaches and catchments are a complete census, and the maps are deterministic. Intervals therefore express **sensitivity**, not sampling error. No p-values are produced.
- **Spatial block resampling.** Catchments are resampled with replacement, B = 1,000, seeds 70001–71000. In each replicate the budget is recomputed (f × resampled length) and the core and diagnostic A1 allocations are recomputed. Headline metrics are reported as the 2.5–97.5 percentile interval, labelled "descriptive: sensitivity to catchment composition".
  - Companion check: leave-one-catchment-out jackknife (105).
- **Spatial dependence.** A distance-band correlogram of reach scores (Moran's I over sampled reach-midpoint pairs; bands 0–1, 1–2, 2–5, 5–10, 10–20, 20–50 and 50–100 km; 2 million pairs, seed 80001).
  - The correlation length is the upper edge of the first band with I < 0.1.
  - Effective number of independent stretches = eligible length ÷ correlation length.
  - Reaches are never treated as independent replicates.
- **Materiality.** A contrast is "material" if its replaced fraction is ≥ 0.10 at the 5% budget. Sensitivity thresholds are 0.05 and 0.20. Aggregation loss is "material" if capture ≤ 0.80 (sensitivity 0.60 and 0.90). These are descriptive conventions; continuous values are always shown.

## 11. Robustness set (fixed; no additions after results)

- Budgets: 1, 5 and 10%.
- Endpoints: A-lo and A-hi.
- Buffers: 20 and 100 m.
- Segmentation: 1 km and 500 m.
- Unknown: conditional.
- Zero land: F-Z exclusion.
- S-C2: drop the 4 partial-coverage catchments, re-basing B.
- S-W4: drop R-W-flagged reaches jointly, only if the 2% trigger is reached nationally.
- Ties: tie-breaking replicates.
- Regret: the alternative normalisations.

## 12. Hypotheses (from `P2B_HYPOTHESIS_REGISTER.csv`, reduced to the 4-scenario design)

| ID | Contrast (5% budget, A1 unless stated) | Support | Non-support | Status |
|---|---|---|---|---|
| H1 | A2 vs A1 (and A3) under C-lo and LEg-lo | Capture(A2) ≤ 0.80 in both, **and** regret(A2) > regret(A3) | Otherwise | Tested |
| H2 (K removed) | D_R vs D_A | D_R ≥ 0.10 **and** D_R > D_A | D_R < 0.10, or D_R ≤ D_A | Tested. The original "max(D_K, D_A)" becomes D_A because K2 is excluded (D-1) |
| H2b | D_R / D_RN | ≥ 0.5: the representation effect is mainly thematic; < 0.5: mainly grain | — | Tested; descriptive |
| H3 | D_R under A2 vs A1 | D_R(A2) ≤ 0.75 · D_R(A1) | D_R(A2) ≥ 0.75 · D_R(A1); amplification reported if D_R(A2) > D_R(A1) | Tested |
| H4 | Robust core of the 4 core A1 allocations | Core ≥ 25% of B **and** ≥ 10 catchments hold 50% of the core | Core < 10% of B, or the core is concentrated in < 5 catchments | Tested. 4 scenarios instead of 8 make the core criterion easier to meet; this is stated with the result. Rank-copula core used as the reference |
| H5 | Legacy weights | — | — | **Not tested.** It needs a gradient-weighted index, which is outside the 4-scenario K1 design (gradient excluded from the score) |
| H6 | Eligibility rule | — | — | **Not tested.** It needs overlays outside the eligible population, which this authorisation does not cover |
| H7 | Otter signs | — | — | **Not tested.** Conditional; no territory labels reconstructed |

## 13. Interpretation limits

- All results are **model-based decision sensitivity** under declared assumptions.
- Regret is relative to a scenario's own score. It is not ecological loss, and capture is not habitat quality.
- C vs LEg is representation at a common grain, still confounded with date (2018 vs 2019–21), production method and error. C vs LEn adds grain.
- Neither map is ground truth, and agreement is not validation.
- Larger disagreement does not mean greater ecological importance.
- The damaged-CORINE legacy results are not used.

## 14. Numerical tolerances and amendments

| Quantity | Tolerance |
|---|---|
| Length reconciliation | 1e-6 km national; 1e-6 km per catchment |
| Budget accounting | 1e-6 km |
| Capture of O_j | 1 within 1e-9 |
| Seeded reruns | Identical |

Amendments: none.
