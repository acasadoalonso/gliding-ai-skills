---
name: validate-fai-licenses
description: >-
  Validate the FAI sporting licenses of every pilot in a competition entry
  spreadsheet against the official FAI extranet records, then colour-code the
  rows by outcome. Use whenever the user wants to check, validate, verify, or
  audit FAI sporting licenses / license numbers for an entry list (WGC, EGC, or
  any SoaringSpot-style .xlsx export), especially when they ask to flag valid vs
  invalid licenses or to colour the Excel rows. For each pilot it looks up the
  provided number in the FAI database; when the number is wrong, non-standard,
  or missing it tries to recover the correct one by matching the pilot's name.
  On EGC PILOTS AND CAPTAINS forms it also writes the resolved licence number
  back into the sheet for team-captain (CPT) rows, whose licence cell is usually
  left blank. Writes a markdown report to reports/ and paints the workbook rows
  green (valid), blue (corrected via name match), and red (invalid/unverifiable).
---

# Validate FAI sporting licenses from an entry .xlsx

Cross-check the FAI licence number of each entrant against the FAI extranet, and
mark up the entry spreadsheet so organisers can see at a glance who is cleared.
A bundled script does the deterministic work (API paging, matching, report,
colouring); this file explains the workflow and how to read the result.

The logic mirrors the memory note
`validate-fai-sporting-license-for-pilots.md`: fetch every Gliding **and
Universal** licence for the pilot's country from the FAI extranet (a Universal
licence covers all FAI sports, so it counts the same as a Gliding one), match
the provided number against the record's `idlicencee`, and — when that fails —
fall back to a **name match** to recover the correct number.

## Inputs to collect

1. **Excel file (.xlsx)** — the entry list. **Always ask the user for the path
   if they didn't give one.** The sheet must have header columns the script can
   recognise: a first-name column (`first_name` / `First name`), a last-name
   column (`last_name` / `Last name`), a country column (`country_code` /
   `country`), and a licence column — either `fai_licence_number` /
   `fai_license_number` (SoaringSpot export) or `Fai sporting licence number`
   (EGC PILOTS AND CAPTAINS form). Column order doesn't matter — columns are
   found by header text, so both layouts work with the same command.
2. **Sheet name** — only needed if the workbook has several sheets and the
   entries aren't on the active one (`--sheet`).
3. **Output** — by default the script **overwrites the input .xlsx** with the
   colours applied. Offer `--out <copy.xlsx>` if the user wants to keep the
   original untouched.

## How each pilot is classified

| Outcome | Meaning | Row colour |
| :--- | :--- | :--- |
| **VALID** | Provided number is a clean number that matches an FAI record | 🟢 green (`C6EFCE`) |
| **NAME_MATCH** | Number was wrong / non-standard / missing, but the pilot was found by name — the correct number is reported | 🔵 blue (`BDD7EE`) |
| **INVALID** | A number was given but matches neither by number nor by name | 🔴 red (`FFC7CE`) |
| **MISSING** | No number given and no name match | (left uncoloured) — except **CPT rows**, painted 🔴 red: a captain needs a licence, so nothing found is a failed validation |

Why the number-vs-name split matters: a value like `GER-4264 ID-129831`,
`POL-110/06`, or `1` is not a clean FAI id, so it can't be trusted as-is. The
script only calls a row VALID when the entered number *is* a plain integer that
exists in the records; anything recovered through the name is reported as a
correction (blue) so the organiser knows the entry sheet needs fixing.

## Procedure

Run from the repo root (`/home/angel`) so `reports/` resolves correctly.

```bash
python3 .claude/skills/validate-fai-licenses/scripts/validate_licenses.py \
  --excel "<path/to/entries.xlsx>" \
  --generated <YYYY-MM-DD>
```

Useful options:
- `--report <path>` — report location (default
  `reports/<excel-stem>_fai_license_validation.txt`).
- `--out <path>` — write the coloured workbook to a copy instead of in place.
- `--no-color` — produce the report only, leave the workbook untouched.
- `--no-captain-fill` — colour rows but do not write resolved numbers into the
  captains' (CPT) licence cells.
- `--title "<text>"` — report heading (default derived from the filename).
- `--sheet "<name>"` — pick a worksheet.

### Entry-form layouts it handles

The EGC PILOTS AND CAPTAINS form groups entrants by nation: a country name sits
alone in the first column (e.g. `GERMANY`) as a section separator, and each
person's row carries a role marker in the first column — `CPT` for the team
captain or a running number for a pilot. This needs no special handling: rows
with no first *and* no last name (the country separators, plus any blank
placeholder row such as an unfilled captain slot) are skipped, and everyone with
a name — captains and pilots alike — is validated, since a captain also needs a
valid licence. Country codes in these forms are ISO-3166 alpha-3 (e.g. `DEU`,
`DNK`, `HRV`, `NLD`), which the built-in IOC map converts before the FAI lookup.

