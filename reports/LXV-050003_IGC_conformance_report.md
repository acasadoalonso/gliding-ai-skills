# IGC Conformance Report — LXV-050003 archive

- **Source scanned:** `/nfs/tmp/LXV-050003.zip` (extracted; the glob `/nfs/tmp/LXV*` matched a zip, not a directory)
- **Date of check:** 2026-08-17
- **Reference:** FAI/IGC flight-log format, `formulas/IGCformat.md`; rules per `formulas/IGC_Validation_Rules.md`
- **Files scanned:** 25
- **Conformant:** 11
- **Non-conformant:** 14

Only non-conformant files are listed. ERROR-tier findings (missing mandatory
records/headers/extensions, broken I-record pointers, wrong-length B/K records,
bad task declarations, missing or misplaced G record, dead ENL/MOP sensor) fail
conformance; WARNING-tier findings are reported but never fail. The spec's
76-character line limit is deliberately not enforced.

## Recorders in the archive

The zip is named for one serial but contains two, both LXNav S20 units:

| Serial (A record) | Glider type | Pilot | Files | Firmware seen |
|---|---|---|---:|---|
| `ALXV050003` | `Default` (not configured) | Uros K (Apr–Jun), Klaus Rheinwald (Jul–Aug) | 19 | 0.03 → 0.23 |
| `ALXV050004` | `Arcus M` | Uros Krasovic | 6 | 0.23 |

The `Arcus M` is a self-launching motorglider, which is the context for the ENL
section at the end of this report.

## Serious findings

| File | Problem |
|------|---------|
| `2026-06-07-LXV-050003-01.igc` | **Not a flight log.** 233 lines consisting of 214 `G` records and 19 `L` records only — **no A, no H, no I, no B records**. The header and the entire fix block are absent; only the trailing security block and LXNav comment records survived. Cannot be validated or scored. |
| `2026-04-02-LXV-050003-01.igc` | **2806 NUL bytes in a single contiguous block at line 2018**, occupying the position where the B/K sequence should continue, immediately before the closing `L`/`G` records. Header (firmware 0.03) is intact, so this is download/flash corruption that destroyed a chunk of the flight, not a bad write from the start. Also **MOP zero across all 989 surviving fixes** (dead sensor) and **no F records**. |

Both files should be re-downloaded from the recorder if the originals still
exist; neither can support a scoring claim as it stands.

## `?` in the task declaration (10 files)

Each of these carries 2 `C` records of the form:

```
C0000000N00000000E???
```

This is LXNav writing `???` as the *name* of the null takeoff/landing point
(zero coordinates = not declared). `?` is not permitted in `B`/`C`/`K`/`N`
records, so it is a genuine spec violation, but it sits in the name field only
and does not affect task geometry or scoring.

**All 10 are firmware 0.17 or older; no file on firmware 0.23 shows it** — the
recorder's firmware appears to have fixed this.

| File | Firmware | First offending line |
|------|---------:|---------------------:|
| `2026-05-14-LXV-050003-01.igc` | 0.06 | 20 |
| `2026-05-16-LXV-050003-01.igc` | 0.07 | 20 |
| `2026-05-16-LXV-050003-02.igc` | 0.07 | 20 |
| `2026-05-16-LXV-050003-03.igc` | 0.07 | 20 |
| `2026-05-16-LXV-050003-04.igc` | 0.07 | 20 |
| `2026-06-07-LXV-050003-03.igc` | 0.10 | 20 |
| `2026-06-07-LXV-050003-04.igc` | 0.10 | 20 |
| `2026-06-20-LXV-050003-01.igc` | 0.17 | 20 |
| `2026-06-20-LXV-050003-02.igc` | 0.17 | 20 |
| `2026-06-20-LXV-050003-03.igc` | 0.17 | 20 |

## No F (satellite constellation) records (4 files)

Regular F records are mandatory; without them the satellite constellation in
use cannot be audited for any part of the flight.

