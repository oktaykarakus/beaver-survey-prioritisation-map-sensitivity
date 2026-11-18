# Repository audit

This file records the checks performed on this repository before release (18 Nov 2026), their results and the known limitations. No national-scale experiment was re-run for this audit.

## 1. How the checks were done

- **Fresh-environment check.** The repository was copied to an unrelated directory and a new Python 3.12 virtual environment was built from `requirements.txt` with PyPI wheels. Then:
  - the unit tests ran;
  - the Level B–C pipeline ran with the README commands (assembly → representation → allocation → core reference → verification → grain-continuation effect);
  - Level A ran (tables and figures);
  - every regenerated file was compared with the shipped file (byte comparison; values comparison where bytes differed).
- **Original-environment check.** The figures were also regenerated in the original analysis environment (Python 3.12.4, conda-forge base).
- **Static checks.** Import scan, byte-compilation of every script, path and identifier scans of every file, `.gitignore` check in a throwaway git repository, and a comparison of each staged file with its source in the research project.

## 2. Results

| Check | Result |
|---|---|
| **Imports and dependencies** | **Pass.** A static import scan of all 34 Python files finds 9 third-party packages: numpy, pandas, geopandas, shapely, pyogrio, pyproj, rasterio, scipy, matplotlib. pyarrow, the parquet engine pandas uses, makes 10. All are pinned in `requirements.txt` at the versions of the analysis environment and installed cleanly from PyPI on Python 3.12 (macOS arm64). Every local module imported (`p2c_lc`, `p2c_net`, `p2c3_overlay`, `p2c3_alloc`, `p2c3_scores`, `geometry`, `indicators`) is included. All 34 files byte-compile without error |
| **Relative paths** | **Pass.** All code resolves paths from its own location (`Path(__file__).parents[k]`), and the repository mirrors the original folder layout. Levels A–C ran in a copy at an unrelated location, which shows that no path depends on the original machine. Every repository path named in `README.md` and `DATA_SOURCES.md` exists, except the raw third-party inputs the user must supply (listed there with their expected paths) |
| **Hard-coded local paths and private identifiers** | **Pass.** No absolute local path, user name, temporary path or e-mail address occurs in any file, including GeoPackages, parquet files and the string arrays inside all 90 `.npz` files. The original shell run scripts are **not** included because they contained absolute local paths and a temporary cache path. The README gives the same commands with repository-relative paths. The code's optional `P2C3_INPUT_CACHE` variable is unset by default and not needed |
| **Configuration files** | **Pass.** Included: `phase1/protocol_lock.json`, the frozen crosswalk (`P2B_ECOLOGICAL_CROSSWALK.csv`), the frozen class table, the tile plan and the analysis-freeze protocol (`P2C3_EXPERIMENTAL_FREEZE.md`). The two protocol files read by the pilot and preflight scripts (`P2C2_PILOT_SELECTION.md`, `P2C3_PREFLIGHT_SELECTION.md`) are also included |
| **References to unavailable files** | **Documented, not resolvable here.** Level E scripts read inputs that are not in this repository: raw OS Open Rivers, the ONS boundary file, `merged_terrain50.tif`, the earlier delivered CORINE copy, `05_Experiments/BHSI_v2_P2B/summaries/` (produced by `p2b_01`/`p2b_03`), and `05_Experiments/P1_5_Portability/script/catchments_107.csv`. The last is withheld because it contains index values and ranks from an unpublished earlier version of the index. Level D needs raw CORINE and Living England. All of these are listed in `README.md` and `DATA_SOURCES.md` |
| **Licences** | **Pass, see notes.** Code: MIT (`LICENSE`). Derived data: CC BY 4.0 with upstream attributions (`DATA_LICENSE.md`). The terms of all five source datasets were checked on the providers' pages or item metadata on 18 Nov 2026 (`DATA_SOURCES.md`):<br>• **CORINE:** CLMS full, open and free access with attribution and a modification notice.<br>• **Living England:** OGL v3.0, plus third-party credits and the NPMS acknowledgement.<br>• **OS Open Rivers:** OS OpenData; the supplied licence link resolves to OGL v3.0.<br>• **ONS boundaries:** OGL v3.0.<br>• **Natural England CaBA boundaries:** OGL v3.0.<br>The only raw third-party file included is the CaBA boundary GeoJSON (3.1 MB, OGL v3.0, unmodified). The choice of MIT and CC BY 4.0 for the authors' own work is a default the authors may change; the upstream terms do not require a particular licence for it |
| **Accidental inclusion** | **Pass.** No raw land-cover or river datasets. The largest files are derived: river-pieces GeoPackage 42.1 MB, eligible network 36.6 MB, reach table 13.6 MB, excluded network 10.8 MB. No `__pycache__`, `.pyc`, `.DS_Store`, AppleDouble, log, temporary or credential files. `.gitignore` was tested in a throwaway git repository: it ignores none of the shipped files and covers caches, temporary files, raw-data locations, credentials and the withheld catchment table |
| **Faithfulness to the analysis** | **Pass.** All 34 code files and all 170 data/protocol files are byte-identical to their sources in the research project. The overlay tiles carry a code hash of `p2c3_overlay.py` + `p2c_lc.py`, and `p2c3_03_assemble.py` checks it, which confirms that the shipped overlay library is the one that produced the shipped tiles |
| **Unit tests** (fresh environment) | **Pass.** `phase1`: 16 tests OK. `p2c`: 34 tests OK, 1 skipped by design (it compares an optional independent re-run of P2-C1 that is not shipped). `p2c3`: 16 tests OK. Two small pilot outputs needed by the `p2c` tests (`P2C2_LANDCOVER_COMPARISON.csv` and two buffer-union confusion tables) were missing from the first staging pass; they were added and the tests re-run |
| **Reproducibility of derived outputs, Levels B–C** (fresh environment) | **Pass: identical.** These were regenerated and are byte-identical:<br>• assembly: `reach_table_B40.parquet`, four `units_*.parquet`, `pooled.npz`, `assemble_checks.json`;<br>• representation (`analysis/rep/`, 10 files);<br>• allocation (`analysis/alloc/`, 10 files, and both deliverable CSVs);<br>• core reference, post-run verification, grain-continuation effect.<br>The only difference is the run-time field `seconds` in `alloc_summary.json`. Run times: assembly 6 s, representation 18 s, allocation 434 s, core reference 66 s |
| **Reproducibility of manuscript tables and figures, Level A** | **Tables: identical** (all three `.tex` files). **Figures:** in the original environment, all six PNG figures are pixel-identical. In the fresh PyPI environment the content is identical, but 0.2–1.0% of pixels differ through font antialiasing and three canvases differ by one pixel; Fig. 2 was inspected visually. Regenerated PDFs differ in embedded metadata |
| **README accuracy** | **Pass for Levels A–C and the tests:** every command was executed as written. Level D and E commands were **not executed**, because they need the raw data (about 7 GB) and, for D, about 7.4 CPU-hours. They are taken from each script's own usage documentation and from the original run scripts, with absolute paths removed |
| **Authors and affiliations** | **Pass.** `README.md`, `CITATION.cff` and `LICENSE` match the manuscript's author block:<br>• Grace David: Earth and Environmental Sciences, Cardiff;<br>• Oktay Karakuş (corresponding): Earth and Environmental Sciences and Computer Science and Informatics, Cardiff;<br>• Can Eyüpoğlu: Computer Science and Informatics, Cardiff, and Computer Engineering, Turkish Air Force Academy, National Defence University, Istanbul.<br>`CITATION.cff` has no DOI, journal, volume or date, and no e-mail addresses |

