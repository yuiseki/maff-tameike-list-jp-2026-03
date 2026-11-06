"""Second route: compare the Parquet source columns with the 8 split xlsx files (read separately), and check invariants."""
import collections, csv, json, sys
import openpyxl, pyarrow.parquet as pq

t = pq.read_table("data/parquet/maff_tameike_ichiran_20260331.parquet").to_pylist()
NUM = ["lat_deg", "lat_min", "lat_sec", "lon_deg", "lon_min", "lon_sec", "dam_height_m", "crest_length_m", "storage_thousand_m3", "surface_area_km2"]
def key_parquet(r):
    return (r["name"], r["prefecture"], r["municipality"], r["address"]) + tuple(r[k] for k in NUM)
def tx(v):
    if v is None: return None
    if isinstance(v, float) and v.is_integer(): v = int(v)
    return str(v)
def fl(v): return None if v is None or v == "" else float(v)
split = []
for i in range(1, 9):
    ws = openpyxl.load_workbook(f"raw/split/tameike_ichiranR8_{i}.xlsx", read_only=True, data_only=True).worksheets[0]
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if all(v is None for v in r): continue
        split.append((tx(r[0]), tx(r[1]), tx(r[2]), tx(r[3])) + tuple(fl(v) for v in r[4:14]))
cp, cs = collections.Counter(key_parquet(r) for r in t), collections.Counter(split)
res = {"parquet_rows": len(t), "split_rows": len(split), "multiset_equal": cp == cs}
bad = [r for r in t if r["coord_status"] in ("ok", "ok_carry") and (r["lat"] != r["lat_original"] or r["lon"] != r["lon_original"])]
res["unchanged_statuses_with_changed_values"] = len(bad)
res["changed_rows"] = [r["source_row"] for r in t if r["lat"] is not None and (r["lat"] != r["lat_original"] or r["lon"] != r["lon_original"])]
res["null_lat_lon_rows"] = sum(1 for r in t if r["lat"] is None and r["lon"] is None)
res["null_only_for_suspect_or_placeholder"] = all((r["lat"] is None) == (r["coord_status"].startswith("suspect") or r["coord_status"] == "placeholder") for r in t)
res["lat_original_never_null"] = all(r["lat_original"] is not None and r["lon_original"] is not None for r in t)
res["non_null_in_range"] = sum(1 for r in t if r["lat"] is not None and 20 <= r["lat"] <= 46 and 122 <= r["lon"] <= 154)
res["non_null_outside_range"] = [r["source_row"] for r in t if r["lat"] is not None and not (20 <= r["lat"] <= 46 and 122 <= r["lon"] <= 154)]
res["source_rows_unique"] = len({r["source_row"] for r in t}) == len(t)
json.dump(res, open("docs/verification.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
