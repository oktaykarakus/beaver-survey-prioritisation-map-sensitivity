# P2-C2 — Pilot catchment selection (recorded before any overlay)

**Written for:** the project lead and later reviewers who need to confirm that the pilot catchment was chosen without reference to the result.

**Timestamp:** 2026-11-08T10:31Z. At this time no Living England raster, no CORINE raster and no source-to-source comparison existed in `05_Experiments/BHSI_v2_P2C/c2/`. The directory held only the two selection files listed under *Provenance*.

## Decision

**Pilot catchment: Derbyshire Derwent (CaBA_ID 19).** It was chosen by a rule fixed in advance (the header of `p2c2_01_select_pilot.py`), not by inspection of results.

## The rule

The rule used only the P2-C1 eligibility table, catchment area, the P2-B Living England **coverage** tables, and CORINE-only categories at eligible river midpoints. It read no Living England class and made no comparison between the sources.

| Filter | Criterion | Why |
|---|---|---|
| H1 | P2-C1 status `ELIGIBLE` (reportable, not flagged partial) | eligibility is settled |
| H2 | no Welsh length; outside-England/Wales ≤1% and England tidal ≤1% of the network; eligible share ≥90% | no unresolved tidal or geographic ambiguity |
| H3 | eligible length 600–1,600 km | substantial but manageable |
| H4 | catchment area ≤2,500 km² | raster size |
| H5 | Living England no-segment share ≤0.5% (random points and river midpoints); CORINE no-match 0 | reliable coverage in both sources |
| H6 | CORINE riparian midpoint shares ≥5% each for woodland (BLW+CON+SCR), grassland (GRS), agriculture (ARB+AGM) | woodland, agricultural and grassland variation |
| Choice | highest Shannon diversity of CORINE model categories (length-weighted, water excluded) among survivors | a CORINE-only quantity; cannot favour a large source difference |

## Result

101 of 107 catchments pass H1. Five pass H1–H5, and four pass all filters:

| Catchment | Eligible km | Share | Area km² | Woody % | Grass % | Agri % | Shannon (CORINE) |
|---|---|---|---|---|---|---|---|
| **Derbyshire Derwent (19)** | 750.0 | 91.5 | 1,445 | 13.3 | 39.4 | 17.4 | **1.834** |
| Yorkshire Derwent (109) | 1,366.1 | 98.4 | 2,066 | 14.6 | 28.1 | 47.9 | 1.482 |
| Hampshire Avon (31) | 697.7 | 96.3 | 1,748 | 8.7 | 59.1 | 21.9 | 1.328 |
| Dove (23) | 659.5 | 93.5 | 1,019 | 8.0 | 72.9 | 11.1 | 1.012 |

Soar (72) passed H1–H5 and failed H6 (0.6% woody). The full 107-row evaluation is in `pilot_selection_candidates_all107.csv`.

## What this choice does and does not support

- **Representativeness.** The H1–H5 filters leave a small, non-random set (five catchments). The pilot tests whether the method works and what it costs. It is not a national sample and its differences cannot be extrapolated.
- **Missing conditions.** The catchment is inland and contains no estuary or tidal water, so the coastal/tidal water handling is untested in the pilot. The CORINE-based diversity criterion favours catchments with many CORINE categories, so it may under-represent catchments dominated by one category.
- **Upland-to-lowland gradient.** Derbyshire Derwent runs from Peak District moorland to the Trent confluence. That is useful for bracken, heath and grassland ambiguity. It also includes urban areas (Derby, Matlock), so urban-fringe classes will be present.
- **Runner-up** (Yorkshire Derwent) is reserved. It would be used only if the pilot catchment failed for a technical reason, and any such switch would be recorded.

## Provenance

| File | sha256 |
|---|---|
| `05_Experiments/BHSI_v2_P2C/c2/pilot_selection.json` | bc1c08facec843b12ed37520de25267a973df7d11642214b215299e521d99a5c |
| `05_Experiments/BHSI_v2_P2C/c2/pilot_selection_candidates_all107.csv` | f3fdac4c678e8b0120b4554df9425dc6b300a06ee9fdf8210d2b0e40ed23c281 |
| `04_BHSI_v2_Development/p2c/p2c2_01_select_pilot.py` | 5fe6daf702b65a9310cb4a5be5ae554831bfc7956125e8760b526619cb22fd7b |

The overlay script (`p2c2_02_overlay.py`) refuses to run unless this file exists, and it records this file's hash in its own outputs.
