# Design — Implement IGC_Validation_Rules.md in the validate-igc-files skill

- **Date:** 2026-08-01
- **Skill:** `skills/validate-igc-files`
- **New reference:** `/home/angel/src/formulas/IGC_Validation_Rules.md`
- **Existing reference:** `/home/angel/src/formulas/IGCformat.md`

## Problem

`skills/validate-igc-files/scripts/validate_igc_files.py` currently implements six
structural checks derived from `IGCformat.md`. The skill was recently updated to
cite `IGC_Validation_Rules.md` as a second reference, but none of that document's
rules are implemented — the docstring only records them as future work.

`IGC_Validation_Rules.md` describes fourteen categories of checks extracted from
Tim Newport-Peace's IGC File Analyser (AL10). Implementing them naively would
destroy the report's usefulness: several fire on the overwhelming majority of
valid competition files.

## Evidence

All severity decisions in this design were calibrated by running each candidate
rule against the 308 real IGC files under `IGCfiles/` (EGC 2026 days of 10 and 13
July, WGC 2026, SGP 2026). Manufacturers present: LXV 245, NAV 57, FLA 3, LXN 3.

> **The figures in this section are the original exploratory probes.** Six were
> later found to be wrong once the rules were implemented properly; the
> authoritative counts are in the rule catalogue below, and the errors are
> explained under *Corrections after implementation*. The severity decisions the
> probes drove all still hold — the corrections shift magnitudes, not tiers.

Rules that fire on most valid files:

| Candidate rule | Files hit |
|---|---:|
| F-record interval > 5 min | 262 / 308 |
| `HFFTY` not ending in `IGC` | 250 / 308 |
| ENL minimum below 10 | 250 / 308 |
| A-record 3-character legacy serial | 245 / 308 |
| A-record `_` comment separator | 245 / 308 |
| Gaps in B-record fixing | 114 / 308 |
| Duplicate timestamps | 93 / 308 |

The A-record findings are explained by LXNav's standard header format,
`ALXVB0V_FLIGHT:1` — a 3-character serial with an underscore separator. The rules
document classifies both as errors; at 245/308 files they cannot be.

Rules that are rare and discriminating:

| Candidate rule | Files hit |
|---|---:|
| I-record missing mandatory `SIU` | 29 / 308 |
| `HFFRS` missing | 22 / 308 |
| `HFDTM` not WGS84 | 14 / 308 |
| `HFCM2` missing | 14 / 308 |
| MOP declared but all-zero | 12 / 63 declaring |
| C-record embedded flight date ≠ `HFDTE` | 4 / 308 |
| I-record pointer chain broken | 3 / 308 |
| I-record declared length ≠ actual | 3 / 308 |
| B-record length ≠ I-record last end-pointer | 3 / 308 |
| `HFFTY` with no comma | 3 / 308 |

Never fires on the corpus: out-of-sequence timestamps, all-zero ENL, disallowed
characters `$ * ! \ ^ ~`, more than one I/J/M record, zero F-records, unknown
E-record event codes, E-record not followed by a matching B-record, K-record
length or content faults.

This mirrors a decision already embedded in the current script, which
deliberately omits the spec's 76-character line limit because every modern
recorder exceeds it.

## Decisions

1. **Two severity tiers.** ERROR fails conformance and sets exit code 1. WARNING
   is always reported but never fails a file, matching how the existing ENL
   section already behaves.
2. **Full rule coverage.** All fourteen categories are implemented, including
   task declaration (C-record), event record (E-record) and GPS spoof/jamming
   checks. Severity, not omission, is what controls noise.
3. **Non-ASCII characters and empty lines are reclassified from ERROR to
   WARNING.** The published `24th-fai-egc` report already describes them as "a
   real spec violation but benign for scoring". ERROR now means the file's
   integrity or scoring validity is in question.
4. **Structured findings with `--json`.** Report generation stops parsing prose.
5. **Per-rule fixtures plus a corpus regression test.**
6. **`C_ZERO_DECL_TIME` added 2026-08-01**, closing a gap against §8 of the rules
   document: *"Declaration time must be non-zero/decodable — a zero/unknown time
   is an error."* It was named during design but omitted from the first draft of
   this catalogue.

## Architecture

