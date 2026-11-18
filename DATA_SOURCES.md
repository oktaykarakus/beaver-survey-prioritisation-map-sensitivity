# Source datasets

This file lists the third-party datasets used in the analysis: where each comes from, its licence and required attribution, and where the code expects it. Only the CaBA partnership boundaries are redistributed here. The other datasets are large and must be obtained from their providers.

Licence information was checked against each provider's own published pages or item metadata on 18 Nov 2026. Re-check the providers' current terms before reuse.

## 1. CORINE Land Cover 2018 (vector), version 2020_20u1

| | |
|---|---|
| Provider | European Environment Agency, Copernicus Land Monitoring Service (CLMS) |
| Dataset DOI | https://doi.org/10.2909/71c95a07-e296-44fc-b22b-415f42acfdf0 |
| Product page | https://land.copernicus.eu/en/products/corine-land-cover/clc2018 |
| Terms | CLMS data policy (https://land.copernicus.eu/en/data-policy): products are made available on a principle of "full, open and free access" (Commission Delegated Regulation (EU) No 1159/2013). Users must state the source when distributing, must state when products were adapted or modified, and must not imply EU endorsement |
| Required attribution (derived products) | "Generated using European Union's Copernicus Land Monitoring Service information; https://doi.org/10.2909/71c95a07-e296-44fc-b22b-415f42acfdf0" |
| How it was obtained here | Polygons downloaded from the EEA's public ArcGIS service `https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_LAEA/MapServer/0` (no login) by `04_BHSI_v2_Development/p2a/p2a_01_download_eea_clc2018.py`, then assembled by `p2a_02_assemble_recovered.py` |
| Expected path | `05_Experiments/BHSI_v2_P2A/derived/clc2018_eea_recovered_3035.gpkg` (layer `clc2018_eea_recovered`, EPSG:3035) |
| SHA-256 of the file used | `bb68d31d7f8e49e0edaf4a1895752805206e0cdd08c307953b46d4fec22f86f1` (about 300 MB) |
| Notes | A pre-packaged CLMS download (which needs a CLMS login) holds the same product. The service download was used because an earlier project copy had records without geometry; completeness was cross-checked against the UK release (Cole et al. 2021, https://doi.org/10.5285/084e0bc6-e67f-4dad-9de6-0c698f60e34d). Level E (`phase1/build_native_candidate.py`, `p2b`) additionally reads that earlier delivered copy as `U2018_CLC2018_V2020_20u1.gpkg` under `01_BHSI_v1_Frozen/source_snapshot/data/` |

## 2. Living England Habitat Map (Phase 4)

| | |
|---|---|
| Provider | Natural England |
| Item | "Living England Habitat Map (Phase 4)", Natural England Open Data (ArcGIS item `b3069e7cb3084732b92478b3db51b9c6`) |
| Download | Defra Data Services Platform, dataset `4aa716ce-f6af-454c-8ba2-833ebc1bde96` (https://environment.data.gov.uk/explore/4aa716ce-f6af-454c-8ba2-833ebc1bde96?download=true), GeoPackage |
| Licence | Open Government Licence v3.0 ("There are no public access constraints to this data. Use of this data is subject to the Open Government Licence", item metadata) |
| Required acknowledgements | Credit Natural England, plus the third-party credits in the item's access information. These include "Contains OS data © Crown copyright and database right 2021" and "Contains modified Copernicus Sentinel data [2021]". The National Plant Monitoring Scheme acknowledgement given in the item licence information is also required |
| Documentation | Kilcoyne et al. (2022), *Living England: Satellite-based habitat classification. Technical User Guide*, Natural England Research Report NERR108 |
| Expected path | `05_Experiments/BHSI_v2_P2B/data_raw/living_england_p4/extracted/Living_England_Habitat_Map_Phase_4.gpkg` (EPSG:27700) |
| SHA-256 | downloaded zip `72a23cce43eb260ded705af358813a078858e7f520af0ccbfe7202693b83101f` (1.11 GB); extracted GeoPackage `ae47a170e3f8f0ee890b67fbb2926ac03737f9f327ebc1580e33543267d51c7f` (6,745,264,128 bytes; 6,905,076 segments) |

## 3. OS Open Rivers

| | |
|---|---|
| Provider | Ordnance Survey (OS OpenData) |
| Product page | https://www.ordnancesurvey.co.uk/products/os-open-rivers |
| Licence | OS OpenData licence. The licence link supplied with the data (`http://os.uk/opendata/licence`) resolves to the Open Government Licence v3.0 |
| Required attribution | "Contains OS data © Crown copyright and database rights 2026", as given in the `licence.txt` supplied with the April 2026 release |
| Release used | GeoPackage `oprvrs_gb.gpkg`, layer `watercourse_link`, release dated 14 April 2026 |
| Expected path | `01_BHSI_v1_Frozen/source_snapshot/data/Rivers/Data/oprvrs_gb.gpkg` |
| SHA-256 | `81fbe8d88396a8d45ab29a9ee14468aa41a325c57fe68d16e9b48ed06daa0644` |
| Used by | Level E only (river pieces, eligibility). The derived network is shipped |

## 4. ONS country boundaries — Countries (December 2023) Boundaries UK BFC

| | |
|---|---|
| Provider | Office for National Statistics, Open Geography Portal (ArcGIS item `e4921755865f435b957c76339bf7e6e4`) |
| Service | https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Countries_December_2023_Boundaries_UK_BFC/FeatureServer |
| Licence | Open Government Licence v3.0 (ONS geography licences page: "Digital boundary products and reference maps are supplied under the Open Government Licence") |
| Required attribution | "Source: Office for National Statistics licensed under the Open Government Licence v.3.0" and "Contains OS data © Crown copyright and database right [year]". ONS does not state the year to use for this release |
| File used | `ctry23_BFC_EW_27700.geojson`: the England (`E92000001`) and Wales (`W92000004`) features with fields `CTRY23CD`, `CTRY23NM`, in EPSG:27700. Full resolution, clipped to mean high water |
| Expected path | `05_Experiments/BHSI_v2_P2B/data_raw/ons_countries/ctry23_BFC_EW_27700.geojson` |
| SHA-256 | `9a827dabc6af3e91594f75f3ab59aa686fcf23efbdfc08c2a35d203b29719653` |
| Notes | The file was queried from the FeatureServer above; the exact query parameters were not recorded. Used by Level E and by the preflight selection only |

## 5. CaBA partnership boundaries — Wild Beavers in Catchment Based Approach Partnerships 2025 (England)

| | |
|---|---|
| Provider | Natural England (ArcGIS item `0b13685f001843ed90dc2b21a4db4e9e`) |
| Page | https://naturalengland-defra.opendata.arcgis.com/datasets/Defra::wild-beavers-in-catchment-based-approach-partnerships-2025-england/about |
| Licence | Open Government Licence v3.0 ("There are no public access constraints to this data. Use of this data is subject to the Open Government Licence") |
| Required attribution | "© Natural England, 2025. Contains data supplied by © Environment Agency 2015." |
| Lineage (provider) | Developed from The Rivers Trust's CaBA Catchment Partnerships layer, derived from the Environment Agency WFD River Waterbody Catchments (Cycle 2) |
| **Included in this repository** | `01_BHSI_v1_Frozen/source_snapshot/data/Beavers/Wild_Beaver_Catchments_England_-2509696373757772249.geojson` (107 partnerships, EPSG:4326), unmodified |

## 6. Other inputs used only for Level E

| Input | Use | Status |
|---|---|---|
| OS Terrain 50 DEM, merged to `merged_terrain50.tif` under `01_BHSI_v1_Frozen/source_snapshot/data/` | Diagnostic channel gradient of river pieces (`phase1/build_native_candidate.py`) | Not included. OS OpenData product; the merge step that created the single GeoTIFF was not scripted. Gradient values are shipped in `canonical_native_rivers.gpkg` |
| `05_Experiments/P1_5_Portability/script/catchments_107.csv` | List and order of the 107 catchments; reconciliation checks | **Not included**: it contains index values and ranks from the earlier, unpublished MSc version of the index |
