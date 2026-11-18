# Repository manifest

Every file in this repository, with its purpose. 210 files, 173 MB in total.
The SHA-256 prefixes (first 16 hex digits) identify the exact file versions.

Two files exceed GitHub's 25 MB browser-upload limit but are below the 100 MB push limit: the eligible network and the river-pieces GeoPackage. Push them with git; the GitHub browser upload rejects files over 25 MB.


## (repository root)

| File | Size | SHA-256 (prefix) | Purpose |
|---|---|---|---|
| `.gitignore` | 959 B | `27fe5b2f81a4e4f5` | Excludes caches, temporary files, raw third-party data, credentials and non-public inputs |

## 01_BHSI_v1_Frozen

| File | Size | SHA-256 (prefix) | Purpose |
|---|---|---|---|
| `01_BHSI_v1_Frozen/source_snapshot/data/Beavers/Wild_Beaver_Catchments_England_-2509696373757772249.geojson` | 3.1 MB | `0275113e0bc83c1d` | Source data (OGL v3.0, unmodified): Natural England CaBA partnership boundaries, 107 polygons |

## 04_BHSI_v2_Development

| File | Size | SHA-256 (prefix) | Purpose |
|---|---|---|---|
| `04_BHSI_v2_Development/p2a/p2a_01_download_eea_clc2018.py` | 3.5 kB | `29cdb17132bcc171` | Level D: download CORINE Land Cover 2018 polygons from the EEA public ArcGIS service |
| `04_BHSI_v2_Development/p2a/p2a_02_assemble_recovered.py` | 1.5 kB | `db7b5c323669b318` | Level D: assemble downloaded CORINE pages into clc2018_eea_recovered_3035.gpkg |
| `04_BHSI_v2_Development/p2b/p2b_01_point_sampling.py` | 5.5 kB | `5e139c81eea92bd0` | Level E: point-sample CORINE and Living England classes (crosswalk evidence) |
| `04_BHSI_v2_Development/p2b/p2b_03_summarise_sampling_and_network.py` | 6.4 kB | `bc6951047f87b591` | Level E: summarise point samples and network form by catchment (crosswalk evidence) |
| `04_BHSI_v2_Development/p2b/p2b_04_build_crosswalk.py` | 15.0 kB | `ffb78ad71ee5f54e` | Level E: build the ecological crosswalk table P2B_ECOLOGICAL_CROSSWALK.csv |
| `04_BHSI_v2_Development/p2c/p2c2_00_write_class_table.py` | 582 B | `2613a08f522a3c26` | Writes the frozen class-treatment table from the crosswalk |
| `04_BHSI_v2_Development/p2c/p2c2_01_select_pilot.py` | 6.1 kB | `5fe6daf702b65a93` | Level E: pre-registered pilot catchment selection (P2-C2) |
| `04_BHSI_v2_Development/p2c/p2c2_02_overlay.py` | 21.1 kB | `4a7d498f0b1817ff` | Level E: single-catchment pilot overlay (incl. grain control applied to CORINE) |
| `04_BHSI_v2_Development/p2c/p2c_01_eligible_network.py` | 18.9 kB | `3e97881ed23b5daf` | Level E: build the eligible / excluded river network (P2-C1) |
| `04_BHSI_v2_Development/p2c/p2c_lc.py` | 7.6 kB | `a9da7bf4d787b83d` | Library: crosswalk class table, forage levels, 10 m rasterisation, grain control (opening + sieve), composition |
| `04_BHSI_v2_Development/p2c/p2c_net.py` | 4.5 kB | `714ddc3d9b69e326` | Library: eligibility rules (country split, OS form, catchment minimum) and reason codes |
| `04_BHSI_v2_Development/p2c/test_p2c1.py` | 6.5 kB | `55ee187d4a0ecdb0` | Unit tests for the eligibility library |
| `04_BHSI_v2_Development/p2c/test_p2c2.py` | 8.4 kB | `2f6efbb33f388840` | Unit tests for rasterisation and grain control |
| `04_BHSI_v2_Development/p2c3/p2c3_00_select_preflight.py` | 3.1 kB | `2c5f630cc0738d43` | Preflight catchment selection (geometric criteria) |
| `04_BHSI_v2_Development/p2c3/p2c3_01_run_overlay.py` | 4.2 kB | `3a97ba05c7f11b21` | Level D driver: tile plan, tiled national overlay, catchment runs, determinism rerun |
| `04_BHSI_v2_Development/p2c3/p2c3_02_preflight_checks.py` | 11.3 kB | `2a2e6c0b71d144c0` | Preflight checks: tiled vs untiled, pilot reproduction, raster vs exact vector overlay |
| `04_BHSI_v2_Development/p2c3/p2c3_03_assemble.py` | 6.7 kB | `8e53f2ca63adc4ef` | Level C: assemble reach/unit tables and pooled pixels from tile outputs, with checks |
| `04_BHSI_v2_Development/p2c3/p2c3_04_representation.py` | 10.6 kB | `23b1f18a6ed4b40a` | Level B: map agreement, kappa, composition, grain-disagreement partition, rank agreement |
| `04_BHSI_v2_Development/p2c3/p2c3_05_allocation.py` | 21.0 kB | `233eaebdaf1bd6cb` | Level B: allocations, turnover, regret, references, bootstrap/jackknife, correlogram, robustness |
| `04_BHSI_v2_Development/p2c3/p2c3_05b_core_reference.py` | 1.9 kB | `3eade658cf1f23f5` | Level B: rank-copula reference for the common priority core |
| `04_BHSI_v2_Development/p2c3/p2c3_07_verify.py` | 6.2 kB | `e20e9613740fcd80` | Level B: independent post-run verification checks |
| `04_BHSI_v2_Development/p2c3/p2c3_alloc.py` | 4.7 kB | `2faf517d23af9871` | Library: allocation strategies (A1 reach, A2 catchment, A3 stratified), value, capture, regret, replaced fraction |
| `04_BHSI_v2_Development/p2c3/p2c3_overlay.py` | 14.8 kB | `05e90b4cae387a27` | Library: national overlay per domain (tile/catchment), unit buffers, pooled pixel histograms |
| `04_BHSI_v2_Development/p2c3/p2c3_scores.py` | 2.7 kB | `4577a6ce6c647066` | Library: reach composition and lo/hi forage scores from pixel counts |
| `04_BHSI_v2_Development/p2c3/test_p2c3_alloc.py` | 5.2 kB | `6c64880d6e46f810` | Library: allocation strategies (A1 reach, A2 catchment, A3 stratified), value, capture, regret, replaced fraction |
| `04_BHSI_v2_Development/p2c3/test_p2c3_overlay.py` | 3.0 kB | `23fbfba3a39bd29c` | Library: national overlay per domain (tile/catchment), unit buffers, pooled pixel histograms |
| `04_BHSI_v2_Development/p2d/p2d_02_grain_continuation.py` | 2.0 kB | `86e5cb470ffaed65` | Level D: grain-control continuation for the 6 tiles that reached the 5-cycle cap |
| `04_BHSI_v2_Development/p2d/p2d_03_grain_effect.py` | 5.4 kB | `13c29cfcc58963df` | Level B: effect of the continuation on scores and decision metrics |
| `04_BHSI_v2_Development/phase1/build_native_candidate.py` | 6.5 kB | `a741fba042a39e78` | Level E: river pieces = OS Open Rivers links clipped to the 107 CaBA catchments; channel gradient |
| `04_BHSI_v2_Development/phase1/geometry.py` | 1.7 kB | `42889a217a86b535` | Level E library: canonical clipping of river links to catchments |
| `04_BHSI_v2_Development/phase1/indicators.py` | 3.5 kB | `fb76eb22631ee216` | Level E library: earlier-index scoring helpers used by the piece builder (gradient, CORINE accounting) |
| `04_BHSI_v2_Development/phase1/protocol_lock.json` | 2.5 kB | `de93e7308b2a09ed` | Level E configuration read by build_native_candidate.py (buffer width, model weights) |
| `04_BHSI_v2_Development/phase1/test_indicators.py` | 4.6 kB | `a3b7d12edaa7fa96` | Unit tests for phase1/indicators.py |