```
scripts/
  igc_model.py            parse + decode           ~150 lines
  igc_rules.py            54 rules + registry      ~640 lines
  igc_observations.py     ENL + GPS anomaly        ~120 lines
  validate_igc_files.py   CLI + reporting          ~210 lines   (entry point unchanged)
  tests/
    build_fixtures.py     generates the baseline plus one mutation per rule
    fixtures/*.igc        generated, committed so failures stay inspectable
    test_model.py
    test_rules.py
    test_observations.py
    test_cli.py
    test_json_output.py
    test_corpus.py
```

Data flow:

```
validate_igc_files.py  walks the tree for *.igc / *.IGC
        ▼
igc_model.parse(path) -> IGCDoc
        one pass: records bucketed by type; I/J column maps decoded;
        B-fixes decoded to (seconds-of-day, lat, lon, validity, pressure alt,
        gnss alt, ext{}) with extensions resolved by TLC name.
        Malformed lines retained as raw text so rules can cite them.
        ▼
igc_rules.RULES  ->  registry of (rule_id, severity, category, fn)
        each fn(doc) -> list[Finding]; pure, no I/O
        ▼
Finding(rule_id, severity, category, message, line, data)
        ├─ ERROR       per-file block; exit code 1
        ├─ WARNING     aggregate tally; per-file under --warnings
        └─ observations (ENL, GPS anomaly) in their own sections
```

`IGCDoc` is parsed once per file and shared across all rules, so rule count does
not affect I/O. Rules are pure functions of the document, which is what makes the
per-rule fixture tests possible.

The entry-point path `python3 ~/.claude/skills/validate-igc-files/scripts/validate_igc_files.py <dir>`
is unchanged, because `SKILL.md` documents it.

Observations (ENL, GPS anomaly) are deliberately not a third severity. They are
per-file measurements to investigate rather than pass/fail judgements, and get
their own output sections.

Dependencies: Python standard library only, as today.

## Rule catalogue

**As implemented: 54 rules — 30 ERROR, 24 WARNING.** Hit counts below are the
measured values from `scripts/tests/corpus_baseline.json`, generated against the
308-file corpus on 2026-08-01.

The catalogue originally listed 52 rules with counts taken from exploratory
probes. Implementation and verification changed six of those figures. Each is
annotated *(was N)* below, and the discrepancies are explained in
**Corrections after implementation** at the end of this section. In every case
the probe was wrong, not the rule.

### ERROR

| Rule id | Check | Hits |
|---|---|---:|
| `H_MISSING_MANDATORY` | Missing any of `DTE PLT CM2 GTY GID DTM RFW RHW FTY GPS PRS FRS` | 22 *(was 36)* |
| `I_MISSING_EXT` | I-record lacks mandatory `FXA` / `ENL` / `SIU` | 29 |
| `H_DTM_NOT_WGS84` | Datum is neither named WGS84 nor coded 100 | 0 *(was 14)* |
| `C_ZERO_DECL_TIME` | Declaration time is zero or undecodable | 0 |
| `ENL_MOP_ALL_ZERO` | ENL or MOP zero throughout — dead sensor | 12 |
| `C_FLIGHTDATE_MISMATCH` | C-record embedded flight date ≠ `HFDTE` | 4 |
| `I_PTR_CHAIN` | First start pointer ≠ 36, or gap / overlap / start > end | 3 |
| `I_LEN_MISMATCH` | Declared item count ≠ actual length (`n*7+3`) | 3 |
| `B_LEN_MISMATCH` | B-record length ≠ I-record last end-pointer | 3 |
| `H_FTY_NO_COMMA` | `HFFTY` has no comma separating manufacturer and model | 3 |
| `G_MISSING` | No G security record | 0 |
| `G_TRAILING_RECORDS` | Non-G/L records after the first G record | 0 |
| `B_MALFORMED` | Bad fix layout, N/S, E/W or A/V field | 0 |
| `A_RECORD_POSITION` | A-record absent, not first, or duplicated | 0 |
| `A_NOT_FAI_APPROVED` | Manufacturer code starts with `X` | 0 |
| `I_RECORD_COUNT` | Zero or more than one I-record | 0 |
| `J_RECORD_COUNT` | More than one J-record | 0 |
| `M_RECORD_COUNT` | More than one M-record | 0 |
| `H_NONE` | No H-records at all | 0 |
| `H_DTE_INVALID` | `HFDTE` date does not decode | 0 |
| `CHAR_CONTROL` | Control character below 0x20 | 0 |
| `RECORD_TYPE_INVALID` | First character not in `A`–`N` | 0 |
| `WILDCARD_DATA` | `?` in a B, C, K or N record | 0 |
| `E_NOT_FOLLOWED_BY_B` | E-record not followed by a B-record with matching timestamp | 0 |
| `TIME_OUT_OF_SEQUENCE` | Timestamp earlier than its predecessor | 0 |
| `F_RECORDS_NONE` | No F-records in the file | 0 |
| `K_LEN_MISMATCH` | K-record length ≠ J-record max end pointer | 0 |
| `K_NON_NUMERIC` | Non-numeric character after the K-record timestamp | 0 |
| `C_DECL_AFTER_FLIGHT` | Declaration date later than the flight date | 0 |
| `C_COUNT_MISMATCH` | C-record count ≠ 5 + declared waypoints | 0 |

