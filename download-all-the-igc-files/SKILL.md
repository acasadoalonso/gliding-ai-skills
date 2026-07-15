---
name: download-all-the-igc-files
description: >-
  Download ALL the IGC flight logs for EVERY class of a competition on a given
  date from SoaringSpot. Use whenever the user wants a batch/bulk download of
  flights — "download all the IGC files", "get every flight for day X", "fetch
  the whole day's logs", "all flights for all classes" — as opposed to fetching
  a single pilot's file (that is the download-igc skill). Asks only for the
  competition name and the competition date, reads that competition's API
  credentials, and runs tools/download_all_igc.py, which walks the SoaringSpot
  REST API itself (contest → classes → task for the date → results) and saves
  every flight per class into IGCfiles/<comp>_<date>/<class>/, printing a
  per-class summary of saved, skipped, and failed files.
---

# Download all IGC files for a competition day

Fetch the IGC flight log of **every contestant in every class** for one
competition day by running `/home/angel/tools/download_all_igc.py`. The
program talks to the SoaringSpot v1 REST API directly (HMAC auth) — it does
the whole walk itself, so no MCP calls are needed for the download.

## Inputs to collect

Ask for exactly two things if not already provided — do not guess either:

1. **Competition name** — the SoaringSpot competition, e.g. `egc2026`. This
   selects the credentials directory and names the output directory.
2. **Date** — the competition day as `YYYY-MM-DD` (e.g. `2026-07-10`).

## Procedure

1. **Locate the credentials.**
   Per-competition credentials live in `/home/angel/src/SoaringSpot/<comp>/`
   as two files, `clientid` and `secretkey`. If that directory doesn't exist
   for the given name, list `/home/angel/src/SoaringSpot/` and ask the user
   which competition they meant. (The client ID is prefixed with the contest
   ID, e.g. `5337_…` — the program uses that prefix to find the contest, so
   the credentials must be the ones issued for this competition.)

2. **Run the program.**

   ```bash
   python3 /home/angel/tools/download_all_igc.py \
     --comp <comp> \
     --clientid "$(cat /home/angel/src/SoaringSpot/<comp>/clientid)" \
     --secret "$(cat /home/angel/src/SoaringSpot/<comp>/secretkey)" \
     --date <YYYY-MM-DD>
   ```

   Give the command a generous timeout (several minutes) — a full day is
   dozens of files, several MB each. What the program does:

   - finds the contest from the clientid prefix and enumerates all classes;
   - for each class picks the task whose `task_date` matches the date,
     preferring a scored day over a practice task when both exist (a class
     with no task that day is reported and skipped);
   - downloads every result's flight into
     `IGCfiles/<comp>_<date>/<class>/` (class = SoaringSpot class type,
     e.g. `standard`, `15_meter`, `club`);
   - skips pilots with no uploaded log, keeps going past individual
     failures, refuses to save JSON/HTML error bodies as `.igc`, and prints
     a per-class summary table (saved / skipped / failed). Exit code is
     non-zero if any download failed.

3. **Report the outcome.**
   Relay the program's summary table to the user: per class the task ID,
   files saved, pilots skipped (no log), and failures, plus the output
   directory and total size (`du -sh`). If the date only matched practice
   tasks (task_number negative), say so — the flights are from a training
   day.

## Example

User: "Download all the IGC files for egc2026 on 2026-07-10."

```bash
python3 /home/angel/tools/download_all_igc.py \
  --comp egc2026 \
  --clientid "$(cat /home/angel/src/SoaringSpot/egc2026/clientid)" \
  --secret "$(cat /home/angel/src/SoaringSpot/egc2026/secretkey)" \
  --date 2026-07-10
```

→ 70 saved, 14 skipped, 0 failed (~75 MB):

```
IGCfiles/egc2026_2026-07-10/
├── standard/   25 files
├── 15_meter/   18 files
└── club/       27 files
```

## Notes

- Credentials are per-competition; a clientid from another competition finds
  the wrong contest (or gets HTTP 400 on its classes), so make sure the
  credentials directory matches the competition asked for.
- The soaringspot MCP server is not required, but remains useful for related
  follow-up questions (results, pilots, tasks) about the same day.
- To check the downloaded files for FAI/IGC conformance afterwards, use the
  `validate-igc-files` skill on the output directory.
