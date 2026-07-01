from tools import cucx_package as pkg
from tools import cucx_bundle as b
from tools.tests.test_cucx_bundle import FakeFetchers


def _bundle():
    return b.build_bundle(93, fetchers=FakeFetchers())


def test_cup_header_and_turnpoints():
    text = pkg.build_cup(_bundle())
    lines = text.splitlines()
    assert lines[0].startswith("name,code,country,lat,lon,elev,style")
    assert any("Starmoen" in ln for ln in lines)
    assert "-----Related Tasks-----" in text


def test_cup_dedupes_shared_turnpoints():
    text = pkg.build_cup(_bundle())
    names = [ln.split(",")[0].strip('"') for ln in text.splitlines()
             if ln and not ln.startswith("name,") and not ln.startswith("---")]
    assert len(names) == len(set(names))


import zipfile
import sqlite3
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
    parts = uv.strip().split("\t")
    assert parts[2] == "18_meter"
    dbp = tmp_path / "check.db"
    dbp.write_bytes(db_bytes)
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
    dbp = tmp_path / "c.db"
    dbp.write_bytes(db_bytes)
    con = sqlite3.connect(dbp)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA application_id").fetchone()[0] == 1668637560
