"""National xlsx -> data/parquet/maff_tameike_ichiran_20260331.parquet with decimal coordinates and a coord_status column.
Usage: python scripts/01_build.py  (run from the dataset directory)"""
import collections, hashlib, json, pathlib, statistics, sys
import openpyxl, pyarrow as pa, pyarrow.parquet as pq
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from coords import judge, dms_to_deg

SRC = "raw/data/tameike_ichiranR8.xlsx"
OUT = pathlib.Path("data/parquet/maff_tameike_ichiran_20260331.parquet")
NAMES = ["name", "prefecture", "municipality", "address", "lat_deg", "lat_min", "lat_sec", "lon_deg", "lon_min", "lon_sec",
         "dam_height_m", "crest_length_m", "storage_thousand_m3", "surface_area_km2"]
wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
ws = wb.worksheets[0]
it = ws.iter_rows(values_only=True)
header = list(next(it))
rows = []
for n, r in enumerate(it, start=2):
    if all(v is None for v in r):
        continue
    rows.append((n, list(r)))
print("rows", len(rows), file=sys.stderr)

def txt(v):
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v)

def f(v):
    return None if v is None or v == "" else float(v)

# pass 1: municipality medians from rows that are not placeholders and are in range
from coords import in_range
tmp = collections.defaultdict(list)
for n, r in rows:
    la = (f(r[4]), f(r[5]), f(r[6])); lo = (f(r[7]), f(r[8]), f(r[9]))
    if None in la + lo or la[1] == la[2] == lo[1] == lo[2] == 0:
        continue
    a, b = dms_to_deg(*la), dms_to_deg(*lo)
    if in_range(a, b):
        tmp[(r[1], r[2])].append((a, b))
med = {k: (statistics.median(x for x, _ in v), statistics.median(y for _, y in v)) for k, v in tmp.items() if len(v) >= 5}

cols = {k: [] for k in NAMES + ["source_row", "lat", "lon", "lat_original", "lon_original", "coord_status"]}
status_count = collections.Counter(); fixed = []
for n, r in rows:
    for k, v in zip(NAMES, r):
        cols[k].append(txt(v) if k in ("name", "prefecture", "municipality", "address") else f(v))
    cols["source_row"].append(n)
    la = (f(r[4]), f(r[5]), f(r[6])); lo = (f(r[7]), f(r[8]), f(r[9]))
    j = judge(la, lo, med.get((r[1], r[2])))
    for k in ("lat", "lon", "lat_original", "lon_original"):
        cols[k].append(j[k])
    cols["coord_status"].append(j["status"]); status_count[j["status"]] += 1
    if j["status"].startswith("fixed") or j["status"].startswith("suspect"):
        fixed.append({"source_row": n, "name": r[0], "prefecture": r[1], "municipality": r[2], "status": j["status"],
                      "dms": [r[i] for i in range(4, 10)], "lat_original": j["lat_original"], "lon_original": j["lon_original"],
                      "lat": j["lat"], "lon": j["lon"]})
t = pa.table(cols)
OUT.parent.mkdir(parents=True, exist_ok=True)
pq.write_table(t, OUT, compression="zstd")
pathlib.Path("docs").mkdir(exist_ok=True)
json.dump({"source": SRC, "source_sha256": hashlib.sha256(open(SRC, "rb").read()).hexdigest(), "rows": len(rows),
           "source_header": header, "status_count": status_count, "municipalities_with_median": len(med)},
          open("docs/build.json", "w"), ensure_ascii=False, indent=1)
with open("docs/coord_review.jsonl", "w") as fh:
    for x in fixed:
        fh.write(json.dumps(x, ensure_ascii=False) + "\n")
print(dict(status_count))
