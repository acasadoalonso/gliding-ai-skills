---
name: validate-igc-files
description: >-
  Scan a directory tree for IGC flight logs (.igc/.IGC) and check every file
  against the FAI/IGC flight-log format (formulas/IGCformat.md, Jan 2026 /
  AL10), reporting only the files that do NOT conform and why. Use whenever the
  user wants to validate, check, verify, or audit the IGC files in a directory
  or folder — e.g. "check the IGC files in <dir>", "which of these flight logs
  are not conformant", "scan this folder for bad IGC files" — as opposed to
  validating a single downloaded file (that is the download-igc skill). Asks
  for the directory if not given, scans it recursively, and runs the bundled
  validator (A record first, mandatory H records, well-formed B fixes, record
  order, trailing G security record, no empty lines, ASCII-only characters).
  Also reports files with ENL engine-on evidence — sustained high Engine
  Noise Level in the B-record fixes — so use it too when the user asks which
  flights show engine running / ENL data / motor use in their IGC logs.
---

# Validate IGC files in a directory

Batch-validate every IGC flight log under a directory against the FAI/IGC
flight-log format defined in `/home/angel/src/formulas/IGCformat.md`, and
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
   specific checks failed, then an `ENL` section listing files with engine-on
   evidence, then a summary line. Exit code is 0 when every file conforms, 1
   otherwise (ENL findings do not affect conformance or the exit code). Add
   `--verbose` only if the user asks to see the conforming files too.

3. Report to the user: the summary counts, then the non-conforming files
   grouped by failure type (see below) so patterns stand out — e.g. all files
   from one logger model missing the same record. Then the ENL engine-on
   files, most-sustained first. Do not list conforming files unless asked.

## Checks performed (from IGCformat.md)

- **A record** — the first line must be the FR manufacturer/ID record.
- **Mandatory H records** — DTE, PLT, GTY, GID, DTM headers present. FXA
  counts as present if declared either as an `HFFXA` header or as a B-record
  extension in the I record (modern Naviter loggers do the latter).
- **B records** — at least one fix; every B line matches the fix layout
  (time, lat/long with N/S/E/W, A/V validity flag, pressure + GNSS altitude)
  with a plausible timestamp.
- **Record order** — no H records after the first B record; nothing but G/L
  records after the first G record (a fix after the security record means a
  truncated or concatenated file).
- **G record** — at least one security record present.
- **Character set / structure** — no empty lines inside the file, no control
  or non-ASCII characters (spec para 6: accented characters must be
  transliterated).

Deliberately **not** checked: the spec's 76-character line limit. Virtually
every modern IGC-approved recorder exceeds it (I/B records with extensions,
L records), so it would flag 100% of real files and drown the true findings.

## ENL engine-on reporting

Alongside conformance, the validator reads the ENL (Engine Noise Level,
000–999) extension declared in the I record and reports files whose fixes show
the engine running: ENL > 500 **sustained for at least 30 continuous
seconds**. The sustain requirement matters — isolated high-ENL fixes are
radio calls, gear warnings, or vario beeps, and a raw threshold flags ~75% of
pure-glider files. Aerotow reads ~400–500; an onboard engine reads 700+.
Each `ENL` line gives max ENL, the number of qualifying runs, the longest
run's time window and duration, and the high-fix count. These are findings to
investigate (motor-glider engine use during a task), not conformance failures.

## Interpreting common failures

- **non-ASCII characters** — usually an accented pilot/site name in appended
  `LCU::`/`LSCS` comment records; a real spec violation but benign for
  scoring.
- **empty line(s) inside file** — typically a blank separator inserted by
  post-flight software before appended L records.
- **no G record / records after G** — serious: the file is truncated,
  concatenated, or its security data was stripped. Flag these prominently.

## Example

User: "validate the IGC files under /nfs/tmp/24th-fai-egc"

```bash
python3 ~/.claude/skills/validate-igc-files/scripts/validate_igc_files.py /nfs/tmp/24th-fai-egc
```

→ `Scanned 123 IGC file(s) … 84 conform, 39 do not.` Then summarize, e.g.:
36 files carry non-ASCII characters or stray blank lines in appended comment
records, and `Club/2026-07-10/67A_CH.igc` has **no G security record** (file
truncated — cannot be validated). The ENL section flagged 6 files with
engine-on evidence, e.g. `Standard/2026-07-10/67A_TC.igc`: a continuous
10-minute run at ENL up to 999 (14:52:54–15:03:00 UTC).
