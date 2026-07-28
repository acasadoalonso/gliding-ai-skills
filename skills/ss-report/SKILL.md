---
name: ss-report
description: >-
  Generate (or refresh) a succinct .docx competition report for a SoaringSpot
  competition — evolution of the competition day by day, number of flights,
  kilometres flown, and hours flown per class, plus current top-5 standings.
  Use whenever the user asks for a competition report, a daily/updated report,
  "today's report", or competition statistics (flights / km / hours by class)
  for a comp with credentials under src/SoaringSpot/ (e.g. 24-fai-egc, egc2026,
  wgc2026). Pulls all data through the soaringspot MCP server only, stores the
  per-class aggregates as JSON under src/reports/.report_data/<comp>/, and runs
  tools/make_competition_report.py to write a date-stamped
  reports/SS.<comp>_competition_report_<date>.docx.
---

# SoaringSpot competition report (.docx)

Refresh the per-class statistics of a competition through the **soaringspot
MCP server only** and regenerate the report. Designed to be re-run every day
of the championship — each run overwrites the class JSONs with the latest
scored data and writes a new date-stamped .docx.

## Inputs to collect

1. **Competition name** — the credentials directory under
   `/home/angel/src/SoaringSpot/` (e.g. `24-fai-egc`). If the user names it
   loosely ("egc2024", "the EGC"), match it against `list_compnames` output
   and confirm the match if ambiguous.

## Procedure

1. **Select the competition.** Call `set_compname` with the credentials
   directory name; it returns the contest id. Call `get_contest(contest_id)`
   to get name, dates, location, and the class ids.

2. **Check for an existing data directory.**
   `/home/angel/src/reports/.report_data/<comp>/` may already exist with a
   `meta.json` (title, subtitle, `class_files`, class ids) and one JSON per
   class. If not, create `meta.json` in that format (see
   `tools/make_competition_report.py` docstring; example in
   `.report_data/24-fai-egc/meta.json`).

3. **Aggregate each class** (spawn one subagent per class in parallel — they
   only need ToolSearch access to the soaringspot MCP tools; tell them NOT to
   call `set_compname` again):
   - `get_class_contestants(class_id)` → contestant count.
   - `get_class_tasks(class_id)` → keep only competition days
     (`task_number >= 1`; skip practice days).
   - `get_task_results(task_id)` for every competition task. Per day compute:
     flights (scored distance > 0), finishers (scored speed > 0), km flown
     (sum of scored distances), hours flown, and the day winner
     (name, points, speed).
   - `get_class_results(class_id)` → top-5 overall standings.
   - **Unit gotchas:** the API returns speeds in **m/s** (× 3.6 for km/h) and
     distances in **metres**. Hours = `scored_finish − scored_start` when both
     present; for landouts without a finish, estimate
     `distance / average finisher speed of that day`. A cancelled day has
     `result_status: "cancelled"`; a day being flown right now shows
     all-zero placeholder results until scored.

4. **Write the class JSONs** into the data directory, one file per class,
   in the exact schema documented in the `make_competition_report.py`
   docstring (`class`, `contestants`, `days[]`, `top5[]`, `hours_method`).

5. **Generate the .docx.** python-docx lives in a dedicated venv (system
   python is externally managed):

   ```bash
   /home/angel/.venv-report/bin/python /home/angel/tools/make_competition_report.py \
     --data-dir /home/angel/src/reports/.report_data/<comp>
   ```

   Output: `/home/angel/src/reports/SS.<comp>_competition_report_<YYYY-MM-DD>.docx`
   (override with `--out`). The script adds overview totals, a per-class
   evolution table with a bold Total row, daily winners, top-5 standings, and
   a status note derived from the data (unofficial days, cancelled days, days
   not yet scored).

6. **Report the outcome.** Give the user the output path, the per-class and
   overall totals (flights / km / hours), the current leaders, and flag which
   days are still unofficial, preliminary, or cancelled.

## Notes

- If the venv is missing, recreate it:
  `python3 -m venv /home/angel/.venv-report && /home/angel/.venv-report/bin/pip install python-docx`.
- Days whose results are `unofficial`/`preliminary` will change on later
  runs — always re-fetch every competition day, not just the newest one.
- Credentials are per-competition; `set_compname` must match the comp being
  reported.