## 05_Experiments

| File | Size | SHA-256 (prefix) | Purpose |
|---|---|---|---|
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_catchment_eligibility.csv` | 19.5 kB | `97503233b5db3489` | Derived: per-catchment eligible length, reportability, partial-coverage flags |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_checks.csv` | 1.4 kB | `4a9a3bde622062f7` | Derived: P2-C1 checks, summary and reconciliation |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_content_hash.txt` | 65 B | `79744a9a865b0b5e` | Derived: P2-C1 checks, summary and reconciliation |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_cross_border_focus.csv` | 759 B | `0eb950daabf176ce` | Derived: P2-C1 checks, summary and reconciliation |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_eligible_network.gpkg` | 36.6 MB | `7a8beaa04483d3ad` | Derived: eligible river network, 76,082 reaches (71,629.9 km) |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_excluded_network.gpkg` | 10.8 MB | `d7cdca002be47afd` | Derived: excluded river fragments with exclusion reasons |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_exclusion_reason_register.csv` | 500 B | `90390e66b7a4ecdf` | Derived: excluded length by reason (Wales, seaward, tidal, canal, lake, catchment minimum) |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_inherited_overlaps.csv` | 5.1 kB | `5ac42489e74d4271` | Derived: collinear duplicate segments inherited from the source network |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_length_reconciliation.csv` | 1.5 kB | `8eb07891b698c56a` | Derived: P2-C1 checks, summary and reconciliation |
| `05_Experiments/BHSI_v2_P2C/c1/p2c1_summary.json` | 1.7 kB | `03e89f9e9607109c` | Derived: P2-C1 checks, summary and reconciliation |
| `05_Experiments/BHSI_v2_P2C/c2/P2C2_LANDCOVER_COMPARISON.csv` | 9.3 kB | `f3d7207ec415e505` | Derived: P2-C2 pilot land-cover comparison (CORINE, LE-N, LE-G); read by the pilot tests |
| `05_Experiments/BHSI_v2_P2C/c2/class_treatment_table_FROZEN.csv` | 3.8 kB | `c44dcdac74abb640` | Derived (definition): frozen class -> category -> lo/hi forage value table used by the overlay |
| `05_Experiments/BHSI_v2_P2C/c2/confusion_C_LEg_buffer_union.csv` | 919 B | `9eadb721851d98a4` | Derived: P2-C2 pilot category confusion table over the buffer union; read by the pilot tests |
| `05_Experiments/BHSI_v2_P2C/c2/confusion_C_LEn_buffer_union.csv` | 966 B | `d7bfec9e9a4818f4` | Derived: P2-C2 pilot category confusion table over the buffer union; read by the pilot tests |
| `05_Experiments/BHSI_v2_P2C/c2/pilot_reach_table.csv` | 302.3 kB | `44798445c835da6a` | Derived: P2-C2 pilot selection, summary and reach table (used by preflight checks) |
| `05_Experiments/BHSI_v2_P2C/c2/pilot_selection.json` | 984 B | `bc1c08facec843b1` | Derived: P2-C2 pilot selection, summary and reach table (used by preflight checks) |
| `05_Experiments/BHSI_v2_P2C/c2/pilot_summary.json` | 7.1 kB | `7f7b6c00af73986e` | Derived: P2-C2 pilot selection, summary and reach table (used by preflight checks) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/alloc_summary.json` | 16.8 kB | `a1c093d98fa67851` | Result: turnover, persistence, core, bootstrap and budget summaries (Tables 2-3) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/allocations_primary_5pct.npz` | 636.0 kB | `df8ebc9adcbd3d37` | Result: 5% allocation vectors per scenario (Fig. 3) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/catchment_bootstrap_5pct.csv` | 251.0 kB | `a6ce7feacb22168f` | Result: 1,000 catchment-bootstrap replicates of headline metrics |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/core_reference.json` | 743 B | `68f91986c1ea4418` | Result: allocation analysis outputs (references, robustness, materiality, per-catchment km) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/jackknife_5pct.csv` | 26.8 kB | `4999b668848359b5` | Result: leave-one-catchment-out jackknife |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/materiality.csv` | 1.4 kB | `dacf1e964d2d0127` | Result: allocation analysis outputs (references, robustness, materiality, per-catchment km) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/nulls_5pct.json` | 5.7 kB | `b90672139a44ad31` | Result: allocation analysis outputs (references, robustness, materiality, per-catchment km) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/replaced_fraction_matrix_5pct.csv` | 795 B | `5cd4fee072350570` | Result: allocation analysis outputs (references, robustness, materiality, per-catchment km) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/robustness_5pct.csv` | 1.6 kB | `5315493755505aad` | Result: allocation analysis outputs (references, robustness, materiality, per-catchment km) |
| `05_Experiments/BHSI_v2_P2C3/analysis/alloc/selected_km_by_catchment.csv` | 165.6 kB | `224e6075c493e6e9` | Result: allocation analysis outputs (references, robustness, materiality, per-catchment km) |
| `05_Experiments/BHSI_v2_P2C3/analysis/assemble_checks.json` | 913 B | `56c61487380be560` | Derived: assembly completeness and conservation checks |
| `05_Experiments/BHSI_v2_P2C3/analysis/pooled.npz` | 123.8 kB | `67a04915784681d1` | Derived: pooled pixel category triples (each pixel once) by catchment |
| `05_Experiments/BHSI_v2_P2C3/analysis/reach_table_B40.parquet` | 13.6 MB | `47d7792ca897362b` | Derived: reach-level composition, scores, woody share, agreement counts (primary 40 m buffer) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/catchment_mean_scores.csv` | 7.8 kB | `fdfb1f20b8286b7d` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/catchment_representation.csv` | 21.6 kB | `9aac8cedcf35aac5` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/category_correspondence_national.csv` | 1.3 kB | `d49c59905bd3a5c3` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/confusion_national_C_LEg.csv` | 1.2 kB | `d4187b9f70fb5883` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/confusion_national_C_LEn.csv` | 1.3 kB | `5f36926fa7ec0a86` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/confusion_national_LEn_LEg.csv` | 1.2 kB | `0ec68f4996f48541` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/rank_agreement.csv` | 1.4 kB | `2ffb97ba0395a93c` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/rep_summary.json` | 10.0 kB | `bd6d1c2c665dd009` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/residual_other_top_pairs_national.csv` | 182 B | `4372334cdcb0364d` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/rep/water_subtypes_national.csv` | 350 B | `30091461756f1756` | Result: representation analysis (agreement, confusion, partition, rank agreement) |
| `05_Experiments/BHSI_v2_P2C3/analysis/units_B100.parquet` | 6.8 MB | `16ba9e939bbcd637` | Derived: unit tables for robustness variants (20 m, 100 m buffers; 1 km, 500 m segments) |
| `05_Experiments/BHSI_v2_P2C3/analysis/units_B20.parquet` | 5.4 MB | `a9fa06acfb481ea2` | Derived: unit tables for robustness variants (20 m, 100 m buffers; 1 km, 500 m segments) |
| `05_Experiments/BHSI_v2_P2C3/analysis/units_S1000.parquet` | 7.9 MB | `4ce3584866b09d0a` | Derived: unit tables for robustness variants (20 m, 100 m buffers; 1 km, 500 m segments) |
| `05_Experiments/BHSI_v2_P2C3/analysis/units_S500.parquet` | 9.7 MB | `73042193184d1ba0` | Derived: unit tables for robustness variants (20 m, 100 m buffers; 1 km, 500 m segments) |
| `05_Experiments/BHSI_v2_P2C3/overlay/reach_tile_assignment.csv` | 4.2 MB | `a6af4417c4606d29` | Derived: tile assignment of every eligible reach |
| `05_Experiments/BHSI_v2_P2C3/overlay/tile_plan.csv` | 7.0 kB | `afc294ab34f1b4de` | Derived: 78 national 50 km tiles with margins |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t002_000.npz` | 33.9 kB | `f7eaf785364fc527` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t003_000.npz` | 112.6 kB | `b989931057219c69` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t003_001.npz` | 77.0 kB | `4b1758df0e05d326` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t004_000.npz` | 22.4 kB | `ce507669baaa9393` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t004_001.npz` | 331.9 kB | `6902b6a04d1453e5` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t004_002.npz` | 128.1 kB | `da24f8f85223874e` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t005_000.npz` | 50.0 kB | `56007d804222e432` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t005_001.npz` | 369.4 kB | `6e1dc4c942c22577` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t005_002.npz` | 353.9 kB | `238b4a48a705dcbd` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t005_010.npz` | 24.2 kB | `89297e6b12d088dc` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_001.npz` | 106.4 kB | `b29869532a9e9c13` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_002.npz` | 319.9 kB | `0fa211853c15542b` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_003.npz` | 51.3 kB | `1bfda1c7a48b3071` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_004.npz` | 106.2 kB | `0381120aaee261c1` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_005.npz` | 203.1 kB | `b125460f732a3a2c` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_006.npz` | 179.6 kB | `6c05a3eaf0fce282` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_007.npz` | 103.6 kB | `4e17cdbae75811ad` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_008.npz` | 198.2 kB | `cc19c9e802b1fb01` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_009.npz` | 250.8 kB | `6b6fdb8f60e866d0` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_010.npz` | 397.0 kB | `51802d285d9d2616` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t006_011.npz` | 152.3 kB | `c6d7506929d4d150` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_001.npz` | 141.4 kB | `5357eb1318775b36` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_002.npz` | 210.7 kB | `39eb5c682f3504e4` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_003.npz` | 209.0 kB | `681303889bf3a3d4` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_004.npz` | 256.9 kB | `5918a81794b634ab` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_005.npz` | 262.1 kB | `9df616b14a16fbb6` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_006.npz` | 254.6 kB | `008ae026be59e642` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_007.npz` | 307.8 kB | `004e7e6b23a2fd24` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_008.npz` | 440.7 kB | `b0af61a0bdbd41b7` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_009.npz` | 437.9 kB | `dc82553dc429d843` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_010.npz` | 443.2 kB | `7d74ed2b1c824eb0` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_011.npz` | 417.0 kB | `6684f2f0d4e9edf0` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_012.npz` | 141.8 kB | `cc7fb76127985254` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t007_013.npz` | 17.5 kB | `26823c292bb3961d` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_001.npz` | 95.3 kB | `13bcc9ad8a406904` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_002.npz` | 319.1 kB | `30e564afe34c5dd9` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_003.npz` | 224.0 kB | `09f09f9813f5c372` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_004.npz` | 238.7 kB | `698d5c60befce32b` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_005.npz` | 239.5 kB | `fbc008b973d2c62a` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_006.npz` | 290.4 kB | `d0a28372f3d870ee` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_007.npz` | 309.3 kB | `752ab52fc8a9b618` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_008.npz` | 344.2 kB | `d18d744a966bf087` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_009.npz` | 334.1 kB | `4831ebe452bb8897` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_010.npz` | 267.3 kB | `fd4541ba3c8f5ee7` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_011.npz` | 174.0 kB | `47b38c01d964fe4f` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t008_012.npz` | 122.6 kB | `6eb26bec4f6df729` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_001.npz` | 53.4 kB | `d40dcba6e85afedc` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_002.npz` | 223.4 kB | `66859839cdc0157c` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_003.npz` | 298.4 kB | `333c93075fa3cc64` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_004.npz` | 235.2 kB | `6bf42a5a7e6bb845` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_005.npz` | 202.4 kB | `6aec0b73c5bedf59` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_006.npz` | 203.7 kB | `148344e21c79517b` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_007.npz` | 219.4 kB | `46e7eed9f7779bf6` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_008.npz` | 255.5 kB | `14b5c3d5cfbc4466` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_009.npz` | 282.0 kB | `0ae808f29502a2a4` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t009_010.npz` | 159.8 kB | `04b6c34e6db04893` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_002.npz` | 329.4 kB | `12d14a4c38503c01` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_003.npz` | 230.5 kB | `6f7b07edf5d4d5f6` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_004.npz` | 232.8 kB | `f72db74b656dede4` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_005.npz` | 224.4 kB | `ef27428fa1fd8c35` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_006.npz` | 136.0 kB | `fbcfa540fcebea01` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_007.npz` | 207.6 kB | `50b25842abbea0c7` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_008.npz` | 129.5 kB | `b38e5ce59a61078f` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t010_009.npz` | 62.7 kB | `16ccbe492ba30221` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t011_001.npz` | 18.9 kB | `abfc0f5320aa4160` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t011_002.npz` | 307.1 kB | `d24ae368963a5106` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t011_003.npz` | 178.7 kB | `5498eef74eaa498f` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t011_004.npz` | 234.5 kB | `9aee267668759656` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t011_005.npz` | 160.5 kB | `80d7e7fffc4bcb41` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t011_006.npz` | 146.0 kB | `404394f9a606212a` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t011_007.npz` | 26.2 kB | `29954999b26fb9de` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t012_002.npz` | 57.5 kB | `af831d46ccc2cf09` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t012_003.npz` | 69.1 kB | `21185ec63b0bac6b` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t012_004.npz` | 120.7 kB | `c52af0fdf218f327` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t012_005.npz` | 248.8 kB | `0206ca32cafc66ff` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t012_006.npz` | 199.8 kB | `a52ebae63ce4d2d3` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t013_005.npz` | 30.3 kB | `b52ec5191725e328` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/overlay/tiles/t013_006.npz` | 17.3 kB | `ad056091d9a68d86` | Derived: per-tile overlay output (pixel counts per unit and arm, pooled histograms, grain-control log) |
| `05_Experiments/BHSI_v2_P2C3/preflight/catchment_107.npz` | 246.8 kB | `f9d305de3395e5c6` | Derived: untiled preflight catchment overlay outputs |
| `05_Experiments/BHSI_v2_P2C3/preflight/catchment_13.npz` | 312.5 kB | `11de41eb212e8fb8` | Derived: untiled preflight catchment overlay outputs |
| `05_Experiments/BHSI_v2_P2C3/preflight/catchment_19.npz` | 172.4 kB | `41caf7a0bb104cf1` | Derived: untiled preflight catchment overlay outputs |
| `05_Experiments/BHSI_v2_P2C3/preflight/catchment_99.npz` | 123.8 kB | `dcf49dc08cfb8885` | Derived: untiled preflight catchment overlay outputs |
| `05_Experiments/BHSI_v2_P2C3/preflight/preflight_checks.json` | 17.4 kB | `4e1234d6854c26b8` | Result: preflight selection and checks |
| `05_Experiments/BHSI_v2_P2C3/preflight/preflight_selection.json` | 708 B | `5915aeee6ed389b4` | Result: preflight selection and checks |
| `05_Experiments/BHSI_v2_P2C3/preflight/preflight_selection_candidates.csv` | 4.6 kB | `362f52bcf41f75ae` | Result: preflight selection and checks |
| `05_Experiments/BHSI_v2_P2C3/preflight/preflight_vector_check.csv` | 55.2 kB | `a41c53e6e2c1d6e6` | Result: preflight selection and checks |
| `05_Experiments/BHSI_v2_P2C3/verification/allocation_rerun_determinism.txt` | 480 B | `9b3291eb5ccc8e33` | Result: post-run verification (independent regret recomputation, determinism) |
| `05_Experiments/BHSI_v2_P2C3/verification/independent_regret_recomputation.csv` | 1.3 kB | `07505f76f0556621` | Result: post-run verification (independent regret recomputation, determinism) |
| `05_Experiments/BHSI_v2_P2C3/verification/post_run_checks.json` | 927 B | `751d9c9379d0f7f7` | Result: post-run verification (independent regret recomputation, determinism) |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/grain_effect.json` | 6.1 kB | `40b86b1ae2ddc965` | Result: effect of grain-control continuation on scores and metrics |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/reach_score_changes.csv` | 387.3 kB | `b84a479f8f91f2aa` | Result: effect of grain-control continuation on scores and metrics |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/t005_000.npz` | 50.0 kB | `624725109b896742` | Derived: continued grain control for one capped tile |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/t005_002.npz` | 353.9 kB | `f15a4c28071fc822` | Derived: continued grain control for one capped tile |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/t006_009.npz` | 250.9 kB | `7c448a5c10ff09e9` | Derived: continued grain control for one capped tile |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/t007_008.npz` | 440.7 kB | `f4cfe6ca0d7882c1` | Derived: continued grain control for one capped tile |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/t007_009.npz` | 437.9 kB | `569a05e5a198acd4` | Derived: continued grain control for one capped tile |
| `05_Experiments/BHSI_v2_P2D/grain_continuation/t012_004.npz` | 120.7 kB | `e0c7007b1eb5fe71` | Derived: continued grain control for one capped tile |
| `05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg` | 42.1 MB | `08391c584ed769c9` | Derived: 94,162 river pieces (OS Open Rivers clipped to catchments) with gradient; input to P2-C1 and assembly |

## 06_Results_Figures

| File | Size | SHA-256 (prefix) | Purpose |
|---|---|---|---|
| `06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv` | 17.9 kB | `097d48c9884e15b2` | Definition: ecological crosswalk (classes, categories, forage values, ambiguity, evidence) |
| `06_Results_Figures/BHSI_v2_P2C/P2C2_PILOT_SELECTION.md` | 4.0 kB | `833c855f8f97d95b` | Protocol: pilot selection rule (read by p2c2_02_overlay.py) |
| `06_Results_Figures/BHSI_v2_P2C3/P2C3_ALLOCATION_RESULTS.csv` | 7.2 kB | `49b12acaa1e08ec9` | Result: allocation summaries (concentration, catchments, turnover) |
| `06_Results_Figures/BHSI_v2_P2C3/P2C3_CROSS_SCENARIO_REGRET.csv` | 82.4 kB | `aa7cc02071605c5d` | Result: regret/capture for every allocation x evaluation scenario x budget |
| `06_Results_Figures/BHSI_v2_P2C3/P2C3_EXPERIMENTAL_FREEZE.md` | 15.0 kB | `2e7f2682c1ac17b1` | Protocol: dated analysis freeze (scenarios, budgets, metrics, seeds, tolerances) |
| `06_Results_Figures/BHSI_v2_P2C3/P2C3_PREFLIGHT_SELECTION.md` | 3.6 kB | `a0ebb03917ec85ac` | Protocol: preflight selection record |

## 07_Manuscript

| File | Size | SHA-256 (prefix) | Purpose |
|---|---|---|---|
| `07_Manuscript/Phase3_Draft/figures/Fig1_study_region_representation.pdf` | 8.6 MB | `0508295fee0c2b6e` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig1_study_region_representation.png` | 874.0 kB | `2c8ec39cf80a7883` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig2_grain_control.pdf` | 41.3 kB | `60ad14c50cab48ed` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig2_grain_control.png` | 194.2 kB | `bc9bd1e34e672e43` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig3_spatial_redistribution.pdf` | 1.5 MB | `becdad9a5b825c05` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig3_spatial_redistribution.png` | 564.5 kB | `7df928377858fc4f` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig4_regret_matrix.pdf` | 22.0 kB | `9ab9952e22cf28dd` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig4_regret_matrix.png` | 256.9 kB | `3ec8240fb4670bc6` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig5_budget_sensitivity.pdf` | 23.7 kB | `5694702269faa98c` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/Fig5_budget_sensitivity.png` | 163.6 kB | `eea7e8496532a19e` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/FigS1_overlap_matrix.pdf` | 23.4 kB | `cb0b99e246e3c4b9` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/figures/FigS1_overlap_matrix.png` | 216.4 kB | `bb324df8791e7248` | Reference output: manuscript figure as used in the manuscript |
| `07_Manuscript/Phase3_Draft/tables/table1_crosswalk.tex` | 1.0 kB | `4842dbb73c08b0fd` | Reference output: manuscript table rows (LaTeX) |
| `07_Manuscript/Phase3_Draft/tables/table2_budgets.tex` | 660 B | `1ad36983a891b681` | Reference output: manuscript table rows (LaTeX) |
| `07_Manuscript/Phase3_Draft/tables/table3_robustness.tex` | 768 B | `e9fcdd8f5b631584` | Reference output: manuscript table rows (LaTeX) |
| `07_Manuscript/Phase3_Draft/tools/make_figures.py` | 12.7 kB | `c17d0eda0ad57bdc` | Level A: regenerate manuscript Figures 1-5 and S1 |
| `07_Manuscript/Phase3_Draft/tools/make_tables.py` | 5.2 kB | `1b4728b69924f799` | Level A: regenerate manuscript Tables 1-3 (LaTeX rows) |

## (repository root)

| File | Size | SHA-256 (prefix) | Purpose |
|---|---|---|---|
| `CITATION.cff` | 1.6 kB | `36dedf516bfd1a22` | Citation metadata (authors, title); no DOI or publication details |
| `DATA_LICENSE.md` | 2.8 kB | `069117954f6801a2` | CC BY 4.0 licence for derived data, with required upstream attributions |
| `DATA_SOURCES.md` | 7.6 kB | `c7c12aa8c30d5feb` | Third-party source datasets: provenance, licence, attribution, expected paths, checksums |
| `LICENSE` | 1.2 kB | `7b3594b90d4494ba` | MIT licence for the source code |
| `README.md` | 20.2 kB | `4ff4235edc2d4e47` | Study overview, structure, installation and reproduction workflow |
| `REPOSITORY_AUDIT.md` | 9.7 kB | `6051b24626c3ce04` | Validation checks performed on this repository and known limitations |
| `REPOSITORY_MANIFEST.md` | 38.1 kB | `` | This file |
| `requirements.txt` | 417 B | `2087124d9bca5e66` | Pinned Python package versions used for the analysis |
