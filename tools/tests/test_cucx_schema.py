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
