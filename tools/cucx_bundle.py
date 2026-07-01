"""Fetch and normalize an SGP competition into a CompBundle dict."""
import sys
from pathlib import Path

_SGP = str(Path(__file__).resolve().parent.parent / "src" / "SGP")
if _SGP not in sys.path:
    sys.path.insert(0, _SGP)


def _default_fetchers():
    import sgp_api
    return sgp_api


def result_status_map(sgp_label: str) -> str:
    label = (sgp_label or "").lower()
    if label == "official":
        return "official"
    if label in ("preliminary", "provisional"):
        return "preliminary"
    return "preliminary"


def _pilot(p: dict) -> dict:
    return {
        "comp_number": p.get("competition_number"),
        "first_name": p.get("first_name", ""),
        "last_name": p.get("last_name", ""),
        "name": p.get("name", ""),
        "country": p.get("country"),
        "aircraft": p.get("aircraft", ""),
        "registration": p.get("registration"),
        "flarm_id": p.get("flarm_id"),
        "ranking_id": p.get("ranking_id"),
    }


def _turnpoint(tp: dict) -> dict:
    return {
        "index": tp["index"],
        "name": tp["name"],
        "role": tp["role"],
        "lat_deg": tp["latitude"],
        "lon_deg": tp["longitude"],
        "oz": tp["observation_zone"],
        "radius_m": tp["radius"],
    }


def _length_m(task: dict) -> float:
    # get_task().length is a string like "261.36 km"; may be absent.
    raw = task.get("length")
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    return float(str(raw).split()[0]) * 1000.0


def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _results_for_day(day_json: dict, total_json: dict) -> list:
    totals = {}
    for s in (total_json or {}).get("standings", []):
        totals[s["competition_number"]] = (s["total_points"], s["rank"])
    out = []
    for r in day_json.get("results", []):
        cn = r["competition_number"]
        tp, tr = totals.get(cn, (None, None))
        out.append({
            "comp_number": cn,
            "rank": _int_or_none(r.get("rank")),
            "points": r.get("points"),
            "points_total": tp,
            "rank_total": _int_or_none(tr),
            "speed_kph": r.get("speed_kph"),
            "distance_km": r.get("distance_km"),
            "igc_file": r.get("igc_file"),
            "takeoff_millis": r.get("start_time_millis"),
            "landing_millis": r.get("finish_time_millis"),
            "start_millis": r.get("start_time_millis"),
            "finish_millis": r.get("finish_time_millis"),
        })
    return out


def build_bundle(comp_id: int, fetchers=None) -> dict:
    f = fetchers or _default_fetchers()
    comp = f.fetch_competition(comp_id)
    raw_pilots = f.fetch_pilots(comp_id)
    pilots = raw_pilots["result"] if isinstance(raw_pilots, dict) else raw_pilots
    day_type = {d["day_id"]: d.get("type_label") for d in comp["days"]}

    tasks = []
    airfield = None
    for day in comp["days"]:
        did = day["day_id"]
        try:
            task = f.fetch_task(comp_id, did)
        except Exception:
            continue  # no task set for this day
        turnpoints = task.get("turnpoints") or []
        if not turnpoints:
            continue  # empty/future day — skip entirely
        if airfield is None:
            airfield = {
                "name": task.get("airfield"),
                "elevation_m": task.get("elevation"),
                "timezone": task.get("timezone"),
                "lat_deg": turnpoints[0]["latitude"],
                "lon_deg": turnpoints[0]["longitude"],
                "country": next((p.get("country") for p in pilots), None),
            }
        day_json, total_json = {}, {}
        try:
            day_json = f.fetch_day_results(comp_id, did)
            total_json = f.fetch_total_results(comp_id, did)
        except Exception:
            day_json, total_json = {}, {}

        if day_type.get(did) == "Practice":
            status = "practice"
        else:
            label = day_json.get("results_status_label") if day_json else None
            status = result_status_map(label) if label else "preliminary"

        tasks.append({
            "day_id": did,
            "date": day["date"],
            "task_number": len(tasks) + 1,
            "name": task.get("name"),
            "type": task.get("type"),
            "distance_m": _length_m(task),
            "start_altitude_m": task.get("start_altitude"),
            "finish_altitude_m": task.get("finish_altitude"),
            "result_status": status,
            "turnpoints": [_turnpoint(tp) for tp in turnpoints],
            "results": _results_for_day(day_json, total_json) if day_json else [],
        })

    return {
        "comp": {
            "id": comp["id"], "name": comp["name"],
            "short_name": comp.get("short_name", comp["name"]),
            "first_day": comp["first_day"], "last_day": comp["last_day"],
        },
        "airfield": airfield or {},
        "pilots": [_pilot(p) for p in pilots],
        "tasks": tasks,
    }
