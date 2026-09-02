---
name: gen_cucx_from_sgp
description: Generate a SeeYou Competition .cucx file from a Sailplane Grand Prix (SGP) competition on crosscountry.aero. Use this whenever the user wants to build, create, export, or generate a .cucx (SeeYou Competition file) from an SGP comp, load an SGP competition into SeeYou, or turn SGP tasks/pilots/results into a SeeYou-importable file — even if they only mention "the cucx", "SeeYou file", or "SGP export" without spelling out every step. Takes two arguments — the .cucx file name and the SGP competition id — then runs tools/make_cucx.py to produce a .cucx whose .cup waypoint file carries both the task definitions and their turnpoints.
---

# Generate a .cucx from an SGP competition

Build a SeeYou Competition `.cucx` from a Sailplane Grand Prix competition using
`tools/make_cucx.py`. That script pulls the comp, pilots, tasks, and results
straight through `src/SGP/sgp_api.py` (no MCP runtime needed) and assembles the
`.cucx`. Your job is to gather the two arguments it needs and run it.

## Arguments

This skill takes two positional arguments, in this order:

1. **`.cucx` file name** — the output file name (e.g. `norway_sgp_2026.cucx`).
   Add the `.cucx` extension if the user left it off.
2. **SGP competition id** — the SGP `comp_id` (e.g. `93`). If the user names a
   competition instead of a number, run `python3 src/SGP/sgp_api.py` helpers or
   the `sgp` MCP `list_competitions` to find the matching `comp_id`, then confirm
   it with the user.

If either argument is missing from the invocation, ask the user for it before
running — don't guess a file name or a competition id.

The task day is not an argument to this skill; it always builds `ALL` scored
days into the `.cup` (see below for what that controls).

## Observation zones

The tool always writes the same zones, overriding whatever observation zone SGP
publishes for the task:

| Point       | Zone     | `R1`             | `A1` | `Line` |
|-------------|----------|------------------|-----:|-------:|
| Start       | Line     | `2500m` (5 km)   | 180  | 1      |
| Turnpoints  | Cylinder | radius from SGP  | 360  | 0      |
| Finish      | Line     | `250m` (500 m)   | 180  | 1      |

Start and finish are **always** lines (`A1=180`, `Line=1`); every other
turnpoint is **always** a cylinder (`A1=360`, `Line=0`), keeping only the radius
SGP publishes. The line half-lengths live in `tools/cucx_bundle.py`
(`START_LINE_R1_M` / `FINISH_LINE_R1_M`) and the zone shapes in
`tools/cucx_db.py` (`_oz_fields`); both are applied once, so the `.cup`
`OBSZONE` lines and `contest.db`'s `point` rows agree.

## What the day selection controls

The `--day` value only decides **which task lines go into the `.cup` Related
Tasks section**. The `contest.db` inside the `.cucx` always contains every day's
task, contestants, and results — narrowing to one day never drops data from the
database, it just focuses the waypoint file's task list on that day.

Each `.cup` task line is the task label followed by its ordered turnpoint names,
and every one of those turnpoints is also emitted as a waypoint above, so SeeYou
resolves the task geometry back to the waypoint database. This is the "tasks +
waypoints in the `.cup`" behavior the tool guarantees.

## Run it

From the repo root (`/home/angel`):

```bash
python3 tools/make_cucx.py --comp-id <ID> --out <name>.cucx
```

`--day` is left at its `ALL` default. The script prints `wrote <path>` on
success. Report that path to the user.

## Verify before claiming success

The `.cucx` is a ZIP; confirm it is well-formed rather than assuming:

```bash
python3 - <<'PY'
import zipfile, sqlite3, tempfile, pathlib
f = "<path>.cucx"
z = zipfile.ZipFile(f)
print("members:", z.namelist())
cup = [n for n in z.namelist() if n.endswith(".cup")][0]
print(z.read(cup).decode().split("-----Related Tasks-----")[1].strip())
db = tempfile.mktemp(suffix=".db")
pathlib.Path(db).write_bytes(z.read("contest.db"))
con = sqlite3.connect(db)
print("integrity:", con.execute("PRAGMA integrity_check").fetchone()[0])
print("app_id:", con.execute("PRAGMA application_id").fetchone()[0])  # expect 1668637560
print("tasks:", con.execute("SELECT COUNT(*) FROM task").fetchone()[0])
PY
```

Expect `integrity: ok`, `app_id: 1668637560`, the four members
(`contest.db`, `waypoint/<id>.cup`, `uv.meta`, `tmptasks.meta`), and the task
line(s) matching the day selection. The one thing not checkable here is whether
SeeYou Competition actually opens the file — if the user can open it, that closes
the loop.

## Tested

Verified 2026-08-08 against a live SGP competition with the two-argument
invocation: `--comp-id 94 --out /nfs/tmp/germany_sgp_2026.cucx` (Germany SGP
2026). Output passed the verification check above — `integrity: ok`, `app_id:
1668637560`, the expected four members, and 3 tasks in `contest.db` with the
practice-day task's turnpoint chain present in the `.cup`.

Zones re-verified 2026-09-02 on the same comp (`--comp-id 94`): across the 72
`OBSZONE` lines of the 10 tasks the only shapes are
`Style=2,A1=180,Line=1` (start), `Style=3,A1=180,Line=1` (finish) and
`Style=1,A1=360,Line=0` (turnpoints); `contest.db`'s `point` rows match —
`oz_angle1` pi with `oz_line=1` for the 10 starts and 10 finishes, 2*pi with
`oz_line=0` for the 52 turnpoints.

## Format & gotchas (for debugging)

`references/cucx_format.md` documents the `.cucx` ZIP/SQLite layout, the
radian-vs-`DDMM.mmm` coordinate split, the content-hash rule, and the SGP data
quirks the tool already handles (empty future days, `DNS` ranks, stray practice
entrants, shared scoring scripts). Read it only if a run fails or the output
looks wrong — the happy path doesn't need it.
