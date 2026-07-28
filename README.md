# gliding-ai-skills

**Gliding championship data validation, reporting, and analysis tooling.**

Claude Code skills and Python utilities for processing World Gliding Championships (WGC), European Gliding Championships (EGC), Sailplane Grand Prix (SGP), FAI Continental Cups (FCC) and other gliding competition datasets.

---

## Overview

This repository contains:

| Category | Contents |
|----------|----------|
| **Skills** | 9 Claude Code skills for generating reports, validating pilots/licenses/flarm/IGC IDs, downloading flight data |
| **Formulas** | FAI Annex A rules (Sporting Code), scoring algorithms, handicaps lists (Club + 20m Multi-Seat), Team Cup formula |
| **Tools** | `.cucx` file generator for SeeYou Competition — builds SeeYou-readable files from SGP competitions with full pytest coverage |
| **Reports** | Generated outputs: team cup standings, IGC conformance reports, FAI license validation reports, CPAS safety summaries |

The tooling integrates two MCP (Model Context Protocol) servers:
- **SoaringSpot** — WGC/EGC/FCC official data source for tasks, contestants, and results
- **SGP.Aero.AI** — Sailplane Grand Prix competition data from crosscountry.aero

---

## Skills Reference

### 📊 Reporting & Analysis

#### `ss-report`
Generates a `.docx` SoaringSpot competition report with:
- Day-by-day evolution (flights, km flown, hours flown per class)
- Daily task summaries and weather notes  
- Current top-5 standings for each class
- Team Cup running totals

**Usage:** Ask "generate today's EGC/WGC/FCC report" or "refresh the competition statistics"

*Output:* `reports/SS.<comp>_competition_report_<YYYY-MM-DD>.docx`

---

#### `cpas-report`
Generates a `.docx` CPAS (crosscountry.aero) safety/incursion summary with:
- Number of days flown and flights per day
- Airspace incursions by class (with enabled/disabled caveat)
- Proximity encounters (30 m threshold), tagged events narrative  
- Per-day weather forecast evolution from open-meteo
- Flight-recorder validation notes (IGC anomalies, correction suggestions)

**Usage:** Ask "how many days flown at EGC/WGC/FCC" or "CPAS summary for <competition>"

*Output:* `reports/CPAS.<comp>_summary_report_<YYYY-MM-DD>.docx`

---

### ✅ Validation Skills

#### `validate-fai-licenses`
Cross-checks every entrant's FAI sporting licence number against the official FAI extranet database:
- **VALID** (🟢 green): Provided clean numeric ID matches an active Gliding or Universal record  
- **NAME_MATCH** (🔵 blue): Number was wrong/non-standard/missing but pilot found by name — correct licence reported
- **INVALID** (🔴 red): A number given, but not found and no name match possible
- **MISSING**: No number given and no name match; captains painted 🔴 red as validation failure

Handles EGC "PILOTS AND CAPTAINS" forms (country header rows + CPT/pilot role markers) including writing resolved licence numbers into blank captain cells.

**Usage:** Ask to validate FAI licences for an entry spreadsheet (.xlsx)

*Output:* Markdown report (`reports/<stem>_fai_license_validation.md`) plus coloured .xlsx workbook copy

---

#### `validate-flarm`
Validates Flarm device IDs from a SoaringSpot contest against the official Flarm pilot database:
- Fetches each contestant's Flarm ID (IGC field `$VFLARMID` in header)
- Looks up name match on https://pilot.flarm.com
- Flags contestants whose glider is not registered or name mismatch suspected

**Usage:** "Validate all the flarms at WGC/EGC/FCC"

*Output:* Markdown report `reports/<comp>_flarm_validation.md`

---

#### `validate-igc-id`  
Validates each entrant's IGC ranking-list ID (the `Igc id` column) against the official IGC Ranking REST API (`https://rankingdata.fai.org/rest/api/rlpilot?id=N`). An ID is accepted only when it exists **and** the registered pilot's name matches the row — accent-, hyphen- and name-order tolerant.

Handles both local `.xlsx` files and Google Sheets URLs (auto-exports to xlsx).

**Usage:** Provide an entry spreadsheet path or Google Sheets URL with `Igc id` column

*Output:* Markdown report (`reports/<stem>_igc_id_validation.md`) plus coloured .xlsx workbook copy

---

#### `check-club-handicaps`
Verifies every contestant's assigned handicap in a handicapped class matches the official IGC list:
- Fetches contestants via SoaringSpot MCP (`get_class_contestants`)
- Matches aircraft models against the Club Class or 20m Multi-Seat handicap list
- Flags: **OK**, **DIFF** (handicap differs), **UNMATCHED** (glider not found), **NO_HANDICAP**

Applies judgement to `DIFF` rows — differences often reflect legitimate takeoff-mass or winglet adjustments per Annex A.

**Usage:** "Check the Club class handicaps at WGC/EGC/FCC"

*Output:* RTF report (`reports/SS.<comp>_club_handicap_check.rtf`) with summary + per-contestant table

---

### 📥 Data Download Skills  

#### `download-all-the-igc-files`  
Downloads all pilots' IGC flight files from a completed SGP competition, one `.zip` per day (or combined).

**Usage:** "Download the complete set of igc files for sgpaero/competition <id>"

*Output:* `sgp/<comp_id>/IGC/day_<N>/<number>.igc.zip`

---

#### `download-igc`  
Downloads a single pilot's IGC file from an SGP competition using the day and competition number.

**Usage:** "Get <name>'s IGC for day <X> of sgpaero/competition <id>"

*Output:* `.IGC` text written to working directory or `sgp/<comp_id>/IGC/day_<N>/<number>.igc`

---

### 📋 SeeYou Integration

