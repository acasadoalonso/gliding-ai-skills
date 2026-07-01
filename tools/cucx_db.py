"""Build and populate a SeeYou contest.db from a CompBundle."""
import datetime
import json
import math
import sqlite3
from pathlib import Path

from tools import cucx_geo as geo

SCHEMA = Path(__file__).with_name("cucx_schema.sql")
AIRCRAFT_TYPE_ID = 7
AIRCRAFT_TYPE = "18_meter"
_ID_BASE = 10_000_000_000
_NOW = "2026-07-01 00:00:00"

# SGP scoring defaults copied from the Pavullo template (class_meta).
_CLASS_META = {
    "auto_save_flight": "-1", "auto_publish_time": "-300", "need_legs": "0",
    "task_from_igc": "0", "engine_calc": "2", "submit_to_ranklist": "0",
    "strict_name": "0", "nominal_launch": "0.96", "nominal_distance": "70000",
    "minimum_distance": "7000", "nominal_goal": "0.25", "nominal_time": "5400",
    "score_back_time": "0", "ftv_factor": "0.2", "use_cache": "0",
}


class IdAllocator:
    """Monotonic, deterministic id source. IDs need only be unique within the
    file, so a single counter over a fixed base suffices; the `table` arg is
    accepted for call-site readability but does not affect the value."""
    def __init__(self):
        self._n = 0

    def next(self, table: str = "") -> int:
        self._n += 1
        return _ID_BASE + self._n


