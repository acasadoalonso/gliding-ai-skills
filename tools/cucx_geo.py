"""Coordinate and geodesic helpers for .cucx generation.

SeeYou stores point/location coordinates in radians; .cup files use DDMM.mmm.
"""
import math

_R = 6371000.0  # FAI sphere radius, metres


def deg2rad(deg: float) -> float:
    return deg * math.pi / 180.0


def rad2deg(rad: float) -> float:
    return rad * 180.0 / math.pi


def _to_cup(deg: float, deg_width: int, pos: str, neg: str) -> str:
    hemi = pos if deg >= 0 else neg
    deg = abs(deg)
    d = int(deg)
    minutes = (deg - d) * 60.0
    return f"{d:0{deg_width}d}{minutes:06.3f}{hemi}"


def to_cup_lat(deg: float) -> str:
    return _to_cup(deg, 2, "N", "S")


def to_cup_lon(deg: float) -> str:
    return _to_cup(deg, 3, "E", "W")


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = deg2rad(lat1), deg2rad(lat2)
    dphi = deg2rad(lat2 - lat1)
    dlam = deg2rad(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * _R * math.asin(min(1.0, math.sqrt(a)))


def bearing_rad(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = deg2rad(lat1), deg2rad(lat2)
    dlam = deg2rad(lon2 - lon1)
    y = math.sin(dlam) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlam)
    return math.atan2(y, x) % (2 * math.pi)
