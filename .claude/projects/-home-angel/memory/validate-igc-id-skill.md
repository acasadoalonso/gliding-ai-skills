---
name: validate-igc-id-skill
description: "How the validate-igc-id skill checks the \"Igc id\" column against the IGC Ranking REST API and colours the cells green/red, and the procedure used to build it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 363e60f3-eb12-4bdf-91b1-340cbaf45a28
---

The `validate-igc-id` skill (`.claude/skills/validate-igc-id/`) validates the
IGC ranking-list IDs in an entry spreadsheet's `Igc id` column against
`https://rankingdata.fai.org/rest/api/rlpilot?id=<N>` (public, no auth; API
documented in `Documents/Ranking list REST api v.0.23.pdf`). Accepts a local
.xlsx or a Google Sheets URL (auto-converts `/edit` to `/export?format=xlsx`,
saves to `Documents/`). Writes `reports/<stem>_igc_id_validation.md`
(valid / wrong / not supplied) and a coloured **copy**
`<stem>_igc_id_validated.xlsx` — Igc id cells green (valid) / red (wrong).

Non-obvious gotchas learned building it:
- The API returns HTTP 200 even for "Data Not Found" — check `data`/`status_message`.
- Some ranking IDs resolve to literal "Blank/Blank" placeholder profiles — treat as wrong/unconfirmable.
- Validity requires the registered name to match the row, not just ID existence.
- NFD accent stripping misses Ł/ø/ß — map them explicitly; treat hyphens as spaces (Abadie-Bérard).
- Google export sheets carry their own fills — overwrite/clear fills on checked cells.

**How it was built** (replayable procedure for future spreadsheet-validation skills):
1. Read the API spec first (`Documents/Ranking list REST api v.0.23.pdf` via the
   Read tool's `pages` param) and the closest existing skill
   (`validate-fai-licenses`) as the structural model — same report + colour
   pattern, same SKILL.md layout.
2. Download the Google Sheet by rewriting the `/edit?gid=...` URL to
   `https://docs.google.com/spreadsheets/d/<id>/export?format=xlsx` (exports
   ALL tabs; pick the sheet by header inspection, not gid).
3. Probe the live API with curl using a known-good ID from the sheet and a
   bogus ID *before* writing code, to learn the real found/not-found shapes.
4. Write a single deterministic script in `scripts/` (stdlib urllib + openpyxl,
   per-unique-ID cache), plus a SKILL.md explaining workflow and outcomes.
5. Run it on the real spreadsheet as the test, then verify the outputs
   independently (re-open the workbook, count green/red fills, confirm they
   match the report counts) — this verification is what exposed the
   diacritics, pre-existing-fill, and Blank-profile bugs.
6. Fix, re-run, re-verify; update SKILL.md with each discovered quirk; commit
   only the skill files (not reports/downloads).

Related: [[validate-fai-licenses-skill]] (different number, FAI extranet DB).