def _millis_to_dt(ms):
    if ms is None:
        return None
    return datetime.datetime.fromtimestamp(
        ms / 1000.0, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _oz_fields(role: str, oz: str):
    """Return (type, oz_type, oz_line, oz_angle1) for a turnpoint."""
    role = role.lower()
    if role == "start":
        return "start", "next", 1 if oz == "Line" else 0, math.pi
    if role == "finish":
        return "finish", "previous", 1 if oz == "Line" else 0, math.pi
    return "point", "symmetric", 0, math.pi


def _insert_warning(cur, ids, start_alt, finish_alt):
    wid = ids.next("warning")
    cur.execute(
        "INSERT INTO warning (id_warning, airspace_violation, failed_validation, "
        "high_enl, max_altitude, min_finish_altitude, max_finish_altitude, "
        "altitude_timeout, start_altitude, start_ground_speed, gps_fix_rate, "
        "altitude_correction, created_at, updated_at) "
        "VALUES (?,1,1,300,0.0,?,10000.0,0,?,0.0,10,50.0,?,?)",
        (wid, float(finish_alt or 0.0), float(start_alt or 0.0), _NOW, _NOW))
    return wid


def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _float_or_none(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def build_contest_db(bundle: dict, db_path: str) -> dict:
    ids = IdAllocator()
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA.read_text())
    cur = con.cursor()

    # location
    af = bundle["airfield"]
    loc_id = ids.next("location")
    cur.execute(
        "INSERT INTO location (id_location, country, continent, name, time_zone, "
        "latitude, longitude, altitude, runway_type, created_at, updated_at) "
        "VALUES (?,?, 'EU', ?, ?, ?, ?, ?, 'grass', ?, ?)",
        (loc_id, af.get("country") or "NO", af.get("name") or "",
         af.get("timezone") or "Europe/Oslo",
         geo.deg2rad(af.get("lat_deg") or 0.0), geo.deg2rad(af.get("lon_deg") or 0.0),
         float(af.get("elevation_m") or 0.0), _NOW, _NOW))

    # contest
    comp = bundle["comp"]
    contest_id = ids.next("contest")
    cur.execute(
        "INSERT INTO contest (id_contest, ref_location, name, start_date, end_date, "
        "country, time_zone, category, live_track_type, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?, 'any', 'none', ?, ?)",
        (contest_id, loc_id, comp["name"], comp["first_day"], comp["last_day"],
         af.get("country") or "NO", af.get("timezone") or "Europe/Oslo", _NOW, _NOW))

    # class (+ class-level warning + class_meta)
    class_warn = _insert_warning(cur, ids, None, None)
    class_id = ids.next("class")
    cur.execute(
        "INSERT INTO class (id_class, ref_warning, ref_aircraft_type, ref_contest, "
        "name, takeoff_altitude, created_at, updated_at) VALUES (?,?,?,?,?,0.0,?,?)",
        (class_id, class_warn, AIRCRAFT_TYPE_ID, contest_id, AIRCRAFT_TYPE, _NOW, _NOW))
    for k, v in _CLASS_META.items():
        cur.execute(
            "INSERT INTO class_meta (id_class_meta, ref_class, key, value) VALUES (?,?,?,?)",
            (ids.next("class_meta"), class_id, k, v))

    # contestants + pilots, keyed by comp_number for result linkage
    cn_to_contestant = {}
    for p in bundle["pilots"]:
        cid = ids.next("contestant")
        cn_to_contestant[p["comp_number"]] = cid
        recorders = json.dumps([{"flarm": p["flarm_id"]}]) if p.get("flarm_id") else None
        cur.execute(
            "INSERT INTO contestant (id_contestant, ref_class, version, name, "
            "aircraft_model, contestant_number, aircraft_registration, handicap, "
            "pure_glider, flight_recorders, not_competing, created_at, updated_at) "
            "VALUES (?,?,1,?,?,?,?,100.0,1,?,0,?,?)",
            (cid, class_id, p["name"], p["aircraft"], p["comp_number"],
             p.get("registration"), recorders, _NOW, _NOW))
        cur.execute(
            "INSERT INTO pilot (id_pilot, ref_contestant, version, first_name, "
            "last_name, nationality, igc_id, created_at, updated_at) "
            "VALUES (?,?,1,?,?,?,?,?,?)",
            (ids.next("pilot"), cid, p["first_name"], p["last_name"],
             p.get("country"), _int_or_none(p.get("ranking_id")), _NOW, _NOW))

    # find the SGP scoring script id
    sgp_script = cur.execute(
        "SELECT id_script FROM script WHERE name LIKE 'Sailplane_Grand_Prix%'"
    ).fetchone()[0]

    # tasks / points / task_points / results
    for t in bundle["tasks"]:
        task_warn = _insert_warning(cur, ids, t["start_altitude_m"], t["finish_altitude_m"])
        task_id = ids.next("task")
        cur.execute(
            "INSERT INTO task (id_task, ref_warning, ref_class, ref_script, task_date, "
            "task_number, result_status, takeoff_altitude, task_type, task_name, "
            "task_distance, start_on_entry, distance_calculation, uncompleted_calculation, "
            "distance_tolerance, altitude_tolerance, min_altitude, multiple_starts, "
            "task_version, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,0.0,'polygon',?,?,0,'waypoints','waypoints',"
            "0.0,0.0,?,0,1,?,?)",
            (task_id, task_warn, class_id, sgp_script, t["date"], t["task_number"],
             t["result_status"], t["name"], float(t["distance_m"]),
             float(t.get("finish_altitude_m") or 0.0), _NOW, _NOW))

        # points with per-leg distance + bearings
        tps = t["turnpoints"]
        for i, tp in enumerate(tps):
            ptype, oz_type, oz_line, oz_angle1 = _oz_fields(tp["role"], tp["oz"])
            if i == 0:
                dist = 0.0
                c_in = 0.0
            else:
                prev = tps[i - 1]
                dist = geo.haversine_m(prev["lat_deg"], prev["lon_deg"],
                                       tp["lat_deg"], tp["lon_deg"])
                c_in = geo.bearing_rad(prev["lat_deg"], prev["lon_deg"],
                                       tp["lat_deg"], tp["lon_deg"])
            if i + 1 < len(tps):
                nxt = tps[i + 1]
                c_out = geo.bearing_rad(tp["lat_deg"], tp["lon_deg"],
                                        nxt["lat_deg"], nxt["lon_deg"])
            else:
                c_out = 0.0
            pid = ids.next("point")
            cur.execute(
                "INSERT INTO point (id_point, name, latitude, longitude, type, elevation, "
                "distance, course_in, course_out, oz_type, oz_radius1, oz_angle1, oz_move, "
                "oz_line, oz_reduce, created_at, updated_at) "
                "VALUES (?,?,?,?,?,0.0,?,?,?,?,?,?,0,?,0,?,?)",
                (pid, tp["name"], geo.deg2rad(tp["lat_deg"]), geo.deg2rad(tp["lon_deg"]),
                 ptype, float(dist), float(c_in), float(c_out), oz_type,
                 int(tp["radius_m"]), oz_angle1, oz_line, _NOW, _NOW))
            cur.execute(
                "INSERT INTO task_point (id_task_point, ref_task, ref_point, point_index, "
                "multiple_start) VALUES (?,?,?,?,0)",
                (ids.next("task_point"), task_id, pid, tp["index"]))

        # results
        for r in t["results"]:
            contestant = cn_to_contestant.get(r["comp_number"])
            if contestant is None:
                continue
            cur.execute(
                "INSERT INTO result (id_result, ref_contestant, ref_task, igc_file, "
                "igc_public_show, points, points_total, rank, rank_total, takeoff, landing, "
                "calculated_start, calculated_finish, calculated_speed, calculated_distance, "
                "status_evaluated, status_airspace_violation, status_high_enl, status_manual, "
                "status_turnpoint_missed, status_fixed_points, w_high_enl, w_no_enl, "
                "w_gps_fix_rate, w_max_altitude, w_finish_altitude, w_start_altitude, "
                "w_max_ground_speed, w_altitude_timeout, w_takeoff_altitude, created_at, updated_at) "
                "VALUES (?,?,?,?,1,?,?,?,?,?,?,?,?,?,?,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,?,?)",
                (ids.next("result"), contestant, task_id, r.get("igc_file"),
                 _float_or_none(r.get("points")), _float_or_none(r.get("points_total")),
                 r.get("rank"), r.get("rank_total"),
                 _millis_to_dt(r.get("takeoff_millis")), _millis_to_dt(r.get("landing_millis")),
                 _millis_to_dt(r.get("start_millis")), _millis_to_dt(r.get("finish_millis")),
                 _float_or_none(r.get("speed_kph")),
                 (r["distance_km"] * 1000.0) if r.get("distance_km") is not None else None,
                 _NOW, _NOW))

    con.commit()
    con.close()
    return {"class_id": class_id, "aircraft_type": AIRCRAFT_TYPE, "contest_id": contest_id}
