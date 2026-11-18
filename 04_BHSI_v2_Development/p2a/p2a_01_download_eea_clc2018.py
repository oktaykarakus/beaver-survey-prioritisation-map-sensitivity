"""P2-A step 1: download CORINE Land Cover 2018 (vector, V2020_20u1) polygons from the EEA's own
public ArcGIS feature service and keep every raw response with a SHA-256.

Usage: python p2a_01_download_eea_clc2018.py <out_dir>
Footprint = bounding envelope of the delivered file (EPSG:3035), so that the recovered layer can be compared
like-for-like with the delivered one. Resumable: existing, hash-recorded pages are not re-fetched.
Nothing outside <out_dir> is written. No credentials are used or required."""
import sys, json, time, hashlib, urllib.request, urllib.parse
from pathlib import Path
SERVICE = "https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_LAEA/MapServer/0"
ENV = "3155190,3095679,3763352,4239405"          # delivered-file bounds, EPSG:3035 (rounded outward)
CHUNK = 200
out = Path(sys.argv[1]); pages = out / "pages"; pages.mkdir(parents=True, exist_ok=True)

def post(path, retries=6, **kw):
    kw.setdefault("f", "json")
    req = urllib.request.Request(f"{SERVICE}/{path}", urllib.parse.urlencode(kw).encode(),
                                 headers={"User-Agent": "BHSI-research-P2A/1.0 (academic data recovery)"})
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(req, timeout=900).read()
        except Exception as e:
            print("retry", attempt, repr(e), flush=True); time.sleep(5 * (attempt + 1))
    raise RuntimeError("download failed")

def fetch(part):
    """Fetch features by OBJECTID; if the server rejects a large response (HTTP 405 seen for pages holding the
    very large polygons), split the request and merge the GeoJSON features."""
    try:
        return json.loads(post("query", retries=2, objectIds=",".join(map(str, part)), outFields="*", returnGeometry="true", outSR=3035, f="geojson"))
    except RuntimeError:
        if len(part) == 1: raise
        h = len(part) // 2; a, b = fetch(part[:h]), fetch(part[h:])
        a["features"] += b["features"]; return a

sha = lambda b: hashlib.sha256(b).hexdigest()
meta_layer = post("")                               # layer description
(out / "service_layer_description.json").write_bytes(meta_layer)
idq = post("query", where="1=1", geometry=ENV, geometryType="esriGeometryEnvelope", inSR=3035,
           spatialRel="esriSpatialRelIntersects", returnIdsOnly="true")
(out / "objectid_list_response.json").write_bytes(idq)
ids = sorted(json.loads(idq)["objectIds"]); print(len(ids), "feature ids", flush=True)
count_all = post("query", where="1=1", returnCountOnly="true"); (out / "service_total_count.json").write_bytes(count_all)
manifest = out / "download_manifest.csv"
done = {}
if manifest.exists():
    for line in manifest.read_text().splitlines()[1:]:
        n, a, b, h, nb, ts = line.split(","); done[n] = line
else:
    manifest.write_text("page,first_oid,last_oid,sha256,bytes,utc_downloaded\n")
t0 = time.time()
for i in range(0, len(ids), CHUNK):
    part = ids[i:i + CHUNK]; name = f"page_{i // CHUNK:05d}.geojson"
    if name in done and (pages / name).exists(): continue
    d = fetch(part); b = json.dumps(d).encode(); n = len(d.get("features", []))
    if "error" in d or n != len(part): raise RuntimeError((name, n, len(part), d.get("error")))
    (pages / name).write_bytes(b)
    with manifest.open("a") as m:
        m.write(f"{name},{part[0]},{part[-1]},{sha(b)},{len(b)},{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    print(name, n, f"{len(b)/1e6:.1f}MB", f"{time.time()-t0:.0f}s", flush=True)
print("DONE", len(ids), flush=True)
