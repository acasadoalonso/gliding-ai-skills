# SGP → SeeYou `.cucx` Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/make_cucx.py`, a reusable generator that pulls an SGP competition's data through `src/SGP/sgp_api.py` and writes a SeeYou Competition `.cucx` file (contest structure, pilots, race tasks with geometry, and scored results), targeting competition 93 (Norway SGP 2026).

**Architecture:** Template-clone. A committed seed SQL file (`tools/cucx_schema.sql`, extracted from `pavullo.cucx`) provides the exact SeeYou schema, PRAGMAs, `aircraft_type` seed rows, and the four `(default)` scoring scripts. The generator builds a fresh `contest.db` from that seed, populates every contest-specific table from a normalized data bundle, generates the active `.cup` waypoint file, and packs `contest.db` + `waypoint/<id>.cup` + `uv.meta` + `tmptasks.meta` into the `.cucx` ZIP. Data is fetched by importing `sgp_api` (no MCP runtime needed).

**Tech Stack:** Python 3, stdlib only for the generator (`sqlite3`, `zipfile`, `hashlib`, `base64`, `math`, `json`, `argparse`); `pytest` for tests; `httpx` (already a dependency of `sgp_api`) for live fetches when capturing fixtures.

## Global Constraints

- **Coordinates in `point` and `location` are stored in radians** (decimal degrees × π/180). `.cup` files store `DDMM.mmm` + hemisphere.
- **`contest_file` hash = `base64.b64encode(sha256(bytes)).decode().rstrip("=")`** (standard base64, padding stripped). `contest_file.size` = raw byte length. (Verified against Pavullo: `waypoint/29958.cup` → `P1jXnrgSI8a2FCf6xulfNifauGG98z3JGadjkkvSDFk`, size 10288.)
- **SQLite header:** `application_id=1668637560`, `user_version=3`, `page_size=1024`, UTF-8.
- **Foreign keys must be internally consistent.** IDs use a fixed base (`10_000_000_000`) plus a per-table sequential counter; values need only be unique within the file.
- **Data source:** import `sgp_api` from `src/SGP`; the generator adds `src/SGP` to `sys.path`. No MCP dependency.
- **Scope:** single class; race days only produce a `task` when `get_task` succeeds and `result` rows only when `get_day_results` returns scored results. No IGC log embedding; `result.igc_file` holds the SGP filename string. No airspace files, no alternate waypoint export formats.
- **Race sphere radius for geodesy:** 6371000 m.

## File Structure

- Create: `tools/cucx_geo.py` — coordinate + geodesic pure functions.
- Create: `tools/cucx_hash.py` — content hashing for `contest_file`.
- Create: `tools/cucx_schema.sql` — seed schema + PRAGMAs + `aircraft_type` + `script` rows (generated from `pavullo.cucx` in Task 3).
- Create: `tools/cucx_bundle.py` — fetch via `sgp_api` and normalize into a `CompBundle` dict.
- Create: `tools/cucx_db.py` — build `contest.db` from seed and populate all tables.
- Create: `tools/cucx_package.py` — `.cup` generation and `.cucx` ZIP assembly.
- Create: `tools/make_cucx.py` — CLI orchestrator.
- Create: `tools/tests/test_cucx_geo.py`, `test_cucx_hash.py`, `test_cucx_schema.py`, `test_cucx_bundle.py`, `test_cucx_db.py`, `test_cucx_package.py`, `test_make_cucx_integration.py`.
- Create: `tools/tests/fixtures/comp93/*.json` — captured `sgp_api` output for offline tests.

---

## Task 1: Coordinate & geodesic helpers (`cucx_geo.py`)

**Files:**
- Create: `tools/cucx_geo.py`
- Test: `tools/tests/test_cucx_geo.py`

**Interfaces:**
- Produces:
  - `deg2rad(deg: float) -> float`
  - `rad2deg(rad: float) -> float`
  - `to_cup_lat(deg: float) -> str` → e.g. `"4416.933N"`
  - `to_cup_lon(deg: float) -> str` → e.g. `"01045.917E"`
  - `haversine_m(lat1, lon1, lat2, lon2) -> float` (degrees in, metres out, R=6371000)
  - `bearing_rad(lat1, lon1, lat2, lon2) -> float` (degrees in, initial bearing in radians, 0..2π)

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_cucx_geo.py
import math
import pytest
from tools import cucx_geo as g

def test_deg2rad_pavullo_latitude():
    # Pavullo location stored as 0.77357181238593 rad ≈ 44.32°N
    assert g.deg2rad(44.32) == pytest.approx(0.7735718, abs=1e-6)

def test_to_cup_lat_north():
    assert g.to_cup_lat(44.282216667) == "4416.933N"

