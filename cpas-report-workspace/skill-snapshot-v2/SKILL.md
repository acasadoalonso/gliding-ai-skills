---
name: cpas-report
description: >-
  Generate a .docx summary report for a gliding competition using ONLY the
  cpas MCP server — days flown, flights per day, airspace incursions per day
  and per class, proximity encounters, per-day weather, and flight-recorder
  validation notes. Use whenever the user asks for a CPAS report, a
  safety/incursion/encounter summary, "how many incursions", "how many days
  were flown", or a competition summary "using the cpas MCP" for a comp
  hosted on CPAS (e.g. 2026 EGC / 24th-fai-egc, 2026 WGC, FCC, SGP events) —
  even if they don't say "report" explicitly. Aggregates the CPAS analysis
  JSON with jq, stores the aggregates under src/reports/.report_data/, and
  runs tools/make_cpas_report.py to write
  src/reports/CPAS.<comp>_summary_report_<date>.docx. Not for SoaringSpot-only
  statistics reports (flights/km/hours per class) — that is competition-report.
---

# CPAS competition summary report (.docx)

Build a competition summary from the **cpas MCP server only** (tools
`mcp__cpas__competition`, `mcp__cpas__environment`, `mcp__cpas__segment`) and
render it with `tools/make_cpas_report.py`. CPAS holds flight-safety analysis
(proximity encounters, airspace incursions, terrain clearance), per-day
weather, and IGC ingestion metadata — it is NOT SoaringSpot: it has no
scores, standings, or (usually) task/class definitions.

## Inputs to collect

1. **Competition name** — match it loosely against `competition(type=list)`
   (entries carry `name`, a UUID `key`, and a `soaringSpot` slug). "EGC2026",
   "the EGC", "24th european championship" all → the entry named "2026 EGC".

## Critical API facts (learned the hard way)

- Every endpoint except `list` requires the **UUID `key`** as `comp`.
  Passing the slug or the display name returns HTTP 403 "Access denied" —
  that is an identifier problem, not a permissions problem.
- `competition(type=analysis)` on a populated comp is **huge** (1–4 MB). The
  tool result gets saved to a file under `tool-results/`; query that file
  with `jq`, never try to read it whole.
- **Incursions ≠ encounters.** CPAS `incursions` are airspace-violation
  events; `encounters` are close-proximity events between gliders (30 m
  threshold). Users often say "incursions" loosely — report both, clearly
  labelled, and never present encounter counts as incursions.
- If `settings` shows `incursions: false` (or `terrain: false`) that
  analysis is disabled and its per-day arrays will be empty. Report the
  count as 0 **with the caveat that the analysis was switched off** — a
  disabled detector is not evidence of a clean competition.
- Task/class names are **case-sensitive display names**: `Club`,
  `Standard`, `Open`, `18 Metre` work; `club`, `standard`, `18m` all 404.
  A 404 means you probed the wrong name, not that task data is absent —
  try capitalised SoaringSpot-style names before concluding anything.
- Even with task data, **encounter/incursion records carry competition
  numbers but no class labels**, so per-class event attribution is only
  possible indirectly (e.g. a day on which a single class flew).
- If `analysis` returns `days: []`, the comp is registered but not yet
  ingested (check `autoFetch` in settings). Still produce the report,
  documenting the absence of data and its likely cause.
- Name the contest site from `flight_location` coordinates carefully —
  look it up rather than guessing a famous gliding airfield nearby, or
  just quote the coordinates (51.70 N 17.85 E is Michałków / Ostrów
  Wielkopolski, not Leszno).

## Procedure

1. **Find the competition.** `competition(type=list)` → match name → note
   the UUID `key`, slug, and country.

2. **Settings.** `competition(type=settings, comp=<key>)` → folder, time
   zone, `autoFetch`, `incursions` + `incursion_threshold`, `terrain` +
   `terrain_clearance`, `competitionEnded`, `foundFiles`, `purgeAfter`.

