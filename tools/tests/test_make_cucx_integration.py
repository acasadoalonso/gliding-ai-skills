import zipfile
import sqlite3
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
    dbp = tmp_path / "c.db"
    dbp.write_bytes(db_bytes)
    con = sqlite3.connect(dbp)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT COUNT(*) FROM contestant").fetchone()[0] == 13
    assert con.execute("SELECT name FROM contest").fetchone()[0] == "Norway SGP 2026"
    ntasks = con.execute("SELECT COUNT(*) FROM task").fetchone()[0]
    assert ntasks >= 1