| File | Note |
|------|------|
| `2026-07-17-LXV-050003-01.igc` | fails on this alone |
| `2026-07-17-LXV-050003-03.igc` | fails on this alone (also a 25 s fixing gap at line 136) |
| `2026-04-02-LXV-050003-01.igc` | *also corrupted — see Serious findings* |
| `2026-06-07-LXV-050003-01.igc` | *also has no flight data — see Serious findings* |

## Warnings — do not affect conformance

| Rule | Files | Notes |
|------|------:|-------|
| `HFFTY` does not end with `IGC` | 24 | Every file with headers. All declare `HFFTYFRTYPE:LXNAV,S20` — a fleet-wide LXNav formatting habit, benign. |
| Gaps in B-record fixing beyond 1 s | 5 | Longest single gaps 19–27 s (`2026-07-17-…-02`, `-03`, `2026-07-30-LXV-050003-01`, `2026-08-06-LXV-050003-01`); `2026-08-09-LXV-050003-01` has 84 gaps but none longer than 3 s. |
| Only one F record in the whole file | 4 | `2026-05-14-…-01`, `2026-05-16-…-01`, `2026-05-16-…-02`, `2026-07-17-…-02`. |
| Duplicate timestamps between consecutive fixes | 3 | All three on the Arcus M: 23 (`07-29`), 28 (`07-30`), 24 (`07-31`). |
| F-record interval longer than 300 s | 2 | `2026-05-16-…-03` (301 s), `2026-05-16-…-04` (longest 601 s). |
| Invalid (`V`) fix carrying non-zero GNSS altitude | 1 | `2026-05-16-LXV-050003-04.igc`, 2 fixes, first 161 m at line 2145. |
| Unrecognised L-record manufacturer prefix | 1 | `2026-06-07-LXV-050003-01.igc`, 6 records with prefix `LXV`. |

## ENL engine-on evidence (8 files)

Files whose B-record ENL (Engine Noise Level) extension shows ENL > 500
sustained for at least 30 continuous seconds. These are findings to
investigate, **not** conformance failures. Sorted by longest sustained run.

| File | Glider | Max ENL | Runs | Longest run (UTC) | Duration | Fixes > 500 |
|------|--------|--------:|-----:|-------------------|---------:|------------:|
| `2026-08-10-LXV-050004-01.igc` | Arcus M | 999 | 2 | 10:50:13–11:00:26 | 613 s | 772 / 17955 |
| `2026-07-28-LXV-050004-01.igc` | Arcus M | 999 | 1 | 10:20:36–10:28:23 | 467 s | 488 / 18503 |
| `2026-07-29-LXV-050004-01.igc` | Arcus M | 999 | 1 | 10:11:30–10:17:49 | 379 s | 380 / 15859 |
| `2026-07-30-LXV-050004-01.igc` | Arcus M | 999 | 1 | 11:20:28–11:26:45 | 377 s | 405 / 13213 |
| `2026-07-31-LXV-050004-01.igc` | Arcus M | 999 | 1 | 11:07:44–11:13:55 | 371 s | 391 / 11490 |
| `2026-07-25-LXV-050004-01.igc` | Arcus M | 999 | 1 | 11:14:17–11:20:27 | 370 s | 401 / 12745 |
| `2026-08-09-LXV-050003-01.igc` | Default | 999 | 4 | 07:56:45–07:59:33 | 168 s | 420 / 2327 |
| `2026-08-06-LXV-050003-02.igc` | Default | 999 | 2 | 16:40:59–16:42:20 | 81 s | 179 / 1170 |

Notable: **all six Arcus M flights** show a single 6–10 minute run at ENL 999,
consistently in the 10:00–11:30 UTC window — the expected self-launch signature
of a motorglider, not an anomaly. The two `LXV-050003` files are different in
character: several shorter runs each, on a recorder whose glider type is left as
`Default`, so what the airframe actually is cannot be read from the file. Worth
a look if either flight was submitted as a pure-glider claim.

## GPS anomalies

**None.** No groundspeed above 300 kt between consecutive valid fixes in any of
the 25 files — no evidence of jamming, spoofing, or clock discontinuity.
