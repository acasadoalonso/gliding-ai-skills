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


def _lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


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


if __name__ == "__main__":
    main()
