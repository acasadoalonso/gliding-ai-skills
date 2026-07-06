---
name: check-club-handicaps
description: >-
  Check that the handicap assigned to each contestant in a competition's Club
  class matches the IGC Club Class handicap list. Use when the user wants to
  verify, audit, or cross-check the handicaps of a handicapped class against the
  official list. Pulls every contestant's glider details (aircraft model,
  registration, assigned handicap) through the soaringspot MCP server
  (get_class_contestants), matches each glider to formulas/club_class_handicaps.md
  (or formulas/20m_multiseat_handicaps.md for the 20m Multi-Seat class), flags any
  contestant whose assigned handicap differs from the list base handicap or whose
  glider is not in the list, and writes an RTF report to
  reports/SS.<comp>_club_handicap_check.rtf.
---

# Check handicaps on the Club class

Verify, contestant by contestant, that the handicap SoaringSpot has assigned in a
handicapped class matches the official IGC handicap list stored under
`formulas/`. The MCP server supplies the glider details; a helper script does the
deterministic matching, comparison, and RTF rendering.

This skill is written for the **Club class** (`formulas/club_class_handicaps.md`)
but works for any handicapped class — pass the matching list, e.g.
`formulas/20m_multiseat_handicaps.md` for the 20 Metre Multi-Seat class.

## Inputs to collect

1. **Competition** — name/slug used for credentials (e.g. `wgc2026`,
   `24-fai-egc`). This selects both the MCP credentials (`SoaringSpot/<comp>/`)
   and the report filename. Ask if not provided.
2. **Class** — defaults to **Club**. Only ask if the contest has more than one
   handicapped class or the request is ambiguous.
3. **Handicap list** — defaults to `formulas/club_class_handicaps.md`. Use
   `formulas/20m_multiseat_handicaps.md` when checking the 20 Metre Multi-Seat
   class.

## Procedure

Work through these with the `soaringspot` MCP tools. If the server is
unreachable, start it with `./run.sh` (see CLAUDE.md) and retry. Run everything
from the repo root `/home/angel/SS`.

1. **Select the competition's credentials.**
   Call `set_compname(<comp>)` first — the API keys are per-competition, and
   `get_class_contestants` returns `400 Bad Request` until the right credentials
   are loaded.

2. **Find the Club class and its id.**
   - `get_contest_classes(<contest_id>)` lists the classes. Pick the one whose
     name is *Club* (or whose `type` indicates a handicapped/club class). Note
     its numeric `class_id` (the id in the class `self` href).
   - If you only have the competition slug and not the contest id, discover it
     with `list_contests` → match by name → `get_contest_classes`.

3. **Pull every contestant's glider details.**
   - `get_class_contestants(<class_id>)` returns, for each pilot:
     `name`, `contestant_number`, `team`, `aircraft_model`,
     `aircraft_registration`, `pure_glider`, and the assigned `handicap`.
   - Save the **raw JSON response** to a working file so the helper can read it,
     e.g. write it to `/tmp/<comp>_club_contestants.json`. (The helper accepts
     either the raw MCP response with `_embedded` or a plain list of contestant
     objects.)

4. **Run the comparison + report helper.**

   ```bash
   python3 .claude/skills/check-club-handicaps/check_handicaps.py \
     --contestants /tmp/<comp>_club_contestants.json \
     --handicap-list formulas/club_class_handicaps.md \
     --comp <comp> --class-name "Club" \
     --out reports/SS.<comp>_club_handicap_check.rtf \
     --generated <today's date YYYY-MM-DD>
   ```

   The helper:
   - parses the Appendix handicap table out of the markdown list,
   - normalises and matches each `aircraft_model` to a list entry (expanding
     grouped variants like `Discus a, b, CS` or `ASW 20, F, L`),
   - compares the assigned handicap against the list **base** handicap
     (tolerance 0.0005), and
   - writes the RTF report and prints a summary of every non-`OK` row to stdout.

   Status codes it assigns per contestant:
   - **OK** — assigned handicap equals the list base handicap.
   - **DIFF** — glider matched, but the assigned handicap differs from the base.
   - **UNMATCHED** — glider not found in the list.
   - **NO_HANDICAP** — no (or zero) handicap on the entry.

5. **Review the flagged rows — do not treat every DIFF as an error.**
   The helper is deliberately conservative; apply judgement to each flag:
   - **DIFF** may be *legitimate*. Under SC3AH §1.6 the base handicap is adjusted
     for **takeoff mass** (§1.6.1: +0.004 per 10 kg above the IGC Reference Mass;
     −0.003 per whole 10 kg below, capped at −0.006) and for **winglets**
     (§1.6.2: +0.004 if added to a glider certified without them). A small
     positive or negative offset from the base is expected and is not a mistake —
     say so in the report rather than calling it wrong. A difference that no
     adjustment can explain *is* worth raising.
   - **UNMATCHED** is usually a **naming variant** (e.g. `LS-4` vs `LS 4`,
     `Std Cirrus` vs `Std. Cirrus B`), not an ineligible glider. Confirm against
     `formulas/club_class_handicaps.md` by eye; if it's just spelling, note the
     correct list row in the report. A genuinely absent glider may signal an
     eligibility issue — flag it for the organisers.
   - **Partial name match** (noted in the row) means the model matched a list row
     only on a prefix — common where the list has two rows for one family (e.g.
     `Std. Cirrus B (15m)` = 1.000 vs `(16m)` = 1.006). Pick the right one from
     the wingspan/remarks and correct the report.

6. **Finalise and report.**
   - The RTF lands at `reports/SS.<comp>_club_handicap_check.rtf` with: a summary
     line (counts of OK / DIFF / UNMATCHED), a full per-contestant table
     (number, pilot, glider, registration, assigned H, list H, status, note),
     and a "Differences & items to review" section listing only the flagged
     rows.
   - Tell the user the report path and summarise the findings in chat: how many
     contestants checked, which differ from the list and by how much, and which
     gliders couldn't be matched — with your read on whether each is a real
     discrepancy or an explainable adjustment / naming variant.
   - *(Optional)* If `soffice`/`libreoffice` is installed, convert to PDF:
     `soffice --headless --convert-to pdf --outdir reports reports/SS.<comp>_club_handicap_check.rtf`.
     The repo currently has no LibreOffice, so default to delivering the RTF.

## Example

User: "Check the Club class handicaps for the 24th FAI EGC."

- `set_compname("24-fai-egc")`
- `get_contest_classes(<contest_id>)` → Club class id, e.g. `10071`.
- `get_class_contestants(10071)` → save raw JSON to `/tmp/egc_club_contestants.json`.
- ```bash
  python3 .claude/skills/check-club-handicaps/check_handicaps.py \
    --contestants /tmp/egc_club_contestants.json \
    --comp 24-fai-egc --class-name "Club" \
    --out reports/SS.24thFAIEGC_club_handicap_check.rtf \
    --generated 2026-06-07
  ```
- Review the printed DIFF/UNMATCHED lines, confirm each against the list, then
  report the RTF path and a plain-language summary.

## Notes

- **Credentials are per-competition.** Always `set_compname` for the right
  competition first; otherwise `get_class_contestants` errors with 400.
- The **Open class is unhandicapped** (every entry has `handicap = 1`) — running
  this skill against Open will flag everything UNMATCHED, which is expected. Use
  it on handicapped classes (Club, 20 Metre Multi-Seat).
- The list base handicap is the *starting* value; the assigned handicap is the
  *flown* value after mass/winglet adjustments. The skill compares against the
  base and leaves the adjustment judgement to you — the goal is to surface
  differences for review, not to recompute the adjustment.
