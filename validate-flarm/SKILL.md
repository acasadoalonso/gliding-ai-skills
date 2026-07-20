---
name: validate-flarm
description: >-
  Validate the FLARM/OGN trackers of every contestant in a SoaringSpot
  competition against the Ktrax range analyser (ktrax.kisstech.ch), saving
  each device's range plots. Use whenever the user wants to check, validate,
  verify, or audit the FLARM devices / trackers / live_track_id of a
  competition's gliders — "validate the flarms for EGC 2026", "are all
  trackers transmitting", "get the Ktrax range reports/plots", "check FLARM
  coverage" — for any contest with credentials under src/SoaringSpot/.
  Extracts each contestant's live_track_id (never the flight_recorders
  field), queries Ktrax with the last 6 hex digits, saves one report file
  per track-id (named with the contestant's competition number, CN) plus
  the RSSI and distances SVG plots into src/reports/, and writes a
  per-contestant summary flagging devices with no data, missing track ids,
  and callsign/registration mismatches.
---

# Validate contestant FLARM trackers against Ktrax

Check that every glider in a competition has a working FLARM/OGN tracker by
pulling each contestant's `live_track_id` from SoaringSpot and fetching that
device's **Ktrax range report** (`https://ktrax.kisstech.ch/plot?device=<id>`).
A bundled script does the deterministic work (SoaringSpot REST walk, Ktrax
fetches, plot downloads, reports); this file explains the workflow and how to
read the result.

Key facts the script relies on:

- The device ID is the **last 6 hexadecimal digits** of the `live_track_id`
  (e.g. `OGNC30A84:FLRD03425` → `D03425`, `FLADDD93F` → `DDD93F`).
- **Never use the `flight_recorders` field** — it holds logger notes, not the
  tracker ID.
- The Ktrax plot page embeds two server-generated SVGs per device
  (`…-rssi.svg`, `…-distances.svg`); their paths carry a `flarm:`/`icao:`
  prefix, so they are scraped from the page, never constructed.

## Inputs to collect

1. **Competition** — the credentials directory name under `src/SoaringSpot/`
   (e.g. `egc2026`, `wgc2026`). **Ask the user if not provided.** The contest
   ID comes from the client-ID prefix, so no contest lookup is needed.

## Procedure

Run from the repo root (`/home/angel`) so `src/` paths resolve:

```bash
python3 .claude/skills/validate-flarm/scripts/validate_flarm.py --comp egc2026
```

Options: `--out-dir` (default `src/reports`), `--credentials-dir` (override
`src/SoaringSpot/<comp>`).

What the script does:
1. Reads `clientid`/`secretkey`, walks contest → classes → contestants.
2. For each contestant takes `live_track_id`; skips (and reports) those
   without one.
3. Fetches the Ktrax range report once per unique device and saves, per
   track-id, into `src/reports/flarm_<comp>/`:
   `<CN>_<device>.md` (pilot, registration, track id, callsign, last
   measurement, firmware versions) + `<CN>_<device>-rssi.svg` +
   `<CN>_<device>-distances.svg`, where `<CN>` is the contestant's
   competition number (dropped when the contestant has none; a device shared
   by two contestants is saved once, under the first one's CN).
4. Writes the summary `src/reports/<comp>_flarm_validation.md`.

## How each contestant is classified

| Status | Meaning |
| :--- | :--- |
| **OK** | Ktrax has measurements for the device (a `Last measurement` timestamp exists) |
| **NO DATA** | Device resolves on Ktrax but has no measurements — likely not transmitting |
| **NO TRACK ID** | Contestant has no `live_track_id` in SoaringSpot |
| **BAD TRACK ID** | `live_track_id` present but its last 6 characters are not hexadecimal |
| **FETCH ERROR** | Ktrax was unreachable — not proven bad, re-run |

An OK row still gets a **note** when the Ktrax callsign differs from the
contestant's aircraft registration — usually a stale OGN DDB entry, a
mistyped `live_track_id`, or the same device pasted onto two contestants
(the duplicate shows the *other* glider's callsign).

## After running

- Tell the user both output paths and the status counts.
- Call out the interesting rows: NO DATA devices (tracker off / not
  installed), callsign-mismatch notes, and duplicated devices (same device
  link on two rows).
- A stale `Last measurement` (days before the contest) is worth mentioning
  even though it counts as OK.
- Classes often have zero coverage before organisers load the tracker IDs —
  a high NO TRACK ID count for a whole class means the data isn't in
  SoaringSpot yet, not that the FLARMs are broken.
- Ktrax only reports recent activity, so validation is only meaningful
  during (or just before) the contest. Run after it ends and NO DATA merely
  means the glider isn't flying *now* — say so when reporting.

## Example

User: "Validate the FLARM trackers for EGC 2026."

```bash
python3 .claude/skills/validate-flarm/scripts/validate_flarm.py --comp egc2026
```

→ `src/reports/egc2026_flarm_validation.md` (35 OK, 49 NO TRACK ID; 3
callsign mismatches flagged) plus `src/reports/flarm_egc2026/` with one
`.md` + two `.svg` per device, named `<CN>_<device>` (e.g. `AC_D03425.md`).
Then summarise counts and highlight the mismatches.

## Notes

- Re-running is safe and idempotent: files are rebuilt from scratch.
- One Ktrax fetch per unique device (~35 devices ≈ a minute).
- This skill replaces the retired `get-flarm-report` skill, which compiled
  an inline report via MCP/WebFetch without validating or saving plots.
