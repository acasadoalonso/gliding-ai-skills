#!/usr/bin/env python3
"""Scan a directory recursively for .igc/.IGC files and validate each against
the FAI/IGC flight-log format (formulas/IGCformat.md, Jan 2026 / AL10).

Prints a report listing ONLY the files that do not conform, with the specific
checks each one failed. Exit code 0 if all conform, 1 if any file fails.

Usage:
    python3 validate_igc_files.py <directory> [--verbose]
"""

import argparse
import re
import sys
from pathlib import Path

# B record: B + HHMMSS + DDMMmmm[NS] + DDDMMmmm[EW] + [AV] + 5-digit pressure
# alt + 5-digit GNSS alt (altitudes may carry a leading '-'), then extensions.
B_RECORD_RE = re.compile(
    r"^B(\d{2})(\d{2})(\d{2})"      # time HHMMSS
    r"(\d{7})([NS])"                 # latitude DDMMmmm N/S
    r"(\d{8})([EW])"                 # longitude DDDMMmmm E/W
    r"([AV])"                        # fix validity
    r"(-\d{4}|\d{5})"                # pressure altitude
    r"(-\d{4}|\d{5})"                # GNSS altitude
)

# Mandatory header records (any source letter F/O/P accepted for robustness).
# FXA is checked separately: recorders may declare it as a B-record extension
# in the I record instead of an HFFXA header line.
MANDATORY_H = {
    "DTE": "flight date",
    "PLT": "pilot in charge",
    "GTY": "glider type",
    "GID": "glider ID",
    "DTM": "GNSS datum",
}

# Valid IGC character set (spec para 6) applies strictly to data records;
# free-text fields in practice carry lower case (the spec's own examples do),
# so we only reject control characters and non-ASCII bytes anywhere.
CONTROL_OR_NON_ASCII = re.compile(r"[^\x20-\x7e]")

# ENL (Engine Noise Level, 000-999) strictly above this value is treated as
# engine noise. Aerotow noise sits around 400-500 on most recorders; a
# running engine on board reads 700+. Isolated spikes (radio calls, gear
# warnings, vario beeps) also cross the threshold, so engine-on is only
# declared for a CONTINUOUS run of at least ENL_MIN_RUN_SECONDS.
ENL_ENGINE_ON = 500
ENL_MIN_RUN_SECONDS = 30


def enl_field(i_record):
    """Return (start, end) 1-based byte positions of ENL in B records, or None."""
    m = re.match(r"^I(\d{2})", i_record)
    if not m:
        return None
    for k in range(int(m.group(1))):
        ext = i_record[3 + k * 7: 10 + k * 7]
        if len(ext) == 7 and ext[4:] == "ENL":
            return int(ext[:2]), int(ext[2:4])
    return None


