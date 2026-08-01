---
name: validate-igc-files
description: >-
  Scan a directory tree for IGC flight logs (.igc/.IGC) and check every file
  against the FAI/IGC flight-log format (formulas/IGCformat.md and
  formulas/IGC_Validation_Rules.md), reporting only the files that do NOT
  conform and why. Use whenever the user wants to validate, check, verify, or
  audit the IGC files in a directory or folder — e.g. "check the IGC files in
  <dir>", "which of these flight logs are not conformant", "scan this folder
  for bad IGC files" — as opposed to validating a single downloaded file (that
  is the download-igc skill). Asks for the directory if not given, scans it
  recursively, and runs the bundled validator: 54 rules across two tiers, where
  ERROR means integrity or scoring validity is in question (missing mandatory
  headers or extensions, broken I-record pointers, wrong-length B/K records,
  bad task declarations, missing G security record) and WARNING covers spec
  deviations that do not invalidate the file (non-ASCII characters, legacy
  serial formats, F-record gaps). Also reports files with ENL engine-on
  evidence — sustained high Engine Noise Level in the B-record fixes — so use
  it too when the user asks which flights show engine running / ENL data /
  motor use in their IGC logs, and flags GPS jamming or spoofing where
  groundspeed between fixes is physically impossible.
---

# Validate IGC files in a directory

Batch-validate every IGC flight log under a directory against the FAI/IGC
flight-log format defined in `/home/angel/src/formulas/IGCformat.md` and
validation rules in `/home/angel/src/formulas/IGC_Validation_Rules.md`, and
report only the non-conforming files.

## Input to collect

**Directory** — the directory to scan. If the user did not name one, ask for
it before doing anything else. Globs are fine (e.g. `/nfs/tmp/24*`); resolve
the glob first and, if it matches several directories, ask which one (or scan
each if the user said so).

## Procedure

1. Confirm the directory exists. The scan is recursive and matches both `.igc`
   and `.IGC` extensions — no need to pre-list the files.

2. Run the bundled validator:

   ```bash
   python3 ~/.claude/skills/validate-igc-files/scripts/validate_igc_files.py <directory>
   ```

   It prints one `FAIL <relative path>` block per non-conforming file with the
   errors it hit, then a tally of warnings by rule, then the `ENL` and `GPS`
   observation sections, then a summary line. Exit code is 0 when every file
   conforms, 1 otherwise — warnings and observations never change it.

3. Report to the user: the summary counts, then the non-conforming files
   grouped by failure type (see below) so patterns stand out — e.g. all files
   from one logger model missing the same record. Then the ENL engine-on
   files, most-sustained first, then any GPS anomalies. Do not list conforming
   files unless asked.

4. When the user wants a written report, re-run with `--json` and build
   `reports/<comp>_IGC_conformance_report.md` from the structured output rather
   than from the printed text. Group by failure type, put serious findings
   first, and keep the ENL and GPS tables at the end, matching the existing
   `24th-fai-egc_IGC_conformance_report.md` layout.

## Two severity tiers

54 rules, in two tiers calibrated against 308 real competition files so the
default report stays readable.

**ERROR** — the file's integrity or scoring validity is in question. These fail
conformance and set exit code 1: a missing or malformed A/H/I/J/M record, any of
the 12 mandatory headers absent, a missing `FXA`/`ENL`/`SIU` extension, broken
I-record column pointers, a wrong-length B or K record, a genuinely wrong
geodetic datum, a task declaration inconsistent with the flight date, a missing
G security record, records after the G record, out-of-sequence timestamps, and a
dead ENL or MOP sensor.

**WARNING** — a real spec deviation that does not invalidate the file. Always
reported, never fails: non-ASCII characters, empty lines, LXNav's 3-character
serial and `_` separator, F-record intervals over 5 minutes, gaps in fixing,
duplicate timestamps, a non-zero GNSS altitude on an invalid fix, unrecognised
three-letter codes, and unregistered L-record prefixes.

