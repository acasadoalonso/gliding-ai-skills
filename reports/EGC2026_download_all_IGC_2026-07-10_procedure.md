# How all the IGC files for EGC 2026 on 2026-07-10 were downloaded

Documentation of the batch download performed on 2026-07-13 using the
`download-all-the-igc-files` skill. Result: **70 of 70 IGC files** (~75 MB)
saved to `/home/angel/IGCfiles/egc2026_2026-07-10/`, zero failures.

## Overview

The procedure walks the SoaringSpot data hierarchy top-down with the
`soaringspot` MCP server, then downloads each flight with the helper script
from the `download-igc` skill:

```
set_compname → contest ID → classes → task per class for the date
             → task results (flight ID + IGC filename per pilot)
             → download_igc.py loop per class
```

## Step by step

### 1. Point the MCP at the competition

```
set_compname(compname="egc2026")   →  comp_id 5337
```

This loads the per-competition API credentials (they are only valid for that
one competition).

### 2. Enumerate the classes

```
get_contest_classes(id=5337)
```

| Class | Class ID |
|-------|----------|
| Standard | 10227 |
| 15 Metre | 10226 |
| Club | 10225 |

### 3. Find each class's task for 2026-07-10

`get_class_tasks(<class_id>)` for each class, selecting the task whose
`task_date` is `2026-07-10`. On that date every class had only a **practice
task** ("Official Training day3", `task_number: -3`,
`result_status: practice`), so those were used — the skill prefers scored
days but falls back to practice when it is the only match.

| Class | Task ID |
|-------|---------|
| Standard | 10723786755 |
| 15 Metre | 10722738179 |
| Club | 10721689603 |

The task ID is the numeric ID in the task's `self` href
(`…/v1/tasks/10723786755`).

### 4. Collect every flight from the task results

`get_task_results(<task_id>)` for each task. Each embedded result that has a
flight carries the two values the downloader needs:

- `igc_file` — the filename, with a Windows-style path prefix, e.g.
  `"67A\\67A_HUN.igc"` (the script strips the prefix);
- the flight href, e.g. `…/v1/flights/10723786811` — the trailing number is
  the flight ID.

Results **without** an `igc_file`/flight link (pilot did not fly or no log
uploaded) are skipped and listed in the summary. There were 14 such pilots.

### 5. Download every flight

One bash loop per class over `flight_id:filename` pairs, calling the existing
helper script:

```bash
CID=$(cat /home/angel/src/SoaringSpot/egc2026/clientid)
SEC=$(cat /home/angel/src/SoaringSpot/egc2026/secretkey)
for pair in 10723786811:67A_HUN.igc 10723786814:67A_LEO.igc …; do
  python3 /home/angel/.claude/skills/download-igc/download_igc.py \
    --comp egc2026 \
    --clientid "$CID" --secretkey "$SEC" \
    --flight-id "${pair%%:*}" --filename "${pair##*:}" \
    --out-dir "IGCfiles/egc2026_2026-07-10" \
    || echo "FAILED: $pair"
done
```

The script builds the HMAC-SHA256 auth header, fetches
`…/v1/flights/<id>` (returns raw `application/vnd.flight+igc` content), and
refuses to save JSON/HTML bodies, so auth problems surface as clear errors
instead of corrupt `.igc` files. `|| echo FAILED` keeps the batch going past
individual failures.

**Gotcha found during this run:** the script looks for credentials under
`/home/angel/SoaringSpot/<comp>/` (relative to its repo root), but for
egc2026 they live in `/home/angel/src/SoaringSpot/egc2026/`. The fix is to
read `clientid`/`secretkey` yourself and pass them with
`--clientid`/`--secretkey`, as above. This fallback is now recorded in the
skill itself.

### 6. Verify and summarize

```bash
ls /home/angel/IGCfiles/egc2026_2026-07-10/ | wc -l   # → 70
du -sh /home/angel/IGCfiles/egc2026_2026-07-10/        # → 75M
```

The file count must equal the number of results that had an `igc_file`
(25 + 18 + 27 = 70 — it matched exactly).

## Result summary

| Class | Task ID | Downloaded | No log uploaded (skipped) |
|-------|---------|-----------:|---------------------------|
| Standard | 10723786755 | 25 | Jakub Barszcz (LOT), Łukasz Błaszczyk (I), Miloslav Cink (JB), Darius Gudziunas (H8) |
| 15 Metre | 10722738179 | 18 | Jonas Florin (JH), Vladimir Foltin (3), Vladas Motuza (M7) |
| Club | 10721689603 | 27 | Simon Gantner (MN), Toni Kittler (NZ), Dylan Osolian (CP), Jaume Prats (AL), Sara Salonen (HV), Kim Toppari (KT), Pascal Zollikofer (FC) |

## Key files

- Skill: `/home/angel/.claude/skills/download-all-the-igc-files/SKILL.md`
- Download script: `/home/angel/.claude/skills/download-igc/download_igc.py`
- Credentials: `/home/angel/src/SoaringSpot/egc2026/{clientid,secretkey}`
- Output: `/home/angel/IGCfiles/egc2026_2026-07-10/`

## Follow-up

To check the downloaded logs against the FAI/IGC flight-log format, run the
`validate-igc-files` skill on the output directory.
