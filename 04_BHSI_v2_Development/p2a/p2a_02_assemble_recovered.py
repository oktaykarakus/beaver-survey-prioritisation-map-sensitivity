"""P2-A step 2: assemble the downloaded EEA pages into one GeoPackage (EPSG:3035) and record checksums.
Usage: python -I p2a_02_assemble_recovered.py <data_raw/eea_clc2018_laea> <derived_dir>
Verifies every page hash against download_manifest.csv before reading."""
import sys, json, hashlib, csv
from pathlib import Path
import geopandas as gpd, pandas as pd
raw, der = Path(sys.argv[1]), Path(sys.argv[2]); der.mkdir(parents=True, exist_ok=True)
man = pd.read_csv(raw / "download_manifest.csv")
frames = []
for r in man.itertuples():
    b = (raw / "pages" / r.page).read_bytes()
    assert hashlib.sha256(b).hexdigest() == r.sha256, f"hash mismatch {r.page}"
    d = json.loads(b)
    g = gpd.GeoDataFrame.from_features(d["features"], crs=3035)   # request used outSR=3035
    frames.append(g)
g = pd.concat(frames, ignore_index=True)
g = gpd.GeoDataFrame(g, geometry="geometry", crs=3035).sort_values("OBJECTID", kind="stable").reset_index(drop=True)
expected = len(json.loads((raw / "objectid_list_response.json").read_text())["objectIds"])
assert len(g) == expected and g.OBJECTID.is_unique, (len(g), expected)
out = der / "clc2018_eea_recovered_3035.gpkg"
g.to_file(out, driver="GPKG", layer="clc2018_eea_recovered")
sha = hashlib.sha256(out.read_bytes()).hexdigest()
(der / "clc2018_eea_recovered_3035.sha256").write_text(f"{sha}  {out.name}\n")
print(json.dumps({"features": len(g), "null_geom": int(g.geometry.isna().sum()), "sha256": sha, "pages": len(man)}))
