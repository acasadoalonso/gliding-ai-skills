# .cucx format & SGP data gotchas

Reference for debugging `tools/make_cucx.py` output. The happy path does not
need this file.

## Modules

`make_cucx.py` orchestrates; the work lives in:
`cucx_geo` (coordinates), `cucx_hash` (content hash), `cucx_bundle` (fetch +
normalize SGP into a bundle dict), `cucx_db` (build `contest.db`),
`cucx_package` (build the `.cup` and assemble the ZIP). The DB is seeded from
`cucx_schema.sql`, regenerated via `gen_cucx_schema.py`. Tests plus comp-93
fixtures live under `tools/tests/`.

## The `.cucx` file — a ZIP containing

- **`contest.db`** — SQLite. Header `application_id=1668637560`,
  `user_version=3`. FK chain: contest→location; class→contest/aircraft_type/
  warning; contestant→class; pilot→contestant; task→class/script/warning;
  task_point→task/point; result→contestant/task. Always holds **every** day,
  regardless of the `--day` selection.
- **`waypoint/<id>.cup`** — the active waypoint file, registered in the
  `contest_file` table with `active=1`. Contains the waypoint list plus a
  `-----Related Tasks-----` section with one line per selected day (task label +
  ordered turnpoint names). **hash = `base64(sha256(bytes))` with `=` padding
  stripped**; `size` = raw byte length.
- **`uv.meta`** — TSV `<class_id>\t<N>\t<aircraft_type>`. The middle field's
  meaning is UNCONFIRMED (Pavullo used 32); only validatable by opening in SeeYou.
- **`tmptasks.meta`** — CUP-format scratch tasks; a minimal header suffices.

## Coordinates

`point`/`location` rows in the DB store coordinates in **radians** (deg × π/180).
The `.cup` file uses `DDMM.mmm` + hemisphere. `cucx_geo` handles both conversions.

## SGP data quirks (already handled by the tool)

- SGP returns empty tasks (0 turnpoints, `length=None`) and `rank:"DNS"` rows for
  future/unflown days — days with no turnpoints are skipped; non-int ranks are
  coerced to `None`.
- Practice days may include a stray entrant not in `get_pilots` (comp 93 had
  `LZ`) — results with no matching contestant are skipped.
- The 4 `(default)` scoring scripts (incl. `Sailplane_Grand_Prix`) are shared
  across contests and ship in the seed schema; race tasks reference the SGP one.

## Template

`tools/pavullo.cucx` (SGP Final Serie XI, 18m) is an example produced by SeeYou —
useful for byte-level comparison when a generated file won't open.
