# uvx --with pytest python -m pytest scripts/test_coords.py
import math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from coords import dms_to_deg, judge, hav_km

def test_dms_to_deg_plain():
    assert math.isclose(dms_to_deg(36, 30, 0), 36.5)

def test_dms_to_deg_carries_sixty_seconds():
    assert math.isclose(dms_to_deg(141, 1, 60), 141 + 2 / 60)

NAGANO = (36.85, 138.37)  # municipality median

def test_missing_hundred_in_longitude_is_fixed():
    r = judge((36, 57, 20), (38, 23, 13), NAGANO)
    assert r["status"] == "fixed_lon_plus100"
    assert 138.38 < r["lon"] < 138.40 and math.isclose(r["lat"], 36 + 57 / 60 + 20 / 3600)

def test_swapped_lat_lon_is_fixed():
    r = judge((138, 23, 13), (36, 57, 20), NAGANO)
    assert r["status"] == "fixed_swap" and r["lat"] < 40 < r["lon"]

def test_normal_point_is_ok():
    assert judge((36, 50, 0), (138, 20, 0), NAGANO)["status"] == "ok"

def test_sixty_seconds_is_marked_carry_but_kept():
    r = judge((36, 50, 60), (138, 20, 0), NAGANO)
    assert r["status"] == "ok_carry" and math.isclose(r["lat"], 36 + 51 / 60)

def test_integer_degree_pair_is_placeholder_and_not_fixed():
    r = judge((36, 0, 0), (136, 0, 0), (37.4, 136.9))
    assert r["status"] == "placeholder" and r["lat"] is None and r["lon"] is None
    assert r["lat_original"] == 36.0 and r["lon_original"] == 136.0

def test_far_point_without_a_fix_is_suspect_and_lat_lon_are_null():
    r = judge((37, 12, 5.3), (138, 16, 24), (34.4, 135.3))
    assert r["status"] == "suspect_city_outlier" and r["lat"] is None and r["lon"] is None
    assert math.isclose(r["lat_original"], 37 + 12 / 60 + 5.3 / 3600)

def test_out_of_range_without_fix_is_suspect_range():
    r = judge((10, 0, 1), (50, 0, 1), None)
    assert r["status"] == "suspect_range" and r["lat"] is None and r["lon"] is None and r["lat_original"] == 10 + 1 / 3600

def test_no_city_median_skips_the_distance_check():
    assert judge((26, 38, 48.3), (142, 10, 7.3), None)["status"] == "ok"

def test_hav_km_is_symmetric_and_sane():
    assert 110 < hav_km(35, 135, 36, 135) < 112