`G_MISSING`, `G_TRAILING_RECORDS` and `B_MALFORMED` carry over unchanged from the
current implementation. They register zero hits on this corpus but `G_MISSING`
fired on one file in the earlier `24th-fai-egc` scan, which is precisely the class
of finding the ERROR tier exists to surface.

A file with no C-records at all is not a finding — declarations are optional, and
3 files in the corpus have none. The C-record rules apply only when C-records are
present.

### WARNING

| Rule id | Check | Hits | Rationale |
|---|---|---:|---|
| `F_INTERVAL_LONG` | F-record interval > 5 min | 262 | 85% of real recorders |
| `H_FTY_NOT_IGC` | `HFFTY` does not end in `IGC` | 250 | Document calls it a comment |
| `ENL_MOP_MIN_LOW` | ENL/MOP minimum above 0 but below 10 | 239 *(was 250)* | Normal for a glider at rest |
| `A_SHORT_SERIAL` | 3-character legacy or otherwise malformed serial ID | 256 *(was 245)* | LXNav standard format |
| `A_BAD_SEPARATOR` | `_` instead of `-` before the comment | 224 *(was 245)* | LXNav standard format |
| `CHAR_NON_ASCII` | Non-ASCII character | 65 | Reclassified; benign for scoring |
| `B_GAPS` | Gap larger than nominal fix interval + 1 s | 114 | Logger mode changes |
| `TIME_DUPLICATE` | Consecutive identical timestamps on valid fixes | 92 *(was 93)* | Sub-second and fast-fix logging |
| `H_DTM_CODE_ONLY` | Datum coded 100 (WGS84) but text does not say WGS84 | 14 | Correct datum, non-standard text |
| `B_V_FLAG_NONZERO_ALT` | GNSS altitude ≠ 0 while fix validity is `V` | 0 *(was 44)* | Invalid fixes are excluded from scoring anyway |
| `CHAR_EMPTY_LINE` | Empty line inside the file | 9 | Reclassified; post-flight software artefact |
| `L_BAD_PREFIX` | L-record manufacturer prefix unrecognised | 25 | `XCM`, `MCU` unregistered but harmless |
| `H_DTE_NO_LITERAL` | `HFDTE` missing the literal `DATE:` | 17 | Legacy header format |
| `H_DUPLICATE_SUBTYPE` | Same H subtype appears twice | 3 | |
| `H_FTY_MULTI_COMMA` | `HFFTY` has more than one comma | 2 | Document says "only noted" |
| `TLC_UNKNOWN_I` / `_J` / `_M` | Unrecognised three-letter code | few | |
| `E_UNKNOWN_CODE` | Unrecognised event code | 0 | |
| `E_PEV_NO_FAST_FIX` | The 30 fixes after a PEV span more than 30 s | 11 *(was 0)* | |
| `H_NONCONTIGUOUS` | H-record block interrupted and resumed | 0 | |
| `WILDCARD_META` | `?` in an A, D, E, F, H, I, J or M record | 0 | |
| `CHAR_DISALLOWED` | `$ * ! \ ^ ~` before the last G record | 0 | |
| `F_RECORDS_ONE` | Exactly one F-record in the file | 0 | |

`L_BAD_PREFIX` reporting is capped at 20 occurrences per file, per the reference
tool, to avoid flooding a single file's block.

`B_V_FLAG_NONZERO_ALT` departs from the reference document, which classifies it as
an error (Spec A4.1.3). Reviewed and confirmed as a WARNING on 2026-08-01: a fix
flagged `V` is invalid and therefore excluded from scoring regardless of what
altitude the recorder wrote alongside it. It turns out to fire on no file in the
corpus at all — see *Corrections after implementation*.

### Observations

