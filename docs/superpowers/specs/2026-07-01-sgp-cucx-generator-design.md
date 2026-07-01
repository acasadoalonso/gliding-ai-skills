# SGP → SeeYou `.cucx` Generator — Design Spec

**Date:** 2026-07-01
**Author:** Angel (with Claude Code)
**Status:** Approved for planning

## Goal

Build a reusable Python script, `tools/make_cucx.py`, that produces a SeeYou
Competition (`.cucx`) file for an SGP competition by pulling its data through the
`sgp` MCP server. The first target is **competition 93 — Norway SGP 2026**.

Success = the generated `.cucx` opens cleanly in SeeYou Competition and contains
the contest structure, pilots, race tasks (with turnpoint geometry), and scored
results for the flown race days.

## Decisions (locked)

- **Data scope:** Structure **plus** results. Include per-task points, ranks,
  and cumulative totals for flown race days. Do **not** embed IGC log files, but
  do populate `result.igc_file` with the SGP-reported filename string.
- **Fidelity:** Must open in SeeYou Competition — replicate radian coordinates,
  internally-consistent BIGINT foreign keys, embedded scoring scripts, and valid
  `.meta` files.
- **Deliverable:** Reusable script `tools/make_cucx.py`, parameterised by
  `comp_id`, writing `<short_name>.cucx`.

## Background: the `.cucx` format (verified from `pavullo.cucx`)

A `.cucx` is a ZIP archive containing:

| Member | Purpose |
|---|---|
| `contest.db` | SQLite database — the core. `application_id=1668637560`, `user_version=3`. |
| `waypoint/<id>.cup` | The active SeeYou `.cup` waypoint file, registered in `contest_file` (`active=1`) with a base64 hash. |
| `uv.meta` | One TSV line: `<class_id>\t<N>\t<aircraft_type>` (Pavullo: `8539\t32\t18_meter`). |
| `tmptasks.meta` | CUP-format scratch tasks (non-essential; a minimal valid header suffices). |

### Key schema facts

- Coordinates in `point` and `location` are stored in **radians** (decimal
  degrees × π/180), not degrees.
- Foreign-key chain:
  `contest → location`; `class → contest`, `class → aircraft_type`,
  `class → warning`; `contestant → class`; `pilot → contestant`;
  `task → class`, `task → script`, `task → warning`;
  `task_point → task`, `task_point → point`; `result → contestant`,
  `result → task`.
- Four `script` rows are `(default)` scoring scripts shared across all contests
  (`Sailplane_Grand_Prix`, `IGC_Annex_A_scoring_2022`, `FFVP_2023`,
  `eGlide_Elapsed_time_scoring`). Race tasks reference `Sailplane_Grand_Prix`.
- `class_meta` holds 16 key/value SGP scoring parameters (`ftv_factor`,
  `nominal_distance`, `nominal_time`, `score_back_time`, …).
- `aircraft_type` is a fixed 15-row seed table; `18_meter` has `id=7`.

## SGP MCP data sources (verified for comp 93)

| MCP tool | Provides |
|---|---|
| `get_competition(93)` | Name, short name, dates, per-day index (`day_id`, date, type: Practice/Race). |
| `get_pilots(93)` | first/last name, comp number, country, aircraft, registration, flarm_id, IGC ranking_id. |
| `get_task(93, day_id)` | task id/name/type, length, airfield + elevation, timezone, start/finish altitude, start time, ordered turnpoints (lat/lon in **degrees**, role, OZ type Line/Cylinder, radius). |
| `get_day_results(93, day_id)` | results status, per-pilot rank, points, speed_kph, distance_km, task_time, start/finish time millis, igc_file. |
| `get_total_results(93, day_id)` | cumulative standings (total_points, rank) as of that day. |

## Field mapping

### `contest` / `location`
- `contest`: name, `start_date`/`end_date` from competition span, `country=NO`,
  `time_zone=Europe/Oslo` (from task), `category=any`, `live_track_type=none`.
- `location`: from the task airfield ("Elverum Starmoen"), elevation, country,
  continent `EU`; lat/lon converted to **radians**.

### `class` / `class_meta` / `script` / `aircraft_type`
- One `class`, `ref_aircraft_type=7` (`18_meter`), `ref_contest`→contest,
  `ref_warning`→a class-level warning row.
- `class_meta`: copy the 16 SGP default key/values from the Pavullo template.
- `script` (4) and `aircraft_type` (15): copied verbatim from the template.

### `contestant` / `pilot` (13 rows each)
- `contestant`: `name`, `aircraft_model`←aircraft, `contestant_number`←comp
  number, `aircraft_registration`←registration, `handicap=100.0`,
  `flight_recorders`←flarm_id (JSON/CLOB), `ref_class`.
- `pilot`: `first_name`, `last_name`, `nationality`←country, `igc_id`←ranking_id,
  `ref_contestant`.

### `task` / `point` / `task_point` (per flown race day with a task)
- `task`: `task_date`, `task_number` (race sequence), `task_type=polygon`,
  `task_name`←task name, `task_distance`←length (metres),
  `result_status` mapped from SGP status (see mapping below),
  `ref_class`, `ref_script`→`Sailplane_Grand_Prix`, `ref_warning`, plus the
  non-null structural columns (`distance_calculation=waypoints`,
  `uncompleted_calculation`, tolerances, `start_on_entry`, `multiple_starts`,
  `task_version`, …) populated from template defaults.