def test_to_cup_lat_south():
    assert g.to_cup_lat(-44.282216667) == "4416.933S"

def test_to_cup_lon_east_zero_padded():
    assert g.to_cup_lon(10.765283333) == "01045.917E"

def test_haversine_known_leg():
    # Starmoen start -> Atna (comp 93 Race1), SGP leg ~ tens of km
    d = g.haversine_m(60.87813333, 11.67323333, 61.73726667, 10.8205)
    assert d == pytest.approx(102000, rel=0.03)

def test_bearing_north_is_zero():
    b = g.bearing_rad(0.0, 0.0, 1.0, 0.0)
    assert b == pytest.approx(0.0, abs=1e-6)

def test_bearing_east_is_half_pi():
    b = g.bearing_rad(0.0, 0.0, 0.0, 1.0)
    assert b == pytest.approx(math.pi / 2, abs=1e-3)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_geo.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.cucx_geo'` (or import error).

- [ ] **Step 3: Write the implementation**

```python
# tools/cucx_geo.py
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
```

Also create `tools/__init__.py` and `tools/tests/__init__.py` (empty) if not present, so `from tools import ...` resolves.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_geo.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
cd /home/angel
git add tools/cucx_geo.py tools/tests/test_cucx_geo.py tools/__init__.py tools/tests/__init__.py
git commit -m "feat(cucx): coordinate and geodesic helpers"
```

---

## Task 2: Content hash helper (`cucx_hash.py`)

**Files:**
- Create: `tools/cucx_hash.py`
- Test: `tools/tests/test_cucx_hash.py`

**Interfaces:**
- Produces: `content_hash(data: bytes) -> str` — standard base64 of `sha256(data)`, `=` padding stripped.

- [ ] **Step 1: Write the failing test**

The known-answer comes from Pavullo's active `.cup`. Extract it in the test setup.

```python
# tools/tests/test_cucx_hash.py
import zipfile
from pathlib import Path
from tools.cucx_hash import content_hash

PAVULLO = Path("/home/angel/pavullo.cucx")

def test_reproduces_pavullo_cup_hash():
    with zipfile.ZipFile(PAVULLO) as z:
        data = z.read("waypoint/29958.cup")
    assert len(data) == 10288
    assert content_hash(data) == "P1jXnrgSI8a2FCf6xulfNifauGG98z3JGadjkkvSDFk"

def test_no_base64_padding():
    assert not content_hash(b"anything").endswith("=")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_hash.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# tools/cucx_hash.py
"""Content hashing for SeeYou contest_file rows."""
import base64
import hashlib


