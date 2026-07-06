---
name: gen_cucx_from_sgp
description: Generate a SeeYou Competition .cucx file from a Sailplane Grand Prix (SGP) competition on crosscountry.aero. Use this whenever the user wants to build, create, export, or generate a .cucx (SeeYou Competition file) from an SGP comp, load an SGP competition into SeeYou, or turn SGP tasks/pilots/results into a SeeYou-importable file — even if they only mention "the cucx", "SeeYou file", or "SGP export" without spelling out every step. The skill prompts for the SGP competition number and the day (a specific day number or ALL), then runs tools/make_cucx.py to produce a .cucx whose .cup waypoint file carries both the task definitions and their turnpoints.
---

# Generate a .cucx from an SGP competition

Build a SeeYou Competition `.cucx` from a Sailplane Grand Prix competition using
`tools/make_cucx.py`. That script pulls the comp, pilots, tasks, and results
straight through `src/SGP/sgp_api.py` (no MCP runtime needed) and assembles the
`.cucx`. Your job is to gather the two inputs it needs and run it.

## Inputs to collect

Ask the user for both before running, unless they already gave them:

1. **Competition number** — the SGP `comp_id` (e.g. `93`). If the user names a
   competition instead of a number, run `python3 src/SGP/sgp_api.py` helpers or
   the `sgp` MCP `list_competitions` to find the matching `comp_id`, then confirm
   it with the user.
2. **Day** — a specific day number **or** `ALL` (the default). The day number is
   the 1-based competition day as shown in the results ("Day 3"), counting only
   days that actually have a task. `ALL` writes every scored day's task into the
   `.cup`.

If the user is vague ("just make the cucx"), assume `ALL` and say so, but still
confirm the competition number — getting that wrong wastes the whole run.

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
# all scored days
python3 tools/make_cucx.py --comp-id <ID>

# a single day (e.g. day 3), optional explicit output name
python3 tools/make_cucx.py --comp-id <ID> --day 3 --out <name>.cucx
```

`--day` accepts `ALL` (default) or an integer. When `--out` is omitted the file
is named from the competition's short name (e.g. `norway_sgp_2026.cucx`). The
script prints `wrote <path>` on success. Report that path to the user.

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

## Format & gotchas (for debugging)

`references/cucx_format.md` documents the `.cucx` ZIP/SQLite layout, the
radian-vs-`DDMM.mmm` coordinate split, the content-hash rule, and the SGP data
quirks the tool already handles (empty future days, `DNS` ranks, stray practice
entrants, shared scoring scripts). Read it only if a run fails or the output
looks wrong — the happy path doesn't need it.
