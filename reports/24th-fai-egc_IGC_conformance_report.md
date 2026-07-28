# IGC Conformance Report — 24th FAI EGC

- **Directory scanned:** `/nfs/tmp/24th-fai-egc` (recursive)
- **Date of check:** 2026-07-11
- **Reference:** FAI/IGC flight-log format, `formulas/IGCformat.md` (Jan 2026 / AL10)
- **Files scanned:** 123
- **Conformant:** 84
- **Non-conformant:** 39

Only non-conformant files are listed. Checks performed: A record first,
mandatory H records (DTE/PLT/GTY/GID/DTM, FXA via header or I record),
well-formed B-record fixes, record order, trailing G security record, no
empty lines, ASCII-only characters. The spec's 76-character line limit is
deliberately not enforced.

## Serious findings

| File | Problem |
|------|---------|
| `Club/2026-07-10/67A_CH.igc` | **No G (security) record** (plus an empty line at 20681). The file is truncated or its security data was stripped — it cannot be validated for scoring. |

## Non-ASCII / control characters (30 files)

A single line with control or non-ASCII characters, typically an accented
pilot or site name in appended `LCU::`/`LSCS` comment records — a real spec
violation (para 6 requires transliteration) but benign for scoring.

| File | First offending line |
|------|---------------------:|
| `Club/2026-07-08/678_A3.igc` | 31597 |
| `Club/2026-07-08/678_PP.igc` | 34083 |
| `Club/2026-07-09/679_PP.igc` | 7463 |
| `Club/2026-07-10/67A_A3.igc` | 28542 |
| `Club/2026-07-10/67A_AD.igc` | 50192 |
| `Club/2026-07-10/67A_CK.igc` | 12448 |
| `Club/2026-07-10/67A_PP.igc` | 25321 |
| `Club/2026-07-10/67A_XW.igc` | 22102 |
| `Meter 15/2026-07-08/678_2L.igc` | 15609 |
| `Meter 15/2026-07-08/678_AX.igc` | 15850 |
| `Meter 15/2026-07-08/678_BB.igc` | 20266 |
| `Meter 15/2026-07-08/678_IR.igc` | 11864 |
| `Meter 15/2026-07-08/678_PL.igc` | 15717 |
| `Meter 15/2026-07-09/679_2L.igc` | 14939 |
| `Meter 15/2026-07-09/679_IR.igc` | 11331 |
| `Meter 15/2026-07-10/67A_2L.igc` | 21476 |
| `Meter 15/2026-07-10/67A_AX.igc` | 13152 |
| `Meter 15/2026-07-10/67A_BB.igc` | 22269 |
| `Meter 15/2026-07-10/67A_IR.igc` | 15752 |
| `Meter 15/2026-07-10/67A_MB.igc` | 28683 |
| `Meter 15/2026-07-10/67A_PL.igc` | 10142 |
| `Standard/2026-07-08/678_JPA.igc` | 10953 |
| `Standard/2026-07-08/678_JW.igc` | 17239 |
| `Standard/2026-07-09/679_AU.igc` | 24227 |
| `Standard/2026-07-09/679_I.igc` | 12613 |
| `Standard/2026-07-09/679_JPA.igc` | 11446 |
| `Standard/2026-07-10/67A_42.igc` | 10489 |
| `Standard/2026-07-10/67A_AU.igc` | 33503 |
| `Standard/2026-07-10/67A_JPA.igc` | 10922 |
| `Standard/2026-07-10/67A_JW.igc` | 13577 |
| `Standard/2026-07-10/67A_WD.igc` | 20681 |

## Empty line(s) inside file (8 files)

Typically a blank separator inserted by post-flight software before appended
L records.

| File | First empty line |
|------|-----------------:|
| `Club/2026-07-08/678_LK.igc` | 30633 |
| `Club/2026-07-09/679_LK.igc` | 21185 |
| `Club/2026-07-10/67A_CH.igc` | 20681 *(also missing G record — see above)* |
| `Meter 15/2026-07-09/679_OS.igc` | 16571 |
| `Standard/2026-07-08/678_42.igc` | 12366 *(also a non-ASCII line at 12368)* |
| `Standard/2026-07-08/678_8C.igc` | 27364 |
| `Standard/2026-07-08/678_AB.igc` | 11324 |
| `Standard/2026-07-08/678_D7.igc` | 13007 |

## ENL engine-on evidence (8 files)

Files whose B-record ENL (Engine Noise Level) extension shows ENL > 500
sustained for at least 30 continuous seconds. These are findings to
investigate (possible motor-glider engine use), **not** conformance
failures. Sorted by longest sustained run.

| File | Max ENL | Runs | Longest run (UTC) | Duration | Fixes > 500 |
|------|--------:|-----:|-------------------|---------:|------------:|
| `Standard/2026-07-10/67A_TC.igc` | 999 | 1 | 14:52:54–15:03:00 | 606 s | 620 / 13229 |
| `Club/2026-07-08/678_FC.igc` | 999 | 49 | 14:37:18–14:39:41 | 143 s | 6243 / 18025 |
| `Meter 15/2026-07-08/678_RX.igc` | 854 | 1 | 16:01:06–16:02:19 | 73 s | 129 / 17910 |
| `Standard/2026-07-08/678_EC.igc` | 999 | 18 | 12:55:25–12:56:21 | 56 s | 6394 / 16152 |
| `Meter 15/2026-07-09/679_OS.igc` | 999 | 1 | 13:22:12–13:22:48 | 36 s | 55 / 12726 |
| `Meter 15/2026-07-10/67A_MB.igc` | 999 | 1 | 12:20:53–12:21:29 | 36 s | 56 / 14967 |
| `Standard/2026-07-10/67A_XC.igc` | 958 | 1 | 15:50:43–15:51:15 | 32 s | 69 / 13589 |
| `Standard/2026-07-09/679_I.igc` | 999 | 1 | 14:46:47–14:47:18 | 31 s | 196 / 11340 |

Notable: `67A_TC.igc` shows a continuous 10-minute run at ENL up to 999 —
strong evidence of an engine running. `678_FC.igc` and `678_EC.igc` have
very high total high-ENL fix counts (~35–40% of the flight) spread across
many runs, also worth a close look.