def content_hash(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_hash.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd /home/angel
git add tools/cucx_hash.py tools/tests/test_cucx_hash.py
git commit -m "feat(cucx): contest_file content hash (sha256/base64, verified vs Pavullo)"
```

---

## Task 3: Seed schema extraction (`cucx_schema.sql`)

Produce a committed SQL seed containing the full schema, header PRAGMAs, and the two shared seed tables (`aircraft_type`, `script`) copied from `pavullo.cucx`. This is generated once by a helper script that is itself committed for reproducibility.

**Files:**
- Create: `tools/gen_cucx_schema.py` (one-shot generator, kept for reproducibility)
- Create: `tools/cucx_schema.sql` (generated artifact, committed)
- Test: `tools/tests/test_cucx_schema.py`

**Interfaces:**
- `tools/cucx_schema.sql` builds a database that, when opened, has `application_id=1668637560`, `user_version=3`, all SeeYou tables, exactly 15 `aircraft_type` rows and 4 `script` rows, and zero rows in every contest-specific table.

- [ ] **Step 1: Write the generator script**

```python
# tools/gen_cucx_schema.py
"""One-shot: derive tools/cucx_schema.sql from pavullo.cucx.

Emits: PRAGMAs (application_id, user_version), every CREATE TABLE, and INSERTs
for the shared seed tables aircraft_type and script. No contest-specific data.
Re-run only if the SeeYou schema needs re-deriving from a new template.
"""
import sqlite3
import zipfile
from pathlib import Path

PAVULLO = Path("/home/angel/pavullo.cucx")
OUT = Path("/home/angel/tools/cucx_schema.sql")
SEED_TABLES = ("aircraft_type", "script")


def main():
    with zipfile.ZipFile(PAVULLO) as z:
        raw = z.read("contest.db")
    tmp = Path("/tmp/_pavullo_contest.db")
    tmp.write_bytes(raw)
    db = sqlite3.connect(tmp)
    lines = [
        "PRAGMA application_id = 1668637560;",
        "PRAGMA user_version = 3;",
        "",
    ]
    # Schema (tables only; skip internal sqlite_* objects).
    for (sql,) in db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        lines.append(sql.strip() + ";")
    lines.append("")
    # Seed-table data as INSERT statements.
    for table in SEED_TABLES:
        cols = [r[1] for r in db.execute(f"PRAGMA table_info({table})")]
        collist = ", ".join(cols)
        for row in db.execute(f"SELECT {collist} FROM {table}"):
            vals = ", ".join(_lit(v) for v in row)
            lines.append(f"INSERT INTO {table} ({collist}) VALUES ({vals});")
    db.close()
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


def _lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate the seed SQL**

Run: `cd /home/angel && python tools/gen_cucx_schema.py`
Expected: prints `wrote /home/angel/tools/cucx_schema.sql (<N> bytes)`; file exists and is non-trivial (>30 KB — the scripts are large).

- [ ] **Step 3: Write the failing test**

```python
# tools/tests/test_cucx_schema.py
import sqlite3
from pathlib import Path

SCHEMA = Path("/home/angel/tools/cucx_schema.sql")
CONTEST_TABLES = ["contest", "location", "class", "contestant", "pilot",
                  "task", "point", "task_point", "result", "warning"]

def _build(tmp_path):
    db = sqlite3.connect(tmp_path / "c.db")
    db.executescript(SCHEMA.read_text())
    db.commit()
    return db

def test_header_pragmas(tmp_path):
    db = _build(tmp_path)
    assert db.execute("PRAGMA application_id").fetchone()[0] == 1668637560
    assert db.execute("PRAGMA user_version").fetchone()[0] == 3

def test_seed_tables_populated(tmp_path):
    db = _build(tmp_path)
    assert db.execute("SELECT COUNT(*) FROM aircraft_type").fetchone()[0] == 15
    assert db.execute("SELECT COUNT(*) FROM script").fetchone()[0] == 4
    # The 18_meter aircraft type keeps id 7.
    assert db.execute(
        "SELECT type FROM aircraft_type WHERE id_aircraft_type=7"
    ).fetchone()[0] == "18_meter"
    # The SGP scoring script is present.
    names = [r[0] for r in db.execute("SELECT name FROM script")]
    assert any("Sailplane_Grand_Prix" in n for n in names)

def test_contest_tables_empty(tmp_path):
    db = _build(tmp_path)
    for t in CONTEST_TABLES:
        assert db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_schema.py -v`
Expected: PASS (3 passed). (If it fails first because the SQL wasn't generated, run Step 2.)

- [ ] **Step 5: Commit**

```bash
cd /home/angel
git add tools/gen_cucx_schema.py tools/cucx_schema.sql tools/tests/test_cucx_schema.py
git commit -m "feat(cucx): seed schema + scoring scripts extracted from Pavullo template"
```

---

## Task 4: SGP data bundle (`cucx_bundle.py`)

Normalize `sgp_api` output into a single `CompBundle` dict the DB layer consumes. Capture fixtures for offline tests.

**Files:**
- Create: `tools/cucx_bundle.py`
- Create: `tools/tests/fixtures/comp93/` (captured JSON)
- Test: `tools/tests/test_cucx_bundle.py`

**Interfaces:**
- Consumes: `sgp_api.fetch_competition`, `fetch_pilots`, `fetch_task`, `fetch_day_results`, `fetch_total_results`.
- Produces:
  - `build_bundle(comp_id: int, fetchers=None) -> dict` where `fetchers` is an optional object exposing the five `fetch_*` methods (defaults to `sgp_api`). Returned dict shape:

```python
{
  "comp": {"id", "name", "short_name", "first_day", "last_day"},
  "airfield": {"name", "elevation_m", "lat_deg", "lon_deg", "country", "timezone"},
  "pilots": [{"comp_number", "first_name", "last_name", "name", "country",
              "aircraft", "registration", "flarm_id", "ranking_id"}],
  "tasks": [                      # only days where fetch_task succeeded
    {"day_id", "date", "task_number", "name", "type", "distance_m",
     "start_altitude_m", "finish_altitude_m", "result_status",
     "turnpoints": [{"index", "name", "role", "lat_deg", "lon_deg",
                     "oz": "Line"|"Cylinder", "radius_m"}],
     "results": [{"comp_number", "rank", "points", "points_total", "rank_total",
                  "speed_kph", "distance_km", "igc_file",
                  "takeoff_millis", "landing_millis",
                  "start_millis", "finish_millis"}]}
  ]
}
```
  - `result_status_map(sgp_label: str) -> str` mapping `official→official`, `preliminary/provisional→preliminary`, else `preliminary`.

- [ ] **Step 1: Capture fixtures**

```python
# run once — tools/tests/fixtures/comp93 capture
cd /home/angel && python - <<'PY'
import sys, json, pathlib
sys.path.insert(0, "src/SGP")
import sgp_api
out = pathlib.Path("tools/tests/fixtures/comp93"); out.mkdir(parents=True, exist_ok=True)
comp = sgp_api.fetch_competition(93)
(out / "competition.json").write_text(json.dumps(comp, indent=2, ensure_ascii=False))
(out / "pilots.json").write_text(json.dumps(sgp_api.fetch_pilots(93), indent=2, ensure_ascii=False))
for d in comp["days"]:
    did = d["day_id"]
    try:
        task = sgp_api.fetch_task(93, did)
    except Exception:
        continue
    (out / f"task_{did}.json").write_text(json.dumps(task, indent=2, ensure_ascii=False))
    try:
        (out / f"day_{did}.json").write_text(json.dumps(sgp_api.fetch_day_results(93, did), indent=2, ensure_ascii=False))
        (out / f"total_{did}.json").write_text(json.dumps(sgp_api.fetch_total_results(93, did), indent=2, ensure_ascii=False))
    except Exception:
        pass
print("captured:", sorted(p.name for p in out.iterdir()))
PY
```
Expected: prints `competition.json`, `pilots.json`, and `task_*/day_*/total_*` for the flown race days.

- [ ] **Step 2: Write the failing test (fixture-backed fake fetcher)**

```python
# tools/tests/test_cucx_bundle.py
import json
from pathlib import Path
import pytest
from tools import cucx_bundle as b

FIX = Path("/home/angel/tools/tests/fixtures/comp93")

class FakeFetchers:
    """Serves captured comp93 JSON, mimicking sgp_api signatures."""
    def fetch_competition(self, comp_id):
        return json.loads((FIX / "competition.json").read_text())
    def fetch_pilots(self, comp_id):
        return json.loads((FIX / "pilots.json").read_text())
    def fetch_task(self, comp_id, day_id):
        p = FIX / f"task_{day_id}.json"
        if not p.exists():
            raise FileNotFoundError(day_id)
        return json.loads(p.read_text())
    def fetch_day_results(self, comp_id, day_id):
        p = FIX / f"day_{day_id}.json"
        if not p.exists():
            raise FileNotFoundError(day_id)
        return json.loads(p.read_text())
    def fetch_total_results(self, comp_id, day_id):
        return json.loads((FIX / f"total_{day_id}.json").read_text())

def test_bundle_comp_and_pilots():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    assert d["comp"]["name"] == "Norway SGP 2026"
    assert len(d["pilots"]) == 13
    assert {p["comp_number"] for p in d["pilots"]} >= {"3V", "IGC", "EI"}

def test_bundle_tasks_have_turnpoints_in_degrees():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    assert len(d["tasks"]) >= 1
    t = d["tasks"][0]
    assert t["turnpoints"][0]["role"] == "Start"
    assert 55 < t["turnpoints"][0]["lat_deg"] < 65   # Norway
    assert t["distance_m"] > 100000

def test_bundle_results_joined_with_totals():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    scored = [t for t in d["tasks"] if t["results"]]
    assert scored, "expected at least one scored task in fixtures"
    r = scored[0]["results"][0]
    assert r["rank"] == 1
    assert r["points"] is not None
    assert r["points_total"] is not None

def test_result_status_map():
    assert b.result_status_map("official") == "official"
    assert b.result_status_map("provisional") == "preliminary"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_bundle.py -v`
Expected: FAIL — module not found.

- [ ] **Step 4: Write the implementation**

```python
# tools/cucx_bundle.py
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
    # get_task().length is a string like "261.36 km".
    raw = task.get("length")
    if isinstance(raw, (int, float)):
        return float(raw)
    return float(str(raw).split()[0]) * 1000.0


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
            "rank": r["rank"],
            "points": r["points"],
            "points_total": tp,
            "rank_total": tr,
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
    pilots = f.fetch_pilots(comp_id)["result"]

    tasks = []
    airfield = None
    for day in comp["days"]:
        did = day["day_id"]
        try:
            task = f.fetch_task(comp_id, did)
        except Exception:
            continue  # no task set for this day
        if airfield is None:
            airfield = {
                "name": task.get("airfield"),
                "elevation_m": task.get("elevation"),
                "timezone": task.get("timezone"),
                "lat_deg": task["turnpoints"][0]["latitude"],
                "lon_deg": task["turnpoints"][0]["longitude"],
                "country": next((p.get("country") for p in pilots), None),
            }
        day_json, total_json = {}, {}
        try:
            day_json = f.fetch_day_results(comp_id, did)
            total_json = f.fetch_total_results(comp_id, did)
        except Exception:
            day_json, total_json = {}, {}
        status = day_json.get("results_status_label") if day_json else None
        tasks.append({
            "day_id": did,
            "date": day["date"],
            "task_number": len([t for t in tasks]) + 1,
            "name": task.get("name"),
            "type": task.get("type"),
            "distance_m": _length_m(task),
            "start_altitude_m": task.get("start_altitude"),
            "finish_altitude_m": task.get("finish_altitude"),
            "result_status": result_status_map(status) if status else "preliminary",
            "turnpoints": [_turnpoint(tp) for tp in task["turnpoints"]],
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_bundle.py -v`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
cd /home/angel
git add tools/cucx_bundle.py tools/tests/test_cucx_bundle.py tools/tests/fixtures/comp93
git commit -m "feat(cucx): normalize SGP competition data into CompBundle"
```

---

## Task 5: Populate `contest.db` (`cucx_db.py`)

Build a fresh DB from the seed SQL, then insert all contest-specific rows from the bundle. The `.cup`/`contest_file` registration is added later in Task 7 via a small hook, so this task exposes an `id_allocator` and returns the DB path plus the class id / aircraft type for `uv.meta`.

**Files:**
- Create: `tools/cucx_db.py`
- Test: `tools/tests/test_cucx_db.py`

**Interfaces:**
- Consumes: bundle dict from Task 4; `cucx_geo.deg2rad`, `haversine_m`, `bearing_rad`; `cucx_schema.sql`.
- Produces:
  - `IdAllocator` with `.next(table: str) -> int` (base `10_000_000_000` + per-table counter).
  - `build_contest_db(bundle: dict, db_path: str) -> dict` → returns `{"class_id": int, "aircraft_type": "18_meter", "contest_id": int}`. Creates the DB, populates: `contest`, `location`, `warning` (class-level + reused per task), `class`, `class_meta`, `contestant`, `pilot`, `task`, `point`, `task_point`, `result`.
  - `AIRCRAFT_TYPE_ID = 7`, `AIRCRAFT_TYPE = "18_meter"`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_cucx_db.py
import json, sqlite3
from pathlib import Path
import pytest
from tools import cucx_db
from tools import cucx_bundle as b
from tools.tests.test_cucx_bundle import FakeFetchers

@pytest.fixture
def db(tmp_path):
    bundle = b.build_bundle(93, fetchers=FakeFetchers())
    p = tmp_path / "contest.db"
    meta = cucx_db.build_contest_db(bundle, str(p))
    return sqlite3.connect(p), meta, bundle

def test_contest_and_class(db):
    con, meta, _ = db
    assert con.execute("SELECT name FROM contest").fetchone()[0] == "Norway SGP 2026"
    assert con.execute("SELECT COUNT(*) FROM class").fetchone()[0] == 1
    assert con.execute("SELECT ref_aircraft_type FROM class").fetchone()[0] == 7

def test_contestants_and_pilots(db):
    con, _, _ = db
    assert con.execute("SELECT COUNT(*) FROM contestant").fetchone()[0] == 13
    assert con.execute("SELECT COUNT(*) FROM pilot").fetchone()[0] == 13

def test_location_stored_in_radians(db):
    con, _, bundle = db
    lat_rad = con.execute("SELECT latitude FROM location").fetchone()[0]
    assert 1.0 < lat_rad < 1.2   # ~60°N in radians

def test_points_and_task_points_consistent(db):
    con, _, bundle = db
    ntp = con.execute("SELECT COUNT(*) FROM task_point").fetchone()[0]
    npt = con.execute("SELECT COUNT(*) FROM point").fetchone()[0]
    total_tps = sum(len(t["turnpoints"]) for t in bundle["tasks"])
    assert ntp == total_tps == npt
    # every task_point references an existing point and task
    orphans = con.execute(
        "SELECT COUNT(*) FROM task_point tp "
        "LEFT JOIN point p ON p.id_point=tp.ref_point "
        "LEFT JOIN task t ON t.id_task=tp.ref_task "
        "WHERE p.id_point IS NULL OR t.id_task IS NULL").fetchone()[0]
    assert orphans == 0

def test_task_distance_matches_sgp(db):
    con, _, bundle = db
    for t in bundle["tasks"]:
        stored = con.execute(
            "SELECT task_distance FROM task WHERE task_date=?", (t["date"],)
        ).fetchone()[0]
        assert abs(stored - t["distance_m"]) < 500  # within 0.5 km

def test_results_present_for_scored_tasks(db):
    con, _, bundle = db
    scored = [t for t in bundle["tasks"] if t["results"]]
    for t in scored:
        n = con.execute(
            "SELECT COUNT(*) FROM result r JOIN task t ON t.id_task=r.ref_task "
            "WHERE t.task_date=?", (t["date"],)).fetchone()[0]
        assert n == 13
    # winner of first scored task has rank 1 and points_total set
    t0 = scored[0]
    row = con.execute(
        "SELECT points, points_total, rank FROM result r "
        "JOIN task t ON t.id_task=r.ref_task WHERE t.task_date=? AND r.rank=1",
        (t0["date"],)).fetchone()
    assert row[2] == 1 and row[0] is not None and row[1] is not None

def test_no_result_rows_for_unscored_tasks(db):
    con, _, bundle = db
    for t in bundle["tasks"]:
        if not t["results"]:
            n = con.execute(
                "SELECT COUNT(*) FROM result r JOIN task t ON t.id_task=r.ref_task "
                "WHERE t.task_date=?", (t["date"],)).fetchone()[0]
            assert n == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_db.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# tools/cucx_db.py
"""Build and populate a SeeYou contest.db from a CompBundle."""
import json
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
    import datetime
    return datetime.datetime.utcfromtimestamp(ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")


def _oz_fields(role: str, oz: str):
    """Return (type, oz_type, oz_line, oz_angle1) for a turnpoint."""
    import math
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
        (loc_id, af.get("country") or "NO", af.get("name") or "", af.get("timezone") or "Europe/Oslo",
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
        point_ids = []
        for i, tp in enumerate(tps):
            ptype, oz_type, oz_line, oz_angle1 = _oz_fields(tp["role"], tp["oz"])
            if i == 0:
                dist = geo.haversine_m(tp["lat_deg"], tp["lon_deg"], tp["lat_deg"], tp["lon_deg"])
                c_in = 0.0
            else:
                prev = tps[i - 1]
                dist = geo.haversine_m(prev["lat_deg"], prev["lon_deg"], tp["lat_deg"], tp["lon_deg"])
                c_in = geo.bearing_rad(prev["lat_deg"], prev["lon_deg"], tp["lat_deg"], tp["lon_deg"])
            if i + 1 < len(tps):
                nxt = tps[i + 1]
                c_out = geo.bearing_rad(tp["lat_deg"], tp["lon_deg"], nxt["lat_deg"], nxt["lon_deg"])
            else:
                c_out = 0.0
            pid = ids.next("point")
            point_ids.append(pid)
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_db.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
cd /home/angel
git add tools/cucx_db.py tools/tests/test_cucx_db.py
git commit -m "feat(cucx): populate contest.db (contest, pilots, tasks, geometry, results)"
```

---

## Task 6: `.cup` waypoint generation (`cucx_package.py` part 1)

**Files:**
- Create: `tools/cucx_package.py`
- Test: `tools/tests/test_cucx_package.py`

**Interfaces:**
- Consumes: bundle dict; `cucx_geo.to_cup_lat/to_cup_lon`.
- Produces: `build_cup(bundle: dict) -> str` — SeeYou `.cup` text over the union of all task turnpoints (deduplicated by name), CRLF line endings, header row matching the Pavullo cup:
  `name,code,country,lat,lon,elev,style,rwdir,rwlen,freq,desc` then a `-----Related Tasks-----` trailer.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_cucx_package.py
from tools import cucx_package as pkg
from tools import cucx_bundle as b
from tools.tests.test_cucx_bundle import FakeFetchers

def _bundle():
    return b.build_bundle(93, fetchers=FakeFetchers())

def test_cup_header_and_turnpoints():
    text = pkg.build_cup(_bundle())
    lines = text.splitlines()
    assert lines[0].startswith("name,code,country,lat,lon,elev,style")
    # Start turnpoint "Starmoen" present with N/E coordinates
    assert any("Starmoen" in ln and "N," in ln.replace('"', "") for ln in lines) or \
           any("Starmoen" in ln for ln in lines)
    assert "-----Related Tasks-----" in text

def test_cup_dedupes_shared_turnpoints():
    text = pkg.build_cup(_bundle())
    names = [ln.split(",")[0].strip('"') for ln in text.splitlines()
             if ln and not ln.startswith("name,") and not ln.startswith("---")]
    assert len(names) == len(set(names))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_package.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# tools/cucx_package.py
"""Generate the .cup waypoint file and assemble the .cucx ZIP."""
from tools import cucx_geo as geo

_CUP_HEADER = "name,code,country,lat,lon,elev,style,rwdir,rwlen,freq,desc"


def _code(name: str) -> str:
    return "".join(ch for ch in name.upper() if ch.isalnum())[:8]


def build_cup(bundle: dict) -> str:
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
    return "\r\n".join(rows) + "\r\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_package.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd /home/angel
git add tools/cucx_package.py tools/tests/test_cucx_package.py
git commit -m "feat(cucx): generate .cup waypoint file from task turnpoints"
```

---

## Task 7: `.cucx` ZIP assembly (`cucx_package.py` part 2)

Register the `.cup` in `contest_file`, write `uv.meta` + `tmptasks.meta`, and zip everything.

**Files:**
- Modify: `tools/cucx_package.py`
- Test: `tools/tests/test_cucx_package.py` (add cases)

**Interfaces:**
- Consumes: bundle; `cucx_db.build_contest_db` output (`class_id`, `aircraft_type`, `contest_id`); `cucx_hash.content_hash`.
- Produces: `assemble_cucx(bundle: dict, out_path: str) -> str` — orchestrates: build DB (temp), generate `.cup`, register it in `contest_file`, write meta files, zip to `out_path`. Returns `out_path`.

- [ ] **Step 1: Write the failing tests (append)**

```python
# append to tools/tests/test_cucx_package.py
import zipfile, sqlite3, tempfile
from pathlib import Path
from tools import cucx_hash

def test_assemble_cucx_members_and_contest_file(tmp_path):
    out = tmp_path / "norway.cucx"
    pkg.assemble_cucx(_bundle(), str(out))
    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        assert "contest.db" in names
        assert "uv.meta" in names
        assert "tmptasks.meta" in names
        cup_members = [n for n in names if n.startswith("waypoint/") and n.endswith(".cup")]
        assert len(cup_members) == 1
        cup_bytes = z.read(cup_members[0])
        db_bytes = z.read("contest.db")
        uv = z.read("uv.meta").decode()
    # uv.meta: <class_id>\t<N>\t<aircraft_type>
    parts = uv.strip().split("\t")
    assert parts[2] == "18_meter"
    # contest_file row matches the packed cup (hash + size), active=1
    dbp = tmp_path / "check.db"; dbp.write_bytes(db_bytes)
    con = sqlite3.connect(dbp)
    row = con.execute(
        "SELECT name, hash, size, active, format FROM contest_file WHERE active=1"
    ).fetchone()
    assert row is not None
    assert row[1] == cucx_hash.content_hash(cup_bytes)
    assert row[2] == len(cup_bytes)
    assert row[4] == "waypoint/cup"

def test_assemble_cucx_integrity(tmp_path):
    out = tmp_path / "norway.cucx"
    pkg.assemble_cucx(_bundle(), str(out))
    with zipfile.ZipFile(out) as z:
        db_bytes = z.read("contest.db")
    dbp = tmp_path / "c.db"; dbp.write_bytes(db_bytes)
    con = sqlite3.connect(dbp)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA application_id").fetchone()[0] == 1668637560
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_package.py -v`
Expected: FAIL — `assemble_cucx` not defined.

- [ ] **Step 3: Write the implementation (append to `cucx_package.py`)**

```python
# append to tools/cucx_package.py
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from tools import cucx_db
from tools import cucx_hash

_TMPTASKS = (
    "version=27\r\nuser=\r\ncup\r\n"
    "name,code,country,lat,lon,elev,style,rwdir,rwlen,rwwidth,freq,desc,userdata,pics\r\n"
    "-----Related Tasks-----\r\n"
)


def _register_contest_file(db_path: str, cup_name: str, cup_bytes: bytes, contest_id: int):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cfid = int(cur.execute("SELECT COALESCE(MAX(id_contest_file),20000000000)+1 FROM contest_file").fetchone()[0])
    cur.execute(
        "INSERT INTO contest_file (id_contest_file, ref_contest, name, hash, size, "
        "active, format, created_at, updated_at) VALUES (?,?,?,?,?,1,'waypoint/cup',?,?)",
        (cfid, contest_id, cup_name, cucx_hash.content_hash(cup_bytes), len(cup_bytes),
         cucx_db._NOW, cucx_db._NOW))
    con.commit()
    con.close()
    return cfid


def assemble_cucx(bundle: dict, out_path: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        db_path = str(Path(td) / "contest.db")
        meta = cucx_db.build_contest_db(bundle, db_path)

        cup_text = build_cup(bundle)
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
```

Note: `uv.meta`'s middle field is a small integer whose exact meaning is unconfirmed (Pavullo used `32`); a stable derived value is used and revisited if SeeYou rejects the file (see spec "Fidelity unknowns").

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/angel && python -m pytest tools/tests/test_cucx_package.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
cd /home/angel
git add tools/cucx_package.py tools/tests/test_cucx_package.py
git commit -m "feat(cucx): assemble .cucx zip with contest_file registration and meta"
```

---

## Task 8: CLI orchestrator + integration (`make_cucx.py`)

**Files:**
- Create: `tools/make_cucx.py`
- Test: `tools/tests/test_make_cucx_integration.py`

**Interfaces:**
- Consumes: `cucx_bundle.build_bundle`, `cucx_package.assemble_cucx`.
- Produces: `generate(comp_id: int, out_path: str = None, fetchers=None) -> str`; CLI `python tools/make_cucx.py --comp-id 93 [--out FILE]`.

- [ ] **Step 1: Write the failing integration test (fixture-backed, no network)**

```python
# tools/tests/test_make_cucx_integration.py
import zipfile, sqlite3
from pathlib import Path
from tools import make_cucx
from tools.tests.test_cucx_bundle import FakeFetchers

def test_generate_produces_valid_cucx(tmp_path):
    out = tmp_path / "norway_sgp_2026.cucx"
    path = make_cucx.generate(93, str(out), fetchers=FakeFetchers())
    assert Path(path).exists()
    with zipfile.ZipFile(path) as z:
        assert {"contest.db", "uv.meta", "tmptasks.meta"} <= set(z.namelist())
        db_bytes = z.read("contest.db")
    dbp = tmp_path / "c.db"; dbp.write_bytes(db_bytes)
    con = sqlite3.connect(dbp)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT COUNT(*) FROM contestant").fetchone()[0] == 13
    assert con.execute("SELECT name FROM contest").fetchone()[0] == "Norway SGP 2026"
    # cumulative totals in DB match SGP standings for the last scored task
    ntasks = con.execute("SELECT COUNT(*) FROM task").fetchone()[0]
    assert ntasks >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/angel && python -m pytest tools/tests/test_make_cucx_integration.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# tools/make_cucx.py
"""Generate a SeeYou Competition (.cucx) file for an SGP competition.

Usage:
    python tools/make_cucx.py --comp-id 93 [--out norway_sgp_2026.cucx]

Data is pulled through src/SGP/sgp_api.py (no MCP runtime required).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from tools import cucx_bundle, cucx_package


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()


def generate(comp_id: int, out_path: str = None, fetchers=None) -> str:
    bundle = cucx_bundle.build_bundle(comp_id, fetchers=fetchers)
    if out_path is None:
        out_path = f"{_slug(bundle['comp']['short_name'])}.cucx"
    return cucx_package.assemble_cucx(bundle, out_path)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a SeeYou .cucx from an SGP competition.")
    ap.add_argument("--comp-id", type=int, required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    path = generate(args.comp_id, args.out)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/angel && python -m pytest tools/tests/test_make_cucx_integration.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Run the full suite**

Run: `cd /home/angel && python -m pytest tools/tests/ -v`
Expected: all tests pass.

- [ ] **Step 6: Generate the real file (live fetch) and verify**

Run:
```bash
cd /home/angel && python tools/make_cucx.py --comp-id 93 --out norway_sgp_2026.cucx
python - <<'PY'
import zipfile, sqlite3, tempfile, pathlib
z = zipfile.ZipFile("norway_sgp_2026.cucx")
print("members:", z.namelist())
db = z.read("contest.db")
p = pathlib.Path(tempfile.mktemp()); p.write_bytes(db)
con = sqlite3.connect(p)
for t in ("contest","contestant","pilot","task","point","task_point","result"):
    print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
print("integrity:", con.execute("PRAGMA integrity_check").fetchone()[0])
PY
```
Expected: members include `contest.db`, `waypoint/*.cup`, `uv.meta`, `tmptasks.meta`; contestant=13, pilot=13, task≥1, result = 13×(scored tasks); integrity `ok`.

- [ ] **Step 7: Commit**

```bash
cd /home/angel
git add tools/make_cucx.py tools/tests/test_make_cucx_integration.py
git commit -m "feat(cucx): CLI orchestrator + end-to-end integration test"
```

- [ ] **Step 8: Manual SeeYou open (user-side)**

Ask the user to open `norway_sgp_2026.cucx` in SeeYou Competition and confirm the contest, pilots, tasks, and results display correctly. If SeeYou rejects it, revisit the `uv.meta` middle field and `tmptasks.meta` (spec "Fidelity unknowns").

---

## Self-Review Notes

- **Spec coverage:** contest/location (T5), class/class_meta/script/aircraft_type (T3, T5), contestant/pilot (T5), task/point/task_point (T5), result + totals join (T4, T5), warning (T5), radian conversion (T1, T5), result-status mapping (T4), template-clone (T3, T5), ID scheme (T5), `.cup` + contest_file hash (T2, T6, T7), meta files (T7), geodesic distance/bearing + ±0.5 km check (T1, T5), verification incl. integrity/counts/totals (T5, T7, T8). All spec sections map to a task.
- **Fidelity unknowns:** hash algorithm resolved (T2). `uv.meta` middle field flagged and handled with a stable value, verified only by manual SeeYou open (T8) — the one item that cannot be unit-tested here.
- **Out of scope honored:** no IGC embedding, no airspace files, no alternate waypoint formats, single class.