3. **Analysis.** `competition(type=analysis, comp=<key>)`. Expect the
   oversized-result path; then aggregate with jq, e.g.:

   ```bash
   jq -r '.data.days[] | [.day, (.flights|length), (.encounters|length),
          (.incursions|length), (.terrainClearances|length)] | @tsv' $F
   jq '.data.days[0].flight_location, .data.bounding_box' $F
   jq -r '.data.days[] | [.day, .flight_location.alt_max] | @tsv' $F   # climb ceiling per day
   jq -r '.data.totals.aircraft | to_entries | sort_by(-.value.count)
          | .[0:5][] | [.key, .value.count] | @tsv' $F                 # encounter leaders (CNs)
   jq '[.data.days[].flights | length] | add' $F                       # total flights
   ```

   If any day's `incursions` array is non-empty, drill into each event with
   `segment(type=incursion, comp, day, item=<event id>, index="0")` and
   break counts down per day (and per class only if class membership is
   actually derivable). Also note reviewed encounters (`comment.status`
   set, e.g. tagged "Team").

4. **Validation.** `competition(type=validation, comp=<key>)` → flight-
   recorder anomalies (type/version/`correction_suggest`/`num`) for the
   data-quality section.

5. **Weather.** `environment(type=weather, comp=<key>)` → `byDay` map from
   open-meteo with per-day `weather_code` (WMO), max/min temperature,
   precipitation sum/hours, max wind speed + dominant direction, plus
   `fetchedAt`. Decode WMO codes: 0 clear, 1–3 partly cloudy, 45/48 fog,
   51/53/55 light/moderate/dense drizzle, 61/63/65 light/moderate/heavy
   rain, 80–82 showers, 95+ thunderstorm. Convert dominant wind bearing to
   a compass point. Write a short narrative of the forecast evolution
   (early/mid/late phases), and correlate with the per-day `alt_max` and
   flight counts where it tells a story (small grids on bad-weather days).

6. **Classes and tasks.** Probe
   `environment(type=task, comp, day=<a flown day>, class_name=...)` with
   **capitalised display names** — `Club`, `Standard`, `15 Metre`,
   `18 Metre`, `20 Metre Multi Seat`, `Open` (names are case-sensitive;
   lowercase variants 404). For each class found, the task JSON gives
   `task_number` (running count of scored tasks), `task_name`,
   `result_status`, `task_type` and distances. Use it to:
   - split **training days from scored competition days** (early days with
     flights but no task, or unofficial status, are training);
   - report **which classes flew on which days** (a day where only one
     class has a task lets you attribute that day's encounters to it);
   - quote headline tasks (e.g. final-day distance and type) in the
     narrative.
   Only if every capitalised probe 404s across several flown days, state
   that no per-class attribution is possible from CPAS.

7. **Assemble the data JSON** at
   `src/reports/.report_data/cpas_<slug>/report_<YYYY-MM-DD>.json` following
   the schema in the `make_cpas_report.py` docstring: `title`, `subtitle`
   (name the data source and comp key), `intro` (generation date +
   competition status), `overview` key/value rows, `days_flown` paragraphs,
   `daily` table rows (one per flown day), and free-form `sections` —
   normally: "Incursions per day and per class" (counts + the
   disabled/enabled caveat + encounter narrative), "Weather forecast over
   the championship" (phase bullets), and "Data-quality notes (CPAS
   validation)". Write the analysis narratives yourself; the script only
   renders.

8. **Render.**

   ```bash
   ~/.venv-report/bin/python /home/angel/tools/make_cpas_report.py \
       src/reports/.report_data/cpas_<slug>/report_<date>.json
   ```

   Output goes to the JSON's `"output"` path — use
   `/home/angel/src/reports/CPAS.<COMP>_summary_report_<YYYY-MM-DD>.docx`
   unless the user asked for somewhere else. Verify the file exists.

9. **Summarize to the user**: days flown, incursion answer (with the
   disabled caveat if it applies), encounter totals and peak days, the
   weather story in two or three sentences, and the report path.