Expect a partially-filled form to produce many blue NAME_MATCH rows: cells left
blank are recovered by name, and non-standard values (`GER-4264 ID-129831`,
`CZE-0201`, `D4053`, a bare `1`) route through the name match too. That is the
intended signal — those entries need fixing at source — not a fault.

**Captain licence write-back.** A captain still needs a valid FAI licence, yet
the CPT row's licence cell is usually left blank on these forms. So for CPT rows
the script goes one step further than colouring: whenever it resolves a real FAI
record for that captain, it writes the number into the `Fai sporting licence
number` column, filling the blank (or replacing a non-standard value). The role
column has no header, so captains are detected by the literal `CPT` marker in
the first column. This runs by default when the workbook is saved; pass
`--no-captain-fill` to colour without touching the cells. Pilot rows are never
written to — only captains — because pilots' numbers come from their own entry
and shouldn't be silently overwritten.

CPT rows are also coloured by outcome like every other row, with one stricter
rule: a captain whose licence can't be resolved at all (MISSING — no number and
no name match) is painted **red**, not left uncoloured as a pilot would be,
because a captain without a licence fails validation. Empty captain slots (a
`CPT` marker with no name at all) are skipped, not coloured — there is no
person to validate.

What the script does:
1. Finds the header row and the needed columns by name.
2. For each pilot, maps the ISO-3166 alpha-3 `country_code` to the FAI **IOC**
   code (e.g. `DEU→GER`, `NLD→NED`, `CHE→SUI`, `DNK→DEN`, `HRV→CRO`; others pass
   through unchanged) and fetches that country's Gliding and Universal
   licences once (cached). Some NACs (e.g. CZE, AUS) issue **Universal**
   sporting licences valid for every FAI sport — these are accepted exactly
   like Gliding ones. They only appear under a separate `discipline=Universal`
   API query, which the script performs automatically.
3. Tries a direct number match → VALID; else a surname (+ given-name) match →
   NAME_MATCH with the recovered number; else INVALID / MISSING.
4. Notes each found licence's `valid until` date and flags expired ones in the
   report (colour is still by found/not-found — expiry is surfaced as a note).
5. Writes the markdown report and, unless `--no-color`, paints the rows and
   saves the workbook — writing the resolved number into any CPT (captain) row
   whose licence cell was blank or non-standard (unless `--no-captain-fill`).

## Credentials

The FAI extranet password is read, in order: `--fai-password`, the `$FAIPWD`
environment variable, then `FAIPWD` in `config.py` under `--config-dir`
(default `/home/angel/tools`). No secret is stored in the skill. If none is
found the script exits with a clear message.

## After running

- Report structure (same shape as prior EGC/WGC reports): an executive-summary
  count table, then sections **2.1 Validated**, **2.2 Corrected via Name Match**
  (showing `provided -> correct`), **2.3 Invalid/Unverifiable**,
  **2.4 Missing Information**, and — when captain cells were written back —
  **2.5 Captain Licence Numbers Written Back** (showing `provided -> resolved`).
- Tell the user the report path and the coloured-workbook path, and summarise
  the counts (valid / corrected / invalid / missing).
- **Apply judgement to the flagged rows.** A NAME_MATCH means the entry sheet
  has the wrong or no number — worth fixing at source. An INVALID for a country
  whose fetch failed (noted in the report) is *unverifiable*, not proven wrong;
  re-run if the FAI extranet was down. Expired licences are surfaced as notes —
  raise them with the organiser even though the row is coloured as found.

## Example

User: "Validate the FAI licenses in the egc2026 pilots and captains form and
colour the rows."

```bash
python3 .claude/skills/validate-fai-licenses/scripts/validate_licenses.py \
  --excel "egc2026-PILOTS AND CAPTAINS-FORM.xlsx" \
  --generated 2026-07-04
```

→ `reports/egc2026-PILOTS AND CAPTAINS-FORM_fai_license_validation.txt` plus the
same workbook with green / blue / red rows. Then report the counts and highlight
any corrections and unverifiable entries for follow-up.

## Notes

- **Country codes must resolve to IOC.** The built-in map covers the common
  European gliding nations and many others; codes not in the map are used
  as-is. If a country comes back with everything INVALID, check the IOC mapping.
- The FAI API pages 100 records at a time and is fetched **once per country**
  (cached), so large multi-country lists stay reasonably fast.
- Re-running is safe and idempotent: it recolours from scratch each time.