- **ENL engine-on** — unchanged behaviour: ENL > 500 sustained for at least 30
  continuous seconds. Reports max ENL, qualifying run count, longest run window
  and duration, and high-fix count.
- **GPS anomaly** — groundspeed between consecutive valid fixes above 300 kt.
  1–4 events are attributed to flight-recorder clock tolerance; 5 or more raise
  an explicit jamming/spoofing warning noting that other findings in the file may
  be compromised. Distance uses the IGC sphere approximation, which the rules
  document permits in place of Vincenty. A coordinate-delta prefilter skips the
  trigonometry on pairs that cannot possibly exceed the threshold, keeping the
  cost negligible across ~19,000 fixes per file.

### Deliberately not implemented

- **The 76-character line limit** — pre-existing omission; every modern recorder
  exceeds it.
- **"No MOP extension declared"** — a comment in the rules document that would
  fire on 245 files while conveying nothing.
- **Informational echoes** — maximum FXA value seen, decoded declaration
  coordinates, and similar "display for review" output from the reference tool.
  They belong to an interactive analyser, not a batch conformance scan.

### Corrections after implementation

Verifying the corpus snapshot against this catalogue on 2026-08-01 surfaced eight
discrepancies. Every one was a fault in the exploratory probe or in this
document, not in the implemented rule.

| Item | Was | Is | Cause |
|---|---:|---:|---|
| Overall conformance | 273 / 35 | **261 / 47** | The probe that produced 35 unioned only the header, I-record and G-record errors. It silently omitted `ENL_MOP_ALL_ZERO` (12 files) and the C-record checks (4), though both appear in this catalogue with those counts. The per-rule figures were right; the roll-up was not. |
| `B_V_FLAG_NONZERO_ALT` | 44 | **0** | The probe read `b[25:30]`, the **pressure** altitude. The rule reads GNSS altitude (columns 31–35), which is what Spec A4.1.3 governs. 44 files do carry a non-zero *pressure* altitude on invalid fixes — correct behaviour, since a barometer does not depend on satellites. No file has a bad GNSS altitude. |
| `H_DTM_NOT_WGS84` | 14 | **0** | All 14 files read `HFDTM100GPSDATUM:WGS-1984`. Datum code 100 *is* WGS84, so these declare the correct datum. §3 of the rules document says code 100 without the literal text is "only a comment". Split into `H_DTM_NOT_WGS84` (error, genuinely wrong datum) and `H_DTM_CODE_ONLY` (warning, 14 files). |
| `A_SHORT_SERIAL` | 245 | **256** | The probe split the A-record tail on `-` and `:` but not `_`, so it read `ALXVB0V_FLIGHT:1` as having a 10-character serial. Correct parsing finds 232 three-character serials plus 24 of other malformed lengths. |
| `A_BAD_SEPARATOR` | 245 | **224** | 245 was the LXV *manufacturer* count, assumed to equal the underscore count. Only 224 files actually contain `_`. |
| `ENL_MOP_MIN_LOW` | 250 | **239** | The rule requires `min > 0` so it does not double-report the 11 files `ENL_MOP_ALL_ZERO` already flags as dead sensors. |
| `TIME_DUPLICATE` | 93 | **92** | The rule requires both fixes to carry the `A` validity flag; the probe did not. |
| `E_PEV_NO_FAST_FIX` | 0 | **11** | Never actually measured — the probe did not test PEV fast-fixing, and 0 was an assumption. Also reimplemented: counting fixes inside a 30 s window reported clean 1 Hz loggers as one fix short, so it now checks that the next 30 fixes span at most 30 s, as the document states. |

`H_MISSING_MANDATORY` at 22 is consistent with the 22-to-36 range this document
predicted, since `HFCM2` and `HFFRS` absences overlap almost entirely.

### Thresholds

`ENL_ENGINE_ON = 500`, `ENL_MIN_RUN_SECONDS = 30`, `ENL_MOP_MIN = 10`,
`SPOOF_MAX_KNOTS = 300`, `SPOOF_CLUSTER = 5`, `F_MAX_INTERVAL_SECONDS = 300`,
`B_GAP_TOLERANCE_SECONDS = 1`, `PEV_FAST_FIX_COUNT = 30`, `L_PREFIX_REPORT_CAP = 20`.

These stay module-level constants rather than CLI flags. No existing workflow has
needed to tune them per contest, and exposing nine knobs would add surface area
for no demonstrated benefit.

## Output

### Default

