import math
import pytest
from tools import cucx_geo as g


def test_deg2rad_matches_math_and_roundtrips():
    assert g.deg2rad(180.0) == pytest.approx(math.pi)
    assert g.deg2rad(44.32) == pytest.approx(44.32 * math.pi / 180.0)
    assert g.rad2deg(g.deg2rad(44.32)) == pytest.approx(44.32)


def test_to_cup_lat_north():
    assert g.to_cup_lat(44.282216667) == "4416.933N"


def test_to_cup_lat_south():
    assert g.to_cup_lat(-44.282216667) == "4416.933S"


def test_to_cup_lon_east_zero_padded():
    assert g.to_cup_lon(10.765283333) == "01045.917E"


def test_haversine_known_leg():
    # Starmoen start -> Atna (comp 93 Race1); great-circle ~105.8 km
    d = g.haversine_m(60.87813333, 11.67323333, 61.73726667, 10.8205)
    assert 100000 < d < 110000


def test_bearing_north_is_zero():
    b = g.bearing_rad(0.0, 0.0, 1.0, 0.0)
    assert b == pytest.approx(0.0, abs=1e-6)


def test_bearing_east_is_half_pi():
    b = g.bearing_rad(0.0, 0.0, 0.0, 1.0)
    assert b == pytest.approx(math.pi / 2, abs=1e-3)
