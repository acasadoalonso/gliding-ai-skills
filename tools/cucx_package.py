"""Generate the .cup waypoint file and assemble the .cucx ZIP."""
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from tools import cucx_db
from tools import cucx_geo as geo
from tools import cucx_hash

_CUP_HEADER = "name,code,country,lat,lon,elev,style,rwdir,rwlen,freq,desc"

_TMPTASKS = (
    "version=27\r\nuser=\r\ncup\r\n"
    "name,code,country,lat,lon,elev,style,rwdir,rwlen,rwwidth,freq,desc,userdata,pics\r\n"
    "-----Related Tasks-----\r\n"
)


def _code(name: str) -> str:
    return "".join(ch for ch in name.upper() if ch.isalnum())[:8]


def _selected_tasks(tasks: list, days) -> list:
    """Tasks whose turnpoint sequence goes into the CUP Related Tasks section.

    `days` is None/"ALL" for every task, or an int task_number (1-based, as
    shown in the day results — "Day 3") to emit just that day's task line.
    The contest DB always keeps every day regardless of this filter.
    """
    if days is None or str(days).upper() == "ALL":
        return tasks
    return [t for t in tasks if t["task_number"] == int(days)]


def _task_line(t: dict) -> str:
    """One CUP task: label followed by the ordered turnpoint names.

    Each name must match a waypoint emitted above, so SeeYou can resolve the
    task geometry back to the waypoint database.
    """
    label = t.get("name") or f"Task {t['task_number']}"
    names = ",".join(f'"{tp["name"]}"' for tp in t["turnpoints"])
    return f'"{label}",{names}'


def build_cup(bundle: dict, days=None) -> str:
    seen = {}
    for t in bundle["tasks"]:
        for tp in t["turnpoints"]:
            seen.setdefault(tp["name"], tp)
    rows = [_CUP_HEADER]
    for name, tp in seen.items():
        lat = geo.to_cup_lat(tp["lat_deg"])
        lon = geo.to_cup_lon(tp["lon_deg"])
        style = "1"  # normal turnpoint
        rows.append(f'"{name}","{_code(name)}",,{lat},{lon},0.0m,{style},,,,')
    rows.append("-----Related Tasks-----")
    for t in _selected_tasks(bundle["tasks"], days):
        rows.append(_task_line(t))
    return "\r\n".join(rows) + "\r\n"


def _register_contest_file(db_path: str, cup_name: str, cup_bytes: bytes, contest_id: int):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cfid = int(cur.execute(
        "SELECT COALESCE(MAX(id_contest_file),20000000000)+1 FROM contest_file"
    ).fetchone()[0])
    cur.execute(
        "INSERT INTO contest_file (id_contest_file, ref_contest, name, hash, size, "
        "active, format, created_at, updated_at) VALUES (?,?,?,?,?,1,'waypoint/cup',?,?)",
        (cfid, contest_id, cup_name, cucx_hash.content_hash(cup_bytes), len(cup_bytes),
         cucx_db._NOW, cucx_db._NOW))
    con.commit()
    con.close()
    return cfid


def assemble_cucx(bundle: dict, out_path: str, days=None) -> str:
    with tempfile.TemporaryDirectory() as td:
        db_path = str(Path(td) / "contest.db")
        meta = cucx_db.build_contest_db(bundle, db_path)

        cup_text = build_cup(bundle, days=days)
        cup_bytes = cup_text.encode("utf-8")
        cup_name = f"{bundle['comp']['id']}_waypoints.cup"
        cfid = _register_contest_file(db_path, cup_name, cup_bytes, meta["contest_id"])

        db_bytes = Path(db_path).read_bytes()
        uv_meta = f"{meta['class_id']}\t{cfid % 100}\t{meta['aircraft_type']}\n"

        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("contest.db", db_bytes)
            z.writestr(f"waypoint/{cup_name}", cup_bytes)
            z.writestr("uv.meta", uv_meta)
            z.writestr("tmptasks.meta", _TMPTASKS)
    return out_path
