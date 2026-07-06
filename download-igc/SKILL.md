---
name: download-igc
description: >-
  Verify that an IGC flight log conforms to the FAI/IGC flight-log format, and
  download the log from SoaringSpot when it isn't already on disk. Use when the
  user wants to check that an IGC file is conformant, and/or fetch a pilot's IGC
  file for a contestant on a given date. Conformance runs the IGC checks (A
  record first, mandatory H-records, untruncated B-record fixes, record order,
  valid character set, and a trailing security G record) against
  formulas/IGCformat.md, and can emit a per-file report like
  reports/SS.<comp>_IGC_conformance.rtf. To obtain a file, it asks for the
  contestant name and date, looks up that day's task result through the
  soaringspot MCP server to find the IGC filename and flight URL, and downloads
  it into the IGCfiles/ directory.
---

# Download IGC files from SoaringSpot

Fetch the IGC flight log for one contestant on one competition day, using the
`soaringspot` MCP server to locate the file and a helper script to download it.

## Inputs to collect

Before starting, make sure you have:

1. **Contestant name** — pilot full name (e.g. "Felipe Levin") or competition
   number (e.g. "FL"). Ask the user if not provided.
2. **Date** — the competition day as `YYYY-MM-DD` (e.g. `2026-05-29`). Ask if
   not provided.
3. **Competition** *(optional)* — defaults to the competition the MCP server is
   currently serving. Only ask if the user's request is ambiguous or spans
   multiple events. The competition name also selects which credentials the
   downloader uses (`SoaringSpot/<comp>/`).

If the contestant name or date is missing, ask for both before proceeding — do
not guess.

## Procedure

Work through these steps with the MCP tools. If the `soaringspot` MCP server is
unreachable, start it first with `./run.sh` (see CLAUDE.md) and retry.

1. **Identify the contest and its classes.**
   - Use `get_tasks` with `date=<YYYY-MM-DD>` to list that day's tasks across
     the served competition(s) — this is the quickest path to the task on a
     specific date. Otherwise enumerate via `list_contests` →
     `get_contest_classes`.
   - A contestant belongs to exactly one class, so you may need to check each
     class's task for that date.

2. **Find the task for the date.**
   - For each candidate class call `get_class_tasks(<class_id>)` and select the
     task whose `task_date` equals the requested date. Note its task id (the
     numeric id in the task's `self` href, e.g. `…/tasks/10541334541`).
   - Skip practice days if the user wants a scored day (practice tasks have a
     negative `task_number` / `result_status: "practice"`), unless the date
     only matches a practice day.

3. **Get the day's results and locate the contestant.**
   - Call `get_task_results(<task_id>)`.
   - In the returned `_embedded` results, match the pilot by the embedded
     contestant `name` (case-insensitive; partial match is fine) or by
     `contestant_number`. If several pilots match, list them and ask the user
     which one.

4. **Extract the IGC filename and download URL from the result JSON.**
   - **IGC filename** — the result's `igc_file` field, e.g. `"65T\\65T_FL.igc"`.
     The downloader strips any leading path; the saved name becomes
     `65T_FL.igc`.
   - **Download URL** — the flight link under the result's
     Using the Flight ID from the task results use the get_flight_from_url 
     endpoint
     endpoint returns the raw IGC content (`Content-Type:
     application/vnd.flight+igc`).


5. **Download the IGC file.**
   use the endpoint get_credentails to get the clientid and secretkey if needed
   Run the helper script (from the repo root `/home/angel/SS`):

   ```bash
   python3 .claude/skills/download-igc/download_igc.py \
     --comp <competition> \
     --url "<flight href from step 4>" \
     --filename "<igc_file value from step 4>"
   ```

   - `--comp` may be omitted when only one competition has credentials under
     `SoaringSpot/`; otherwise pass it (e.g. `wgc2026`, `24-fai-egc`).
   - Instead of `--url` you can pass `--flight-id <id>` (the numeric id).
   - Files are written to `IGCfiles/` by default; override with `--out-dir`.

6. **Confirm the result.**
   Report the saved path and byte count (the script prints them), and the
   pilot / date / task it corresponds to.

7. **Check IGC conformance.**
   Validate the downloaded file against the IGC flight-log format defined in
   `formulas/IGCformat.md` (FAI/IGC Technical Specification, Jan 2026 / AL10).
   Run each of these checks and note pass/fail per file:

   1. **A record (first line).** The very first line must start with `A` — the
      FR manufacturer/identification record (3-letter code + serial, e.g.
      `AXXXABC…`). It is always the first record in the file.
   2. **Mandatory H-records.** The header block must carry the required H-records:
      `HFDTE` (flight date, `DDMMYY`), `HFFXA` (fix accuracy), `HFPLT`
      (pilot in charge), `HFGTY` (glider type), `HFGID` (glider ID /
      registration) and `HFDTM` (GNSS datum, `100`/WGS-1984). Competition logs
      also typically carry `HFCID` (competition number) and `HFCCL` (class).
   3. **B-records (fixes).** A full, untruncated set of B (GPS fix) records must
      be present — each `B` line carries time, lat/long, validity flag, pressure
      and GNSS altitude. Confirm the count is non-zero and no line is empty or
      cut mid-record.
   4. **Record order.** Records must appear in the spec order: `A` first, then
      `H`, `I`/`J`, optional `C` (task), then time-series `B`/`E`/`F`/`K`, with
      `L` (logbook) allowed after the header.
   5. **Valid characters.** Lines use only the valid IGC character set
      (upper-case `A–Z`, digits, space, `- + . , : /`). Accented/lower-case
      characters are not valid in the data records.

8. **Check the G (security) records.**
   - The Security (G) record(s) must be present and must be the **last**
     record(s) in the file. L records are allowed after the G records
   - Verify there are **no B-records after the G
     records (may be multiple G records) ** — a G record followed by more fixes 
     indicates a truncated/ tampered or concatenated file and fails conformance.

9. **Report conformance.**
   State per file whether it passes, and summarize the findings (pilot, comp ID,
   date, B-record count, glider/registration). For a multi-file run, produce a
   conformance report like `reports/SS.<comp>_IGC_conformance.rtf` — see the
   existing `reports/SS.WGC2026_IGC_conformance.rtf` for the format.

## Example

User: "Download the IGC for Felipe Levin on 2026-05-29."

- `get_class_tasks(10053)` → task on `2026-05-29` is id `10541334541`.
- `get_task_results(10541334541)` → Felipe Levin's result has
  `igc_file = "65T\\65T_FL.igc"` and flight href
  `http://api.soaringspot.com/v1/flights/10541334728`.
- Download:

  ```bash
  python3 .claude/skills/download-igc/download_igc.py \
    --comp wgc2026 \
    --url "http://api.soaringspot.com/v1/flights/10541334728" \
    --filename "65T\\65T_FL.igc"
  ```

  → `Saved 2,185,151 bytes -> /home/angel/SS/IGCfiles/65T_FL.igc`

## Notes

- IGC files can be large (several MB); that is expected.
- The script saves raw bytes and refuses to write a file if the endpoint
  returns JSON/HTML instead of IGC (e.g. an auth failure), so a bad credential
  or wrong `--comp` surfaces as a clear error rather than a corrupt `.igc`.
- Credentials are per-competition; make sure `--comp` matches the competition
  the contestant flew in.
