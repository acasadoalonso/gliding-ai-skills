---
name: sgp-report
description: >-
  Generate (or refresh) a succinct .docx competition report for a Sailplane
  Grand Prix (SGP) competition on crosscountry.aero — evolution of the
  competition day by day, number of flights, kilometres flown, and hours
  flown for the field, plus the current top-5 standings. Use whenever the
  user asks for an SGP competition report, a daily/updated SGP report,
  "today's SGP report", or SGP statistics (flights / km / hours) for an event
  such as "Italy SGP 2026" or "Germany SGP 2026". Pulls all data through the
  sgp MCP server only, stores the field aggregates as JSON under
  src/reports/.report_data/sgp-<comp>/, and runs
  tools/make_competition_report.py to write a date-stamped
  reports/SGP.<comp>_competition_report_<date>.docx.
---

# SGP competition report (.docx)

Refresh the field's per-day statistics of an SGP competition through the
**sgp MCP server only** and (re)generate the report using the same renderer
as the `ss-report` skill, `tools/make_competition_report.py`. Designed to be
re-run at any point in the championship — each run overwrites the field JSON
with the latest scored data and writes a new date-stamped `.docx`.

Unlike `ss-report`, an SGP competition has **no classes** — one fleet races
each day — and **no credentials**: the crosscountry.aero SGP REST API behind
the `sgp` MCP server is public. There is no `set_compname` equivalent.

## Arguments

This skill takes one argument:

1. **SGP `comp_id`** — the numeric SGP competition id (e.g. `91` for Italy
   SGP 2026). If the user names a competition instead of giving the number
   (e.g. "Italy SGP 2026", "the German SGP"), call `list_competitions` and
   match it on `title`/`edition_title`, confirm the match if ambiguous, and
   use the resulting `id`. If a numeric id is given directly, confirm it
   with `get_competition(comp_id)` rather than assuming it's valid.

If the competition can't be resolved to a single `comp_id`, ask the user
before proceeding — don't guess.

## Procedure

1. **Resolve the competition.** `get_competition(comp_id)` → name, short
   name, pilot count, and the day index. Each day carries a `day_id` and a
   `type_label` (`Race`, `Practice`, `Rest`, `Cancelled`, `Other`). Only
   `Race` days are competition days — number them 1..N in day-index order.

2. **Get the field.** `get_pilots(comp_id)` → contestant count, and build a
   `competition_number → aircraft` map (needed later for the top-5 "glider"
   column; `get_total_results` standings don't carry aircraft).

3. **Aggregate each Race day** — `get_task_length(comp_id, day_id)` for the
   task name and length (parse `"205.16 km"` → `205.16`), then
   `get_day_results(comp_id, day_id)` for that day's results:
   - `flights` = results with `distance_km > 0` (includes landouts/DNF —
     everyone who logged distance, not just finishers).
   - `finishers` = results with a **numeric** `rank` (non-finishers carry
     `rank: "DNF"` or `"DNS"` and `speed_kph: 0`; do not trust the `finished`
     field — it is `true` even for DNF/DNS entries in observed data).
   - `km_flown` = sum of `distance_km` over **all** entries with
     `distance_km > 0` (finishers and landouts) — matches `ss-report`'s "sum
     of scored task distances per pilot per day".
   - `hours_flown` = sum of `task_time_seconds / 3600` over **finishers
     only**. SGP gives no elapsed time for non-finishers (`task_time_seconds:
     0`), unlike SoaringSpot, so there is no landout-hours estimate to make —
     say so in `hours_method`.
   - `winner` = the rank-1 result (`name`, `points`, `speed_kph` → `speed_kmh`).
   - `status` = `results_status_label` (`preliminary`/`unofficial`/
     `official`) from the day payload; use `"cancelled"` if the day index
     itself marked the day `Cancelled`, or `"pending"`/zero values if a Race
     day has no results yet (in progress).

4. **Get the standings.** `get_total_results(comp_id, last_race_day_id)` →
   ranked cumulative points. Take the top 5, joining each pilot's aircraft
   from step 2 for the "glider" column.

5. **Write the data files** to
   `src/reports/.report_data/sgp-<slug>/` (slug from the competition's short
   name, e.g. `italy-sgp-2026`):
   - `meta.json`: `{"comp", "title", "subtitle", "class_files": ["field.json"],
     "methodology": "...", "source_label": "SGP (crosscountry.aero)"}`. Set
     `methodology` to name the `sgp` MCP tools actually used (get_competition,
     get_pilots, get_task_length, get_day_results, get_total_results) — the
     renderer's default methodology text names the soaringspot MCP and would
     be wrong here.
   - `field.json`: one "class" entry (`class` = competition name) in the
     exact schema `make_competition_report.py` expects (`class`,
     `contestants`, `days[]`, `top5[]`, `hours_method`) — see its docstring,
     or the JSON files in `.report_data/24-fai-egc/` for the shape.

6. **Generate the .docx.** Same venv and script as `ss-report`:

   ```bash
   /home/angel/.venv-report/bin/python /home/angel/tools/make_competition_report.py \
     --data-dir /home/angel/src/reports/.report_data/sgp-<slug> \
     --out /home/angel/src/reports/SGP.<slug>_competition_report_<YYYY-MM-DD>.docx
   ```

   (`--out` must be given explicitly — the script's default filename prefix
   is `SS.`, for the SoaringSpot skill.)

7. **Report the outcome.** Give the user the output path, the per-day and
   overall totals (flights / km / hours), the current top 5, and flag any
   preliminary, unofficial, cancelled, or not-yet-flown days.

## Notes

- If the venv is missing, recreate it:
  `python3 -m venv /home/angel/.venv-report && /home/angel/.venv-report/bin/pip install python-docx`.
- `make_competition_report.py` is shared with `ss-report`; its `meta.json`
  now supports two optional overrides used by this skill —
  `methodology` (the Methodology-section paragraph) and `source_label` (the
  "generated from ... data on ..." status line, which otherwise defaults to
  "SoaringSpot"). Both are additive and don't change `ss-report`'s output
  when absent.
- Days whose results are `unofficial`/`preliminary` will change on later
  runs — always re-fetch every Race day, not just the newest one.
- No credentials are needed; the `sgp` MCP server queries the public
  crosscountry.aero API directly by `comp_id`.
