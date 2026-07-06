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
    wpt_section = text.split("-----Related Tasks-----")[0]
    names = [ln.split(",")[0].strip('"') for ln in wpt_section.splitlines()
             if ln and not ln.startswith("name,")]
    assert len(names) == len(set(names))


def _tasks_section(text):
    return text.split("-----Related Tasks-----")[1]


def test_cup_all_days_emit_one_task_line_each():
    bundle = _bundle()
    tasks = _tasks_section(pkg.build_cup(bundle))
    lines = [ln for ln in tasks.splitlines() if ln.strip()]
    assert len(lines) == len(bundle["tasks"])  # comp93 has 6 tasks
    # each line: task label followed by its ordered turnpoint names
    race1 = next(ln for ln in lines if ln.startswith('"Race1"'))
    assert '"Starmoen"' in race1 and '"Hernes krk"' in race1


def test_cup_single_day_emits_only_that_task():
    bundle = _bundle()
    # task_number 3 is Race1 in the comp93 fixture
    tasks = _tasks_section(pkg.build_cup(bundle, days=3))
    lines = [ln for ln in tasks.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert lines[0].startswith('"Race1"')


def test_single_day_cucx_keeps_all_days_in_db(tmp_path):
    # DB always carries every day; --day only narrows the .cup task section.
    out = tmp_path / "day3.cucx"
    pkg.assemble_cucx(_bundle(), str(out), days=3)
    with zipfile.ZipFile(out) as z:
        db_bytes = z.read("contest.db")
        cup = z.read([n for n in z.namelist() if n.endswith(".cup")][0]).decode()
    dbp = tmp_path / "d.db"
    dbp.write_bytes(db_bytes)
    con = sqlite3.connect(dbp)
    assert con.execute("SELECT COUNT(*) FROM task").fetchone()[0] == 6
    assert len(_tasks_section(cup).split("\r\n")[1:-1]) == 1


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
