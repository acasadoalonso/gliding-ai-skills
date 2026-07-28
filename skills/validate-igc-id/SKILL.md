---
name: validate-igc-id
description: >-
  Validate the IGC ranking-list IDs ("Igc id" column) of every pilot in a
  competition entry spreadsheet against the official IGC Ranking database
  (rankingdata.fai.org REST API), then colour the Igc id cells by outcome.
  Use whenever the user wants to check, validate, verify, or audit IGC IDs /
  ranking-list IDs / rankingdata IDs for an entry list — an .xlsx file or a
  Google Sheets URL — especially when they ask to flag valid vs wrong IDs, to
  colour the Excel cells, or mention the "Igc id" column. Confirms each ID
  exists in the ranking list AND belongs to the named pilot. Writes a markdown
  report (valid / wrong / not supplied) to reports/ and saves a copy of the
  workbook with the Igc id cells painted green (valid) or red (wrong).
---

# Validate IGC ranking IDs from an entry spreadsheet

Cross-check the `Igc id` of each entrant against the IGC Ranking-list database
and mark up a copy of the entry spreadsheet so organisers can see at a glance
whose ID is good. A bundled script does the deterministic work (download, API
lookups, name cross-check, report, colouring); this file explains the workflow
and how to read the result.

The authoritative API description is `Documents/Ranking list REST api
v.0.23.pdf`. The one call this skill needs is public (no auth):

```
https://rankingdata.fai.org/rest/api/rlpilot?id=<ranking-list id>
```

It returns `{"status_message": "Data Found", "data": [{pilotid, surname,
firstname, nationality, ...}]}` when the ID exists, or `"Data Not Found"` with
`data: null` when it doesn't (HTTP status is 200 either way — check the
payload, not the status code).

## Inputs to collect

1. **The spreadsheet** — either a local `.xlsx` path or a Google Sheets URL
   (the script converts an `/edit...` URL into an `/export?format=xlsx`
   download automatically, saving to `Documents/`). **Ask the user for the
   file or URL if they didn't give one.** The sheet needs header columns
   `Igc id`, `First name`, `Last name`, and ideally `country` — found by
   header text within the first 10 rows, so column order doesn't matter.
2. **Sheet name** — only if the entries aren't on the workbook's active sheet
   (`--sheet`). Google exports put every tab in the file; the active tab is
   usually the current one, but verify if the workbook has several.

## How each person is classified

An ID that merely *exists* in the ranking list is not enough — ID 5161 typed
into the wrong row would still "exist". So the ID must exist **and** the
registered pilot's name must match the row's name (accent-insensitive,
compound surnames allowed, swapped first/last order tolerated).

| Outcome | Meaning | Igc id cell |
| :--- | :--- | :--- |
| **VALID** | ID found in the ranking list and the registered name matches the row | 🟢 green (`C6EFCE`) |
| **WRONG** | ID not found; or not a plain number (`ARG-123`); or it belongs to a *different* pilot (report says who); or it resolves to an empty "Blank/Blank" placeholder profile in the ranking DB; or the API errored (unverifiable) | 🔴 red (`FFC7CE`) |
| **NOT SUPPLIED** | Igc id cell is empty | left uncoloured |

Rows with no first *and* no last name (country separator rows like `ARGENTINA`,
unfilled slots) are skipped. Google-Sheets float formatting (`5161.0`) is
normalised before lookup. A nationality mismatch between the sheet and the
ranking record does not fail the row — it's surfaced as a note.

Name matching handles the letters NFD accent-stripping misses (`Ł→l`, `ø→o`,
`ß→ss`, …) and treats hyphens as spaces, so *Błaszczyk* matches *Blaszczyk*
and *Abadie Bérard* matches *Abadie-Bérard*. The source sheet's own cell
colours on the `Igc id` column are overwritten (or cleared, for not-supplied
cells) so the copy's colour always reflects this run's verdict.

## Procedure

Run from the repo root (`/home/angel`) so `reports/` resolves correctly.

```bash
python3 .claude/skills/validate-igc-id/scripts/validate_igc_ids.py \
  --excel "<path/to/entries.xlsx or Google Sheets URL>" \
  --generated <YYYY-MM-DD>
```

Useful options:
- `--report <path>` — report location (default
  `reports/<excel-stem>_igc_id_validation.md`).
- `--out <path>` — coloured copy location (default
  `<excel-stem>_igc_id_validated.xlsx` next to the input; the original is
  never modified).
- `--sheet "<name>"` — pick a worksheet.
- `--title "<text>"` — report heading.

What the script does:
1. Downloads the Google Sheet if given a URL (to
   `Documents/igc_id_gsheet_download.xlsx`).
2. Finds the header row and columns by name.
3. For each named row, cleans the ID, queries `rlpilot?id=` (cached per unique
   ID, so duplicated pilots — e.g. a captain who also flies — cost one call).
4. Classifies VALID / WRONG / NOT SUPPLIED as above.
5. Writes the markdown report and saves the coloured **copy** — the input file
   is left untouched.

## After running

- Report structure: **1. Summary** (count table), **2.1 Valid IDs**,
  **2.2 Wrong IDs** (each with the reason — not found, belongs to someone
  else, non-standard, API error), **2.3 Not supplied**.
- Tell the user both output paths and the counts, and call out the
  interesting rows: a WRONG that "belongs to <other pilot>" is usually a
  copy-paste slip worth fixing at source; an "unverifiable — API error" row is
  not proven wrong — re-run if rankingdata.fai.org was down.
- NOT SUPPLIED rows are common for team captains, who often have no ranking
  profile; they are listed but not painted.

## Example

User: "Validate the Igc ids in the JWGC entry sheet and colour them."

```bash
python3 .claude/skills/validate-igc-id/scripts/validate_igc_ids.py \
  --excel "https://docs.google.com/spreadsheets/d/<id>/edit?gid=..." \
  --generated 2026-07-06
```

→ `reports/igc_id_gsheet_download_igc_id_validation.md` plus
`Documents/igc_id_gsheet_download_igc_id_validated.xlsx` with green/red
`Igc id` cells. Then summarise the counts and highlight the wrong IDs.

## Notes

- Re-running is safe and idempotent: the copy is rebuilt from scratch.
- The API is queried once per unique ID; a full entry list is typically a
  minute or less.
- This validates the **IGC ranking-list ID** only. FAI *sporting licences*
  (a different number, different database) are handled by the separate
  `validate-fai-licenses` skill.