Warnings are collapsed into a per-rule tally by default. Pass `--warnings` to see
them per file.

Several of these are classified as errors in `IGC_Validation_Rules.md` but fire
on most valid files — LXNav's A-record format alone accounts for 224 of 308
files. Treating them as errors would fail nearly every log of every contest. The
same reasoning keeps the spec's 76-character line limit unenforced.

## Options

| Flag | Effect |
|------|--------|
| *(none)* | Errors per file, warnings as a tally, observation sections, summary |
| `--warnings` | Expand warnings per file |
| `--verbose` | Also list conforming files |
| `--json` | Structured findings for report generation |

## Observations — never conformance failures

**ENL engine-on** — ENL > 500 sustained for at least 30 continuous seconds. The
sustain requirement matters: isolated high-ENL fixes are radio calls, gear
warnings or vario beeps, and a raw threshold flags ~75% of pure-glider files.
Aerotow reads 400–500; an onboard engine reads 700+. Each `ENL` line gives max
ENL, the qualifying run count, the longest run's window and duration, and the
high-fix count.

**GPS anomaly** — groundspeed above 300 kt between consecutive valid fixes. One
to four events is flight-recorder clock tolerance; five or more is flagged as a
cluster suggesting jamming or spoofing, in which case other findings in that file
may be unreliable. Relevant for contests in regions with active GPS interference.

Both are findings to investigate, not failures.

Deliberately **not** checked: the spec's 76-character line limit. Virtually
every modern IGC-approved recorder exceeds it (I/B records with extensions,
L records), so it would flag 100% of real files and drown the true findings. For
the same reason "no MOP extension declared" is not reported at all — it would
fire on 245 of 308 files while telling you nothing.

## Interpreting common findings

- **non-ASCII characters** — usually an accented pilot/site name in appended
  `LCU::`/`LSCS` comment records; a real spec violation but benign for scoring.
  A warning, not a failure.
- **empty line(s) inside file** — typically a blank separator inserted by
  post-flight software before appended L records. A warning.
- **datum coded 100 but text does not say WGS84** — the datum *is* WGS84 (code
  100 means WGS84); only the free text is non-standard. A warning.
- **no G record / records after G** — serious: the file is truncated,
  concatenated, or its security data was stripped. Flag these prominently.
- **broken I-record pointers / B-record length mismatch** — the B-record
  extension columns cannot be trusted, so ENL and other per-fix data from that
  file are unreliable.

## Example

User: "validate the IGC files under IGCfiles/egc2026_2026-07-13"

```bash
python3 ~/.claude/skills/validate-igc-files/scripts/validate_igc_files.py \
  IGCfiles/egc2026_2026-07-13
```

→ `Scanned 84 IGC file(s) … 68 conform, 16 do not.` Then summarize, e.g.: nine
files are missing the `HFFRS` security header or the mandatory `SIU` extension;
four have a dead MOP sensor reading zero across every fix; and `club/67D_CP.igc`
and `standard/67D_EC.igc` declare a flight date of `301299`, a placeholder that
does not match their `HFDTE` of `130726`. The warning tally shows the fleet-wide
patterns — 68 files with F-record intervals over 5 minutes, 67 with LXNav's
legacy 3-character serial — none of which affect conformance. The ENL section
flagged 4 files, longest `club/67D_56.igc` at 110 s up to ENL 999.

## Testing

The bundled suite covers every rule twice: it must fire on its own fixture and
stay silent on a conformant baseline. That second half is what stops a rule
quietly firing on most valid files.

```bash
python3 -m pytest ~/.claude/skills/validate-igc-files/scripts/tests/ -q
```

`test_corpus.py` additionally pins the per-rule hit counts across the four
calibrated contest directories (308 files, 261 conform / 47 do not). It is
skipped automatically when that corpus is not present.
