"""Coordinate rules for the MAFF reservoir list (degrees, minutes, seconds to decimal degrees).

Rules, in order, per row:
 1. dms_to_deg: d + m/60 + s/3600. A minute or second of exactly 60 is converted as is (a carry).
 2. placeholder: both latitude and longitude have minute = second = 0. lat and lon become null, the
    converted source values stay in lat_original and lon_original.
 3. range: latitude 20 to 46 and longitude 122 to 154. Outside is an anomaly.
 4. city outlier: a municipality with 5 or more rows (placeholders excluded) has a median point.
    More than OUTLIER_KM from it is an anomaly. A municipality with fewer rows is not judged.
 5. fix: only for an anomaly, try in order (a) longitude degrees + 100, (b) swap latitude and longitude.
    Accept the first candidate that is in range and within FIX_KM of the municipality median.
    No candidate: lat and lon become null, the converted source values stay in lat_original and
    lon_original, and the row is marked suspect. Nothing else is guessed.
"""
import math

LAT_RANGE, LON_RANGE = (20.0, 46.0), (122.0, 154.0)
OUTLIER_KM, FIX_KM = 50.0, 30.0

def dms_to_deg(d, m, s):
    return float(d) + float(m) / 60 + float(s) / 3600

def hav_km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    x = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))

def in_range(lat, lon):
    return LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]

def judge(lat_dms, lon_dms, median):
    """lat_dms, lon_dms: (d, m, s). median: (lat, lon) of the municipality or None. Returns a dict."""
    lat, lon = dms_to_deg(*lat_dms), dms_to_deg(*lon_dms)
    out = {"lat": lat, "lon": lon, "lat_original": lat, "lon_original": lon}
    if lat_dms[1] == lat_dms[2] == lon_dms[1] == lon_dms[2] == 0:
        out.update(status="placeholder", lat=None, lon=None); return out
    carry = 60 in (lat_dms[1], lat_dms[2], lon_dms[1], lon_dms[2])
    rng = in_range(lat, lon)
    far = rng and median is not None and hav_km(lat, lon, *median) > OUTLIER_KM
    if rng and not far:
        out["status"] = "ok_carry" if carry else "ok"; return out
    cands = [("fixed_lon_plus100", lat, lon + 100 if lon < 100 else None), ("fixed_swap", lon, lat)]
    for name, la, lo in cands:
        if lo is None or not in_range(la, lo) or median is None:
            continue
        if hav_km(la, lo, *median) <= FIX_KM:
            out.update(status=name, lat=la, lon=lo); return out
    out.update(status="suspect_city_outlier" if rng else "suspect_range", lat=None, lon=None)
    return out
