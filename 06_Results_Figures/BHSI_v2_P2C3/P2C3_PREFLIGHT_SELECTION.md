# P2-C3 preflight — catchment selection rules (recorded before any preflight computation)

**Written for:** reviewers checking that the three preflight catchments were chosen by geometry alone, before any land-cover, score or allocation result was computed.

Recorded 17 Nov 2026, before `p2c3_00_select_preflight.py` was first run. The rules use only the frozen P2-C1 network, the CaBA polygons and the ONS boundary. No land cover is read.

| Slot | Purpose (brief §4) | Rule | Tie-break |
|---|---|---|---|
| P1 | Cross-border | Reportable catchment with the most **eligible** length within 1 km of the England–Wales land boundary (ONS Countries Dec 2023: England boundary ∩ Wales boundary) | lower CaBA_ID |
| P2 | Internal river/catchment boundary complexity | Among the remaining reportable catchments, the most eligible length within 100 m (the widest buffer used) of **another** CaBA polygon. These are the reaches whose buffers draw land cover from a neighbouring catchment | lower CaBA_ID |
| P3 | Coastal / estuarine edge with eligible freshwater | Among the remaining reportable catchments, the most eligible length within 1 km of an excluded fragment whose primary reason is `GEO_OUTSIDE_E_W` or `FORM_TIDAL` | lower CaBA_ID |

The pilot catchment (Derbyshire Derwent, CaBA 19) is recomputed as a fourth, reproducibility-only case, against the 8 Nov pilot outputs.

## Acceptance criteria (fixed now)

"Tiled" = the national processing unit, a 50 km core tile plus a margin of at least 3 km beyond every assigned reach buffer. "Untiled" = the P2-C2 pilot method, one domain per catchment (bounding box + 3 km).

1. **Length conservation:** per catchment, Σ reach length = P2-C1 eligible km (|Δ| < 1e-6 km). Standardised 1 km and 500 m segments sum to their parent fragment (|Δ| < 1e-6 m).
2. **Assignment:** every eligible fragment is assigned to exactly one tile; fragment ids are unique; the set equals P2-C1; CaBA_ID is unchanged.
3. **No duplicated or missing pieces:** as 2. The inherited 0.42 km eligible–eligible collinear overlap (P2-C1) is quantified with an upper bound on its allocation influence. The frozen network is not edited.
4. **Buffers at edges:** buffer pixel count per reach is identical tiled vs untiled for 100% of reaches.
5. **Composition, tiled vs untiled:** CORINE and LE-native native-class counts are identical for 100% of reaches. LE-G25 (which depends on spatial context): length-weighted mean |Δ score| ≤ 0.001 at both endpoints, and ≤ 0.5% of eligible length with |Δ score| > 0.01.
6. **Water and zero-land denominators:** water fraction and zero-land flags identical tiled vs untiled. Rule R-W flags (water fraction > 0.75) reported against the 2% trigger. LE no-coverage inside buffers (sea beyond mean high water springs, Wales) is counted as unknown under the frozen rule (P2-B §5). This is reported as a **material asymmetry** if eligible reaches whose land is more than 50% LE no-coverage exceed 2% of a catchment's eligible length.
7. **Determinism:** one tile run twice gives identical arrays (sha256).
8. **Independent checks:** exact vector overlay of the 40 m buffer for 100 seeded random reaches per catchment (CORINE and LE-native): mean absolute difference < 2% of buffer area. Derbyshire Derwent recomputed in tiled mode vs the 8 Nov pilot reach table: native land pixel counts identical; LE-G25 within criterion 5.

Any failure of 1–4, 6 (consistency part), 7 or 8, or a material asymmetry under 6, stops the work before the national run, and the problem is reported. No network repair and no protocol change is made silently.