def validate_file(path):
    """Return (failures, enl) — failures is a list of strings (empty = file
    conforms); enl is a dict with engine-noise stats when the file shows
    engine-on evidence (max ENL > ENL_ENGINE_ON), else None."""
    failures = []
    try:
        raw = path.read_bytes()
    except OSError as e:
        return [f"unreadable: {e}"], None

    if not raw:
        return ["empty file"], None

    text = raw.decode("ascii", errors="replace")
    # Keep original lines to detect stray control chars; strip CR/LF only.
    lines = [ln.rstrip("\r\n") for ln in text.splitlines()]
    # Ignore trailing blank lines (common and harmless).
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ["empty file"], None

    # --- A record must be the first line ---
    first = lines[0]
    if not first.startswith("A"):
        failures.append(f"first record is not an A record (starts with {first[:10]!r})")
    elif len(first) < 7:
        failures.append(f"A record too short (needs 3-char manufacturer + 3-char serial): {first!r}")

    # --- collect record indices ---
    # No line-length check: the spec's 76-char limit is exceeded by virtually
    # all modern approved recorders (I/B records with extensions, L records).
    h_lines, b_indices, g_indices, i_records = [], [], [], []
    empty_lines, bad_chars, bad_b = [], [], []
    enl_pos = None
    enl_max, enl_high, enl_fixes = 0, 0, 0
    run_start = run_end = None          # current high-ENL run (secs of day)
    runs = []                           # completed runs: (start, end) secs
    for i, ln in enumerate(lines):
        if ln == "":
            empty_lines.append(i + 1)
            continue
        rec = ln[0]
        if CONTROL_OR_NON_ASCII.search(ln):
            bad_chars.append(i + 1)
        if rec == "H":
            h_lines.append((i, ln))
        elif rec == "I":
            i_records.append(ln)
            enl_pos = enl_pos or enl_field(ln)
        elif rec == "B":
            b_indices.append(i)
            m = B_RECORD_RE.match(ln)
            if not m:
                bad_b.append(i + 1)
            else:
                hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if hh > 23 or mm > 59 or ss > 59:
                    bad_b.append(i + 1)
                if enl_pos:
                    val = ln[enl_pos[0] - 1: enl_pos[1]]
                    if val.isdigit():
                        v = int(val)
                        enl_fixes += 1
                        enl_max = max(enl_max, v)
                        sec = hh * 3600 + mm * 60 + ss
                        if v > ENL_ENGINE_ON:
                            enl_high += 1
                            if run_start is None:
                                run_start = sec
                            run_end = sec
                        elif run_start is not None:
                            runs.append((run_start, run_end))
                            run_start = run_end = None
        elif rec == "G":
            g_indices.append(i)

    if empty_lines:
        failures.append(f"{len(empty_lines)} empty line(s) inside file (first at line {empty_lines[0]})")
    if bad_chars:
        failures.append(f"{len(bad_chars)} line(s) with control/non-ASCII characters (first at line {bad_chars[0]})")

    # --- mandatory H records ---
    h_text = "\n".join(ln for _, ln in h_lines)
    missing = [f"{tlc} ({desc})" for tlc, desc in MANDATORY_H.items()
               if not re.search(rf"^H[FOP]{tlc}", h_text, re.MULTILINE)]
    # FXA: either an HFFXA header line or an FXA extension declared in the I record.
    if not re.search(r"^H[FOP]FXA", h_text, re.MULTILINE) and \
       not any("FXA" in ln for ln in i_records):
        missing.append("FXA (fix accuracy, neither HFFXA header nor I-record extension)")
    if missing:
        failures.append("missing mandatory H record(s): " + ", ".join(missing))

    # --- B records ---
    if not b_indices:
        failures.append("no B (fix) records")
    if bad_b:
        failures.append(f"{len(bad_b)} malformed/truncated B record(s) (first at line {bad_b[0]})")

    # --- record order: all H records before the first B record ---
    if b_indices and h_lines:
        late_h = [i for i, _ in h_lines if i > b_indices[0]]
        if late_h:
            failures.append(f"H record(s) after the first B record (line {late_h[0] + 1})")

    # --- G security record: present, and nothing but G/L records after it ---
    if not g_indices:
        failures.append("no G (security) record")
    else:
        tail_bad = [i + 1 for i in range(g_indices[0] + 1, len(lines))
                    if lines[i] and lines[i][0] not in "GL"]
        if tail_bad:
            failures.append(
                f"{len(tail_bad)} non-G/L record(s) after the first G record "
                f"(first at line {tail_bad[0]}) — truncated or concatenated file")

    enl = None
    if run_start is not None:
        runs.append((run_start, run_end))
    long_runs = [(s, e) for s, e in runs if e - s >= ENL_MIN_RUN_SECONDS]
    if long_runs:
        hms = lambda s: f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
        s, e = max(long_runs, key=lambda r: r[1] - r[0])
        enl = {"max": enl_max, "high": enl_high, "fixes": enl_fixes,
               "n_runs": len(long_runs),
               "longest": f"{hms(s)}-{hms(e)} UTC ({e - s}s)"}
    return failures, enl


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", help="directory to scan recursively for .igc/.IGC files")
    ap.add_argument("--verbose", action="store_true", help="also list conforming files")
    args = ap.parse_args()

    root = Path(args.directory)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        sys.exit(2)

    igc_files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".igc")
    if not igc_files:
        print(f"No .igc/.IGC files found under {root}")
        sys.exit(0)

    non_conforming = 0
    engine_on = []
    for path in igc_files:
        failures, enl = validate_file(path)
        if enl:
            engine_on.append((path, enl))
        if failures:
            non_conforming += 1
            print(f"FAIL {path.relative_to(root)}")
            for f in failures:
                print(f"     - {f}")
        elif args.verbose:
            print(f"OK   {path.relative_to(root)}")

    if engine_on:
        print()
        print(f"ENL engine-on evidence (ENL > {ENL_ENGINE_ON} sustained "
              f">= {ENL_MIN_RUN_SECONDS}s) in {len(engine_on)} file(s):")
        for path, enl in engine_on:
            print(f"ENL  {path.relative_to(root)}: max ENL {enl['max']}, "
                  f"{enl['n_runs']} run(s), longest {enl['longest']}, "
                  f"{enl['high']}/{enl['fixes']} fixes > {ENL_ENGINE_ON}")

    print()
    print(f"Scanned {len(igc_files)} IGC file(s) under {root}: "
          f"{len(igc_files) - non_conforming} conform, {non_conforming} do not.")
    sys.exit(1 if non_conforming else 0)


if __name__ == "__main__":
    main()