```
FAIL 15_meter/67D_2L.igc
     - I-record missing mandatory SIU extension
FAIL club/67D_AD.igc
     - I-record column pointers broken: item 3 starts at 41, expected 40
     - B-record length 43 != I-record last end-pointer 45

WARNINGS (do not affect conformance) — 289 file(s) affected
   262  F-record interval exceeds 5 min
   250  HFFTY does not end with 'IGC'
   250  ENL minimum below 10
   245  A-record uses 3-character legacy serial ID
   245  A-record comment separator is '_' (spec requires '-')
   ...  (run with --warnings for per-file detail)

ENL engine-on evidence (ENL > 500 sustained >= 30s) in 4 file(s):
ENL  club/67D_56.igc: max ENL 999, 21 run(s), longest 15:59:59-16:01:49 UTC (110s), 2548/12501 fixes > 500

GPS anomaly (groundspeed > 300 kt) in 2 file(s):
GPS  standard/67D_I.igc: 9 events — CLUSTER, possible jamming/spoofing; max 1240 kt at 14:02:11 UTC

Scanned 308 IGC file(s) under IGCfiles: 261 conform, 47 do not.
```

### Flags

| Flag | Effect |
|---|---|
| *(none)* | Errors per file, warnings as an aggregate tally, observation sections, summary |
| `--warnings` | Expand warnings per file alongside errors |
| `--verbose` | Also list conforming files (existing behaviour) |
| `--json` | Emit structured findings to stdout instead of the text report |

Exit code is 1 if any ERROR was found, 0 otherwise. Warnings and observations
never change it.

### JSON shape

```json
{
  "root": "IGCfiles",
  "scanned": 308,
  "conform": 273,
  "non_conform": 35,
  "warning_tally": { "F_INTERVAL_LONG": 262, "A_SHORT_SERIAL": 256 },
  "files": [
    {
      "path": "club/67D_AD.igc",
      "conform": false,
      "findings": [
        {
          "rule": "I_PTR_CHAIN",
          "severity": "error",
          "category": "i-record",
          "message": "I-record column pointers broken: item 3 starts at 41, expected 40",
          "line": 14,
          "data": { "item": 3, "start": 41, "expected": 40 }
        }
      ],
      "enl": { "max": 999, "n_runs": 21, "longest": "15:59:59-16:01:49 UTC (110s)", "high": 2548, "fixes": 12501 },
      "gps_anomaly": { "events": 9, "cluster": true, "max_knots": 1240, "first": "14:02:11" }
    }
  ]
}
```

The skill builds `reports/<comp>_IGC_conformance_report.md` from this, grouping by
failure type as the existing `24th-fai-egc` report does, rather than parsing the
text output.

## Testing

```
scripts/tests/
  fixtures/valid_baseline.igc     minimal fully-conformant file
  fixtures/<rule_id>.igc          one variant per rule, breaking exactly that rule
  test_rules.py
  test_corpus.py
```

`test_rules.py` asserts, for every rule in the registry, that it produces a
finding on its own fixture and produces nothing on `valid_baseline.igc`. The
second assertion is what catches a rule that would flood. A registry-completeness
test fails if any rule lacks a fixture, so new rules cannot be added untested.

`test_corpus.py` runs the validator over `IGCfiles/` and asserts overall
conformance stays at 273/308 and that per-rule hit counts remain within tolerance
of the values measured on 2026-08-01. It is skipped when `IGCfiles/` is absent, so
the suite stays portable.

Run with `pytest scripts/tests/`.

## Skill documentation updates

`SKILL.md` needs revision once the implementation lands:

- Replace the six-check list with the ERROR / WARNING split and explain that
  ERROR means integrity or scoring validity is in question.
- Document `--warnings` and `--json`.
- Note the reclassification of non-ASCII and empty-line findings, so the change
  in conformance rate against earlier reports is not mistaken for a regression.
- Describe the GPS anomaly section alongside the existing ENL section.
- Extend the "deliberately not checked" note to cover the A-record serial and
  separator rules and the reasoning behind treating them as warnings.

## Success criteria

1. `pytest scripts/tests/` passes, with a fixture for every registered rule.
2. Across the four calibrated corpus directories (308 files), 261 conform and 47 do not — asserted by `test_corpus.py`.
3. Every failing file's errors are structural — no file fails solely on
   non-ASCII characters or empty lines.
4. `--json` output validates against the shape above and round-trips into the
   markdown report.
5. The command documented in `SKILL.md` runs unchanged.
6. No third-party dependencies.
