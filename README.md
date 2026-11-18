# Same Rivers, Different Priorities — reproducibility code and data

This repository holds the analysis code, derived data and figure/table scripts for the manuscript

> **Same Rivers, Different Priorities: How Environmental Maps Shape Conservation Decisions**
> Grace David, Oktay Karakuş and Can Eyüpoğlu

The manuscript is prepared for *Ecological Indicators*. No publication details or DOI exist yet; see [Citation](#citation).

## The study in brief

We ask how much the choice of land-cover map changes a fixed-budget river-survey prioritisation. The decisions are made with a forage-oriented indicator for the Eurasian beaver (*Castor fiber*).

- **Study population.** 76,082 eligible river reaches (71,630 km) in 105 Catchment Based Approach (CaBA) catchments in England.
- **Riparian composition.** Calculated in 40 m buffers from three representations:
  - **CORINE** Land Cover 2018;
  - native **Living England** Phase IV (**LE-N**);
  - a grain-controlled Living England (**LE-G**) generalised towards CORINE's 25 ha / ~100 m mapping grain.
- **Scoring.** Land-cover classes map to 13 ecological categories with forage values of 1.0, 0.5, 0.1 or 0. Ambiguous categories carry lower/upper (lo/hi) endpoints.
- **Allocation.** Survey budgets of 1, 5 and 10% of river length are allocated by reach-level, whole-catchment and catchment-stratified strategies.
- **Comparison.** Allocations are compared by replaced fraction (turnover), normalised cross-scenario regret, a common priority core, and robustness and reference analyses.

At the primary 5% budget, switching between CORINE and LE-G replaced 47% of selected river length. Allocations optimised under one map forfeited 29–40% of the attainable improvement above random selection when evaluated under the other. The manuscript gives the full results; this repository reproduces them.

## What you can reproduce, and what it needs

| Level | What it reproduces | Needs | Time (indicative) |
|---|---|---|---|
| **A. Tables and figures** | Manuscript Tables 1–3 and Figures 1–5, S1, from the shipped derived results | This repository only | Minutes |
| **B. Decision analysis** | All turnover, regret, robustness, reference and consensus metrics (`analysis/alloc/`, `analysis/rep/`, deliverable CSVs), from the shipped reach-level composition table | This repository only | About 10 min (allocation ~7 min) |
| **C. Assembly** | The reach-level composition and score tables, from the shipped per-tile overlay outputs | This repository only | Minutes |
| **D. National overlay** | The per-tile land-cover pixel counts (CORINE, LE-N, LE-G) from raw maps | Raw CORINE and Living England (about 7 GB; see [`DATA_SOURCES.md`](DATA_SOURCES.md)) | About 7.4 CPU-hours (78 tiles) |
| **E. Network and crosswalk construction** | The eligible river network and the ecological crosswalk evidence | Raw OS Open Rivers, ONS boundaries, OS Terrain 50, the original CORINE delivery, **and a catchment table that is not public** | See [Limitations](#limitations) |

Levels A–C run entirely from this repository. In a fresh environment built from `requirements.txt`, Levels B–C reproduced every shipped data output byte-for-byte (apart from a run-time field), and Level A reproduced the tables exactly and the figures with identical content. See [`REPOSITORY_AUDIT.md`](REPOSITORY_AUDIT.md).

## Repository structure

The folder names mirror the original research project. The code resolves every path relative to the repository root, so it runs unmodified; the analysis code is byte-identical to the version used for the manuscript.

```
04_BHSI_v2_Development/          analysis code
  phase1/   river pieces: OS Open Rivers clipped to the 107 CaBA catchments; channel gradient (Level E)
  p2a/      download of CORINE Land Cover 2018 polygons from the EEA's public service (Level D input)
  p2b/      evidence used to build the ecological crosswalk (Level E)
  p2c/      eligibility rules and eligible network (P2-C1); class table, rasterisation and grain-control library;
            single-catchment pilot (P2-C2)
  p2c3/     national overlay, assembly, scores, allocation, decision metrics, verification (P2-C3)
  p2d/      grain-control convergence continuation for the six tiles that reached the cycle cap
05_Experiments/                  derived data (inputs and outputs of the code above)
  BHSI_v2_Phase1/native_001/     river pieces with channel gradient (input to P2-C1 and to assembly)
  BHSI_v2_P2C/c1/                eligible and excluded river network, eligibility tables
  BHSI_v2_P2C/c2/                frozen class-treatment table; pilot selection and pilot reach table
  BHSI_v2_P2C3/overlay/          tile plan, reach-to-tile assignment, per-tile overlay outputs (78 .npz)
  BHSI_v2_P2C3/analysis/         reach-level composition/score tables, pooled pixels, representation and allocation results
  BHSI_v2_P2C3/preflight/        preflight catchment runs and checks
  BHSI_v2_P2C3/verification/     post-run verification outputs
  BHSI_v2_P2D/grain_continuation/ continuation tiles and their effect on scores and metrics
06_Results_Figures/              frozen definitions and deliverable result tables
  BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv     ecological crosswalk (class -> category -> forage value)
  BHSI_v2_P2C3/P2C3_EXPERIMENTAL_FREEZE.md     dated analysis protocol, fixed before national results
  BHSI_v2_P2C3/P2C3_CROSS_SCENARIO_REGRET.csv  all allocations x evaluation scenarios x budgets
  BHSI_v2_P2C3/P2C3_ALLOCATION_RESULTS.csv     allocation summaries
07_Manuscript/Phase3_Draft/
  tools/make_tables.py, tools/make_figures.py  manuscript table and figure scripts
  tables/, figures/              manuscript tables (LaTeX rows) and figures as used in the manuscript (reference copies)
01_BHSI_v1_Frozen/source_snapshot/data/Beavers/  Natural England CaBA partnership boundaries (OGL v3.0)
```

[`REPOSITORY_MANIFEST.md`](REPOSITORY_MANIFEST.md) lists every file and its purpose.

## Installation

The analysis used Python 3.12.4 on macOS (arm64).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` pins the ten third-party packages the code imports, at the versions used. All commands below run from the repository root with `python -I -B`: isolated mode, no bytecode files.

**Note on GDAL.** The original environment linked rasterio against conda-forge GDAL 3.9.1. The PyPI rasterio 1.3.10 wheel bundles GDAL 3.8.4. Levels A–C do not depend on GDAL. For Level D, byte-identity of the rasterised overlay was established only with GDAL 3.9.1.

## How the analysis works, and where in the code

1. **Environmental inputs** ([`DATA_SOURCES.md`](DATA_SOURCES.md)).
   - CORINE Land Cover 2018 (vector, version 2020_20u1) is downloaded polygon by polygon from the EEA's public ArcGIS service (`p2a/p2a_01_download_eea_clc2018.py`), then assembled (`p2a/p2a_02_assemble_recovered.py`).
   - Living England Phase IV is a direct GeoPackage download from Defra.
   - OS Open Rivers, ONS country boundaries and the CaBA partnership boundaries define the river network and its eligibility.
2. **Eligible river network** (`p2c/p2c_01_eligible_network.py`, rules in `p2c/p2c_net.py`).
   - Starting point: OS Open Rivers watercourse links clipped to the 107 CaBA catchments (`phase1/build_native_candidate.py`, `phase1/geometry.py`).
   - Pieces are cut at the England boundary (ONS, mean high water) and kept only if OS `form = inlandRiver` and the catchment holds ≥ 10 km of eligible river.
   - Result: `05_Experiments/BHSI_v2_P2C/c1/p2c1_eligible_network.gpkg` (76,082 reaches).
3. **Riparian land-cover representations** (`p2c3/p2c3_overlay.py`, using `p2c/p2c_lc.py`).
   - Both maps are rasterised on a common 10 m British National Grid (cell centres).
   - LE-G is built by per-class morphological opening (disk radius 5 px, about 110 m minimum width) with nearest-class refill. A GDAL sieve then merges 8-connected patches under 2,500 px (25 ha). The two steps repeat until under 0.01% of pixels change, to at most 5 cycles (`p2c_lc.grain_control`).
   - Pixel counts are taken in 40 m buffers (also 20 m and 100 m buffers, and 1 km and 500 m segments).
   - National processing runs in 50 km tiles with ≥ 3 km margins (`p2c3/p2c3_01_run_overlay.py`).
4. **Ecological categories and forage scores.**
   - `06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv` maps every CORINE and Living England class to one of 13 ecological categories, water or unclassified, with the evidence for each mapping.
   - `p2c/p2c_lc.py` holds the forage levels (`POINT`, `INTERVAL_CAT`, `BRACKEN`) and builds the class table (`p2c/p2c2_00_write_class_table.py` → `05_Experiments/BHSI_v2_P2C/c2/class_treatment_table_FROZEN.csv`).
   - `p2c3/p2c3_scores.py` computes the scores. Water is excluded from numerator and denominator. Unclassified cells and cells without a source polygon stay in the denominator and score 0 (lo) / 1 (hi).
5. **Survey-allocation scenarios** (`p2c3/p2c3_alloc.py`, driven by `p2c3/p2c3_05_allocation.py`).
   - Scenarios: CORINE, LE-G and LE-N, each at the lo and hi endpoints.
   - Budgets: 1, 5 and 10% of eligible length.
   - Strategies: A1 reach ranking, A2 whole catchments, A3 catchment-stratified, and a woody-share reference. Random references use seeded replicates.
6. **Decision metrics** (`p2c3/p2c3_alloc.py`, `p2c3/p2c3_05_allocation.py`, `p2c3/p2c3_05b_core_reference.py`).
   - Replaced fraction (D_R, D_A, D_G, D_RN), persistence ratio and catchment redistribution.
   - Normalised, proportional and absolute regret.
   - Common priority core.
   - Rank-copula and spatial-shuffle references.
   - Catchment bootstrap (1,000) and leave-one-out jackknife.
   - Correlogram.
   - Robustness variants: buffer width, segmentation, unknown-land handling, zero-land reaches, partial catchments.
   - The analysis definitions were fixed in `06_Results_Figures/BHSI_v2_P2C3/P2C3_EXPERIMENTAL_FREEZE.md` before national results were computed.
7. **Manuscript tables and figures.** `07_Manuscript/Phase3_Draft/tools/make_tables.py` and `make_figures.py`.

## Reproduction workflow

### Level A — manuscript tables and figures (minutes)

```bash
cd 07_Manuscript/Phase3_Draft/tools
python -I -B make_tables.py          # writes ../tables/table{1,2,3}_*.tex
python -I -B make_figures.py         # writes ../figures/*.pdf and *.png (all figures)
python -I -B make_figures.py Fig3_spatial_redistribution   # optional: one figure only
cd ../../..
git status                           # unchanged tables = identical reproduction
```

| Manuscript item | Script | Main inputs |
|---|---|---|
| Table 1 (crosswalk) | `make_tables.py` | `05_Experiments/BHSI_v2_P2C/c2/class_treatment_table_FROZEN.csv` |
| Table 2 (budgets) | `make_tables.py` | `analysis/alloc/alloc_summary.json`, `P2C3_CROSS_SCENARIO_REGRET.csv` |
| Table 3 (robustness) | `make_tables.py` | `analysis/alloc/robustness_5pct.csv`, bootstrap in `alloc_summary.json` |
| Fig. 1 (study area, composition) | `make_figures.py` | catchments, eligible network, `analysis/rep/` |
| Fig. 2 (grain-control partition) | `make_figures.py` | `analysis/rep/rep_summary.json`, `catchment_representation.csv` |
| Fig. 3 (spatial redistribution) | `make_figures.py` | `analysis/alloc/allocations_primary_5pct.npz`, `selected_km_by_catchment.csv` |
| Fig. 4 (regret matrix) | `make_figures.py` | `P2C3_CROSS_SCENARIO_REGRET.csv` |
| Fig. 5 (budget sensitivity) | `make_figures.py` | `alloc_summary.json`, `P2C3_CROSS_SCENARIO_REGRET.csv` |
| Fig. S1 (allocation overlap) | `make_figures.py` | `analysis/alloc/replaced_fraction_matrix_5pct.csv` |

Table rows are written as LaTeX fragments; the table frames and captions are in the manuscript.

How closely the regenerated figures match the shipped ones depends on the environment:
- **Original environment** (conda-forge matplotlib): the PNG figures are pixel-identical.
- **Fresh environment from `requirements.txt`** (PyPI wheels): the content is identical, but 0.2–1% of pixels differ through font antialiasing, and some canvases differ by one pixel.
- **PDF files** also differ in their embedded creation metadata.

### Level B — decision analysis from the reach-level table (about 10 minutes)

```bash
python -I -B 04_BHSI_v2_Development/p2c3/p2c3_04_representation.py   # map agreement, partition, rank agreement -> analysis/rep/
python -I -B 04_BHSI_v2_Development/p2c3/p2c3_05_allocation.py       # allocations, regret, references, bootstrap, robustness
                                                                     #   -> analysis/alloc/ and 06_Results_Figures/BHSI_v2_P2C3/*.csv
python -I -B 04_BHSI_v2_Development/p2c3/p2c3_05b_core_reference.py  # rank-copula core reference -> analysis/alloc/core_reference.json
python -I -B 04_BHSI_v2_Development/p2c3/p2c3_07_verify.py           # independent checks -> verification/post_run_checks.json
python -I -B 04_BHSI_v2_Development/p2d/p2d_03_grain_effect.py       # effect of grain-control continuation (6 tiles)
```

These scripts overwrite the shipped outputs in place, so `git status` / `git diff` shows any difference. The only expected difference is the `seconds` run-time field in `alloc_summary.json`.

To write the allocation outputs elsewhere instead, set `P2C3_TEST_DIR` to a directory that holds copies of `reach_table_B40.parquet` and the four `units_*.parquet` files. The script then writes its results there.

### Level C — assembly from the per-tile overlay outputs (minutes)

```bash
python -I -B 04_BHSI_v2_Development/p2c3/p2c3_03_assemble.py
```

This rebuilds `analysis/reach_table_B40.parquet`, `units_{B20,B100,S1000,S500}.parquet`, `pooled.npz` and `assemble_checks.json` from `overlay/tiles/*.npz`. It checks completeness, length conservation and that every tile carries the expected code hash. The diagnostic gradient columns come from `05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg`.

### Level D — national overlay from raw land-cover maps (about 7.4 CPU-hours)

1. Obtain the raw inputs and place them at the paths in [`DATA_SOURCES.md`](DATA_SOURCES.md). The CORINE layer is built with:

   ```bash
   python -I 04_BHSI_v2_Development/p2a/p2a_01_download_eea_clc2018.py 05_Experiments/BHSI_v2_P2A/data_raw/eea_clc2018_laea
   python -I 04_BHSI_v2_Development/p2a/p2a_02_assemble_recovered.py 05_Experiments/BHSI_v2_P2A/data_raw/eea_clc2018_laea 05_Experiments/BHSI_v2_P2A/derived
   ```

2. Run the overlay:

   ```bash
   python -I -B 04_BHSI_v2_Development/p2c3/p2c3_01_run_overlay.py plan 05_Experiments/BHSI_v2_P2C3/overlay
   python -I -B 04_BHSI_v2_Development/p2c3/p2c3_01_run_overlay.py tiles 05_Experiments/BHSI_v2_P2C3/overlay 4
   python -I -B 04_BHSI_v2_Development/p2c3/p2c3_03_assemble.py
   ```

   - `tiles` skips any tile whose `.npz` already exists with the same code hash. **Delete or move the shipped `overlay/tiles/*.npz` first** to recompute them.
   - The last argument is the number of worker processes.
   - The national run used 78 tiles and 26,753 CPU-seconds; the 64 non-preflight tiles took 66 min on 6 processes. Peak memory per worker depends on tile content.

3. Optional preflight and convergence checks, as reported in the manuscript:

   ```bash
   python -I -B 04_BHSI_v2_Development/p2c3/p2c3_01_run_overlay.py catchment 05_Experiments/BHSI_v2_P2C3/preflight 107   # likewise 99, 13, 19
   python -I -B 04_BHSI_v2_Development/p2c3/p2c3_01_run_overlay.py rerun 05_Experiments/BHSI_v2_P2C3/overlay t012_003 05_Experiments/BHSI_v2_P2C3/preflight/determinism_t012_003.npz
   python -I -B 04_BHSI_v2_Development/p2c3/p2c3_02_preflight_checks.py
   python -I -B 04_BHSI_v2_Development/p2d/p2d_02_grain_continuation.py 4                 # 6 capped tiles, cycle cap raised to 12
   ```

   The original runs read the large inputs from a hash-verified local copy through the optional `P2C3_INPUT_CACHE` variable. It is not needed when the inputs sit at the documented paths.

### Level E — network and crosswalk construction

The scripts are included so the construction is fully documented:
- **River pieces:** `phase1/build_native_candidate.py --output <new dir under 05_Experiments>`.
- **Eligibility:** `p2c/p2c_01_eligible_network.py <new dir under 05_Experiments>`.
- **Crosswalk evidence:** `p2b/p2b_01_point_sampling.py`, `p2b_03_summarise_sampling_and_network.py`, `p2b_04_build_crosswalk.py`.
- **Pilot:** `p2c/p2c2_01_select_pilot.py`, `p2c2_02_overlay.py`.

They need the raw inputs in [`DATA_SOURCES.md`](DATA_SOURCES.md) and the file `05_Experiments/P1_5_Portability/script/catchments_107.csv`, which is **not included**. That table comes from the earlier, unpublished MSc version of the index and holds its catchment index values and ranks. The scripts use it to fix the list and order of the 107 catchments; P2-C1 also uses it for reconciliation checks. Their outputs, the river pieces, eligible network, crosswalk and pilot tables, are shipped. Levels A–D start from them.

## Tests

```bash
python -I -B -m unittest discover -s 04_BHSI_v2_Development/p2c3 -p 'test_*.py'
python -I -B -m unittest discover -s 04_BHSI_v2_Development/p2c  -p 'test_*.py'
python -I -B -m unittest discover -s 04_BHSI_v2_Development/phase1 -p 'test_*.py'
```

There are 66 tests in all. They use synthetic inputs or the shipped derived data, and none needs raw third-party data. One test skips by design: it compares an optional independent re-run of P2-C1 that is not shipped.

## Data, licences and attribution

- **Code:** MIT License ([`LICENSE`](LICENSE)).
- **Derived data:** the files under `05_Experiments/`, `06_Results_Figures/` and `07_Manuscript/Phase3_Draft/{tables,figures}/` are released under CC BY 4.0, subject to the upstream attributions in [`DATA_LICENSE.md`](DATA_LICENSE.md).
- **Raw third-party data:** not redistributed, except the Natural England CaBA partnership boundaries (OGL v3.0). [`DATA_SOURCES.md`](DATA_SOURCES.md) lists each source, licence, required attribution, download location and expected file path.

Generated using European Union's Copernicus Land Monitoring Service information (CORINE Land Cover 2018, https://doi.org/10.2909/71c95a07-e296-44fc-b22b-415f42acfdf0); derived data were modified from the original. Contains Natural England data © Natural England. Contains OS data © Crown copyright and database rights 2026. Source: Office for National Statistics licensed under the Open Government Licence v.3.0.

## Limitations

- **Network and crosswalk construction (Level E)** cannot be re-run from this repository alone, because one input table from the unpublished earlier index is not public (see Level E). It also needs:
  - **`merged_terrain50.tif`**, a merged OS Terrain 50 DEM used only for the diagnostic channel gradient. No merge script survives.
  - **The ONS boundary file**, which was queried from the ONS ArcGIS service. The exact query parameters were not recorded; [`DATA_SOURCES.md`](DATA_SOURCES.md) describes the result.
- **The derived results are model-based.** The forage values are ordinal scores, not calibrated probabilities, and no allocation has been validated against field observations of beaver activity.
- **Directory names** follow the original project (for example `01_BHSI_v1_Frozen`, `BHSI_v2_P2C3`), so the unmodified code runs. Only the files listed in the manifest are part of this repository.

## Citation

The manuscript has not yet been published. Until it is, please cite this repository using [`CITATION.cff`](CITATION.cff) ("Cite this repository" on GitHub). Once the article is published, cite the article.

## Authors

- Grace David — Department of Earth and Environmental Sciences, Cardiff University, Cardiff, UK
- Oktay Karakuş (corresponding author) — Department of Earth and Environmental Sciences and Department of Computer Science and Informatics, Cardiff University, Cardiff, UK
- Can Eyüpoğlu — Department of Computer Science and Informatics, Cardiff University, Cardiff, UK; Department of Computer Engineering, Turkish Air Force Academy, National Defence University, Istanbul, Türkiye