#### `gen_cucx_from_sgp`  
Generates a **SeeYou Competition** (`.cucx`) file from an SGP competition — pilots, tasks with turnpoints, results. The `.cucx` is a ZIP archive containing:
- SQLite database (`contest.db`) in SeeYou format
- Embedded `.cup` waypoint files referenced by day/task

**Usage:** "Generate the cucx for sgpaero/competition <id>"

*Output:* `SGP/<comp_id>.cucx`

---

## Formulas & Reference Documentation

All formulas live under `/home/angel/formulas/`:

| File | Description |
|------|-------------|
| **ANNEX-A.md** | Complete FAI Sporting Code Annex A (Section 3) — World and Continental Gliding Championship rules. The authoritative source for task setting, scoring algorithms, eligibility criteria |
| **annex_a_scoring.formula.md** | Summary of the Annex A result calculation formula (§5): `score = Vm × R / FV`. Includes glide factor (GF), speed record (SR) definitions, minimum/maximum distance handling |
| **club_class_handicaps.md** | IGC Club Class glider handicaps — aircraft model → base handicap mapping. Used by `check-club-handicaps` skill |
| **20m_multiseat_handicaps.md** | 20 Metre Multi-Seat class glider handicaps (Arcus T, Duo Discus X/T/XL, etc.) |
| **teamcup.formula.md** | FAI Team Cup scoring algorithm: per-day team points = top 3 pilots × their individual scores. Explains tie-break rules and minimum pilot requirements |
| **pilot-of-the-year.md** | Criteria for IGC Pilot of the Year awards — annual best performances by class |
| **goranax.formula.md** | Goran Axén Trophy (best Standard Class performance) selection criteria |
| **robert.kronfeld.challenge.cup.formula.md** | Robert Kronfeld Challenge Cup formula for youth pilots under 23 |
| **seeyou_cup_file_format.md** | SeeYou `.cup` and `.cucx` file format reverse-engineered documentation — SQLite schema, coordinate encoding (radians), content hash algorithm |
| **IGCformat.md** | IGC flight recorder file specification: header records ($VHFLARMID for Flarm ID extraction), fix data block structure (
C\tX	Y	Z	A×10 M×10 S/3600 Q flag) |

---

## Python Tools (Direct CLI)

### `.cucx` Generator  
The `gen_cucx_from_sgp` skill's underlying tool — generates SeeYou Competition files from SGP data.

```bash
# Generate complete competition cu c x file (all days, all pilots)
python3 tools/make_cucx.py --comp-id 93 --day ALL --out norway_sgp_2026.cucx
```

**Components:**
- `tools/cucx_db.py` — SQLite schema creation & insertion (contests, classes, pilots, tasks, turns)
- `tools/cucx_geo.py` — Geometry conversion: SeeYou radians ← WGS84 degrees; turnpoint decoding  
- `tools/cucx_hash.py` — Content hash calculation for `.cucx` integrity verification
- `tools/cucx_schema.sql` — SQLite DDL matching the reverse-engineered `.cup` format

**Tests:** Full pytest suite under `/home/angel/tools/tests/` with recorded SGP fixtures (no network required)
```bash
tools/
pip install pytest
pytest tools/tests/
```

---

## Data Sources & MCP Servers  

### SoaringSpot (MCP)  
Official WGC/EGC/FCC competition platform. Provides:
- Contest metadata, class definitions, task geometry with turnpoints  
- Contestant entries, IGC file submissions, scored results
- Team Cup standings per day/class

**Credentials:** Per-competition — stored under `src/SoaringSpot/<comp>/` (`clientid`, `secretkey`) — not universal keys.

### SGP.Aero.AI (MCP)  
Sailplane Grand Prix data from [crosscountry.aero](https://www.crosscountry.aero): events, pilots, tasks with decoded turnpoints, per-day results and cumulative standings. Also validates pilot FAI ranking-list IDs via the IGC Ranking API.

---

## Reports Directory Structure  

Generated reports are stored under `/home/angel/reports/`:

| Pattern | Description |
|---------|-------------|
| `SS.<comp>_competition_report_<date>.docx` | SoaringSpot daily competition report (flights, km, hours per class) |
| `CPAS.<comp>_summary_report_<date>.docx` | CPAS safety/incursion summary with weather context |
| `<stem>_fai_license_validation.md` + `.xlsx` | FAI licence validation results for an entry sheet |
| `<comp>_flarm_validation.md` | Flarm ID verification report per contest |
| `SS.<comp>_teamcup_standings.md` | Team Cup standings (per-day aggregation of top-3 team scores) |
| `		<stem>_igc_id_validation.md` + `.xlsx`	`|	IGC ranking-list ID validation for entry sheet  |

---

## Example Workflows  

### Daily EGC/WGC/FCC Report Generation  
```bash
# Via skill invocation (preferred)
cp /home/angel/skills/ss-report/SKILL.md SKILLS_PATH=/current/path/	
```

Or manually:
```bash
/home/angel/.venv-report/bin/python src/tools/make_competition_report.py \
  --data-dir reports/.report_data/<comp>
```

### FAI Licence Batch Validation  
```bash
python3 .claude/skills/validate-fai-licenses/scripts/validate_licenses.py \		--excel "egc2026-pilots-and-captains.xlsx" --generated 2026-07-24
tools/make_cucx.py```

### SeeYou `.cucx` Generation from SGP Competition  
```bash
python3 tools/make_cucx.py --comp-id 93 --day ALL --out norway_sgp.cucx	
```

---	
## License

[MIT](LICENSE)

---

**Related Projects:**
- [SGP.Aero.AI](https://github.com/acasadoalonso/SGP.Aero.AI) — Sailplane Grand Prix MCP server  
- Crosscountry.aero (CPAS) — Official SGP data and safety analysis platform