- `point`: one per turnpoint. lat/lon → **radians**. `type` by role
  (start/point/finish). `oz_type`: start=`next`, turnpoint=`symmetric`,
  finish=`previous`. `oz_line=1` for Line OZ (start/finish), else 0.
  `oz_radius1`←radius, `oz_angle1=π`. `distance`, `course_in`, `course_out`
  computed geodesically per leg.
- `task_point`: ordered `point_index` linking task→point.

### `result` (13 × flown race day)
- Join `get_day_results` (per-day) with `get_total_results` (cumulative) by
  `pilot_id`/`competition_number`, and to contestants by comp number.
- `points`←day points, `points_total`←cumulative total, `rank`←day rank,
  `rank_total`←cumulative rank, `calculated_speed`←speed_kph,
  `calculated_distance`←distance_km×1000, `takeoff`/`landing`/`calculated_start`/
  `calculated_finish` from millis, `igc_file`←SGP filename string.

### `warning`
- Populated from the task's `start_altitude` (→ `start_altitude`) and
  `finish_altitude` (→ `min_finish_altitude`); other fields from template defaults.

### Result-status mapping
| SGP `results_status_label` | SeeYou `task.result_status` | Result rows emitted? |
|---|---|---|
| official | official | yes |
| preliminary / provisional | preliminary | yes |
| task set, not yet scored | preliminary | no |
| practice day | practice | yes if scored, else none |

A day only yields a `task` row when `get_task` returns a task. It only yields
`result` rows when `get_day_results` returns scored results. Future/unset days
are skipped entirely — no `task`, no `result`.

## Build approach — template-clone

Copy the Pavullo `contest.db` to use as a schema skeleton. This guarantees the
exact schema, PRAGMAs, `application_id`, `user_version`, the four embedded
`(default)` scoring scripts, and the `aircraft_type` seed rows. Then:

1. `DELETE` all contest-specific rows (`contest`, `location`, `class`,
   `class_meta`, `class_start`, `contestant`, `contestant2category`, `pilot`,
   `task`, `task_point`, `task_changelog`, `point`, `result`, `result_start`,
   `leg`, `leg_timeout`, `warning`, `contest_file`, `task_image`).
2. Keep `aircraft_type` and `script`.
3. Re-populate every table from comp 93 data.

(Alternative — build the schema from scratch with `CREATE TABLE` — rejected:
higher risk that embedded scripts/pragmas differ from what SeeYou expects.)

## ID scheme

Reuse Naviter's large-BIGINT style: a fixed base offset plus a per-table
sequential counter, keeping foreign keys internally consistent. Values need only
be unique and consistent within the file, not match any server-side IDs.

## Waypoint file + `contest_file`

- Generate `waypoint/<id>.cup` from the union of all task turnpoints (SeeYou
  `.cup` format: `name,code,country,lat,lon,elev,style,...`; lat/lon in
  `DDMM.mmm` hemisphere format).
- Register it in `contest_file` with `active=1`, `format=waypoint/cup`, correct
  `size`, and the content hash.

## Fidelity unknowns — resolved empirically

1. **`contest_file` hash algorithm.** The 43-char base64 hash implies
   SHA-256/base64. Confirm by reproducing Pavullo's existing hash
   (`P1jXnrgSI8a2FCf6xulfNifauGG98z3JGadjkkvSDFk`) from `waypoint/29958.cup`
   before writing any new file. Determine standard vs. url-safe base64 and
   whether padding is stripped.
2. **`uv.meta` middle field (`32`).** Meaning unknown (not the contestant
   count). Replicate the field's structure, test-open in SeeYou, and flag if it
   proves significant.

## Geodesic computation

Compute per-leg great-circle `distance` (metres) and `course_in`/`course_out`
(bearings, radians) for each `point`. Sum of leg distances must match the
SGP-reported task length within ±0.5 km; otherwise flag.

## Verification strategy

1. **Hash check:** reproduce Pavullo's `.cup` hash → confirms the algorithm.
2. **Integrity:** `PRAGMA integrity_check`; every FK resolves; no orphan
   `task_point`/`result`/`pilot`.
3. **Counts:** 13 contestants, 13 pilots, one `task` per flown race day, 13
   `result` rows per flown task.
4. **Distance:** each task's summed leg distance ≈ SGP length (±0.5 km).
5. **Totals:** `result.points_total` for the last flown day equals the
   `get_total_results` standings.
6. **Round-trip:** re-extract the generated `.cucx` and re-run the SQLite checks.
7. **Manual:** open in SeeYou Competition (user-side) to confirm it loads.

## Out of scope

- Embedding IGC flight logs.
- Airspace files (`.cub`/OpenAIR) — the Pavullo example includes them, but they
  are not required and not available from the SGP MCP.
- Alternative waypoint export formats (`.da4`, `.gpx`, `.dbt`, `.ndb`, `.wpz`,
  `.dat`) — only the active `.cup` is generated.
- Multi-class contests (SGP is single-class).