## 3. Environment used for the checks

| | Fresh environment | Original analysis environment |
|---|---|---|
| Python | 3.12 (PyPI venv) | 3.12.4 (conda-forge base) |
| numpy / pandas / geopandas | 1.26.4 / 2.1.1 / 1.1.3 | same |
| shapely / pyogrio / pyproj | 2.0.5 / 0.12.1 / 3.7.2 | same |
| rasterio (GDAL) | 1.3.10 (bundled GDAL 3.8.4) | 1.3.10 (GDAL 3.9.1) |
| scipy / matplotlib / pyarrow | 1.11.3 / 3.8.0 / 23.0.0 | same |
| Platform | macOS arm64 | macOS arm64 |

The original environment also contains unrelated packages that the code does not use. They are not listed in `requirements.txt`.

## 4. Limitations

1. **Level E cannot be run from this repository alone.** Building the river pieces, the eligible network, the crosswalk evidence and the pilot needs raw inputs and one table from the unpublished earlier index (see `DATA_SOURCES.md` §6). Their outputs are shipped, and Levels A–D start from them.
2. **Level D was not re-executed for this audit.** The national overlay was run, checked for determinism and verified during the original analysis (`verification/`, `preflight/`). Exact byte-identity of rasterised outputs is established only for GDAL 3.9.1.
3. **The ONS boundary query was not recorded.** `DATA_SOURCES.md` records the service, fields, features, coordinate system and checksum of the file used.
4. **`merged_terrain50.tif` has no merge script.** It affects only the diagnostic channel gradient, which is shipped.
5. **Cross-platform reproduction was checked only on macOS arm64.** Floating-point-sensitive steps (rasterisation, distance transforms) may differ at the last bit on other platforms. Allocation decisions in the original verification were insensitive to tie-breaking.
6. **Results are model-based.** The forage values are ordinal and uncalibrated, and the allocations have not been validated against field observations; see the manuscript.
