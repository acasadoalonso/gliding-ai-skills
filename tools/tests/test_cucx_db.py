import sqlite3
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
    known = {p["comp_number"] for p in bundle["pilots"]}
    scored = [t for t in bundle["tasks"] if t["results"]]
    for t in scored:
        n = con.execute(
            "SELECT COUNT(*) FROM result r JOIN task t ON t.id_task=r.ref_task "
            "WHERE t.task_date=?", (t["date"],)).fetchone()[0]
        expected = sum(1 for r in t["results"] if r["comp_number"] in known)
        assert n == expected
        if t["result_status"] == "official":
            assert n == 13
    # The winner of the first official race must have rank 1 and populated points.
    official = next(t for t in scored if t["result_status"] == "official")
    row = con.execute(
        "SELECT points, points_total, rank FROM result r "
        "JOIN task t ON t.id_task=r.ref_task WHERE t.task_date=? AND r.rank=1",
        (official["date"],)).fetchone()
    assert row[2] == 1 and row[0] is not None and row[1] is not None


def test_every_result_links_to_contestant(db):
    con, _, _ = db
    orphans = con.execute(
        "SELECT COUNT(*) FROM result r "
        "LEFT JOIN contestant c ON c.id_contestant=r.ref_contestant "
        "WHERE c.id_contestant IS NULL").fetchone()[0]
    assert orphans == 0
