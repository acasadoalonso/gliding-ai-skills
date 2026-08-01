#!/usr/bin/env python3
"""Scan a directory recursively for .igc/.IGC files and validate each against
the FAI/IGC flight-log format.

References:
  /home/angel/src/formulas/IGCformat.md
  /home/angel/src/formulas/IGC_Validation_Rules.md

Findings come in two tiers. ERROR means the file's integrity or scoring validity
is in question and sets exit code 1. WARNING is a spec deviation worth knowing
about that does not invalidate the file; warnings are collapsed into a tally by
default and expanded per file with --warnings.

Separately, two observations are reported that are never conformance failures:
sustained ENL (engine noise) and implausible groundspeed suggesting GPS
jamming or spoofing.

Usage:
    python3 validate_igc_files.py <directory> [--warnings] [--verbose] [--json]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from igc_model import parse
from igc_rules import run_all, ERROR, WARNING
from igc_observations import (
    enl_engine_on, gps_anomaly, ENL_ENGINE_ON, ENL_MIN_RUN_SECONDS,
    SPOOF_MAX_KNOTS,
)


def scan(root):
    """Validate every IGC file under root. Returns one dict per file."""
    files = sorted(p for p in root.rglob("*")
                   if p.is_file() and p.suffix.lower() == ".igc")
    results = []
    for path in files:
        doc = parse(path)
        findings = run_all(doc)
        results.append({
            "path": str(path.relative_to(root)),
            "findings": findings,
            "enl": enl_engine_on(doc),
            "gps": gps_anomaly(doc),
            "conform": not any(f.severity == ERROR for f in findings),
        })
    return results


def _by_severity(findings, severity):
    return [f for f in findings if f.severity == severity]


_HEADLINE_CUTS = (" (first at line", ", first", " (line", " ending at line",
                  ", longest", " at line")


def _headline(message):
    """Strip the per-file specifics so the tally reads as one line per rule."""
    for cut in _HEADLINE_CUTS:
        message = message.split(cut)[0]
    return message


def _run_seconds(longest):
    """Pull the duration out of a '10:00:00-10:05:00 UTC (300s)' string."""
    try:
        return int(longest.rsplit("(", 1)[1].rstrip("s)"))
    except (IndexError, ValueError):
        return 0


def report_text(root, results, show_warnings=False, verbose=False):
    out = []

    for r in results:
        errors = _by_severity(r["findings"], ERROR)
        warnings = _by_severity(r["findings"], WARNING)
        if errors:
            out.append(f"FAIL {r['path']}")
            out.extend(f"     - {f.message}" for f in errors)
        elif verbose:
            out.append(f"OK   {r['path']}")
        if show_warnings and warnings:
            out.append(f"WARN {r['path']}")
            out.extend(f"     - {f.message}" for f in warnings)

    if not show_warnings:
        tally = {}
        affected = 0
        for r in results:
            warnings = _by_severity(r["findings"], WARNING)
            if warnings:
                affected += 1
            for f in warnings:
                tally[f.rule_id] = tally.get(f.rule_id, 0) + 1
        if tally:
            out.append("")
            out.append(f"WARNINGS (do not affect conformance) — "
                       f"{affected} file(s) affected")
            first_message = {}
            for r in results:
                for f in _by_severity(r["findings"], WARNING):
                    first_message.setdefault(f.rule_id, f.message)
            for rule_id, count in sorted(tally.items(), key=lambda kv: -kv[1]):
                out.append(f"  {count:5d}  {_headline(first_message[rule_id])}")
            out.append("         (run with --warnings for per-file detail)")

    enl = [r for r in results if r["enl"]]
    if enl:
        enl.sort(key=lambda r: -_run_seconds(r["enl"]["longest"]))
        out.append("")
        out.append(f"ENL engine-on evidence (ENL > {ENL_ENGINE_ON} sustained "
                   f">= {ENL_MIN_RUN_SECONDS}s) in {len(enl)} file(s):")
        for r in enl:
            e = r["enl"]
            out.append(f"ENL  {r['path']}: max ENL {e['max']}, "
                       f"{e['n_runs']} run(s), longest {e['longest']}, "
                       f"{e['high']}/{e['fixes']} fixes > {ENL_ENGINE_ON}")

    gps = [r for r in results if r["gps"]]
    if gps:
        gps.sort(key=lambda r: (not r["gps"]["cluster"], -r["gps"]["events"]))
        out.append("")
        out.append(f"GPS anomaly (groundspeed > {SPOOF_MAX_KNOTS} kt) in "
                   f"{len(gps)} file(s):")
        for r in gps:
            g = r["gps"]
            flag = ("CLUSTER, possible jamming/spoofing — other findings in "
                    "this file may be compromised" if g["cluster"]
                    else "isolated, consistent with recorder clock tolerance")
            out.append(f"GPS  {r['path']}: {g['events']} event(s) — {flag}; "
                       f"max {g['max_knots']} kt at {g['first']} UTC")

    bad = sum(1 for r in results if not r["conform"])
    out.append("")
    out.append(f"Scanned {len(results)} IGC file(s) under {root}: "
               f"{len(results) - bad} conform, {bad} do not.")
    return "\n".join(out)


def report_json(root, results):
    tally = {}
    for r in results:
        for f in _by_severity(r["findings"], WARNING):
            tally[f.rule_id] = tally.get(f.rule_id, 0) + 1
    bad = sum(1 for r in results if not r["conform"])
    return json.dumps({
        "root": str(root),
        "scanned": len(results),
        "conform": len(results) - bad,
        "non_conform": bad,
        "warning_tally": tally,
        "files": [
            {
                "path": r["path"],
                "conform": r["conform"],
                "findings": [
                    {
                        "rule": f.rule_id,
                        "severity": f.severity,
                        "category": f.category,
                        "message": f.message,
                        "line": f.line,
                        "data": f.data,
                    }
                    for f in r["findings"]
                ],
                "enl": r["enl"],
                "gps_anomaly": r["gps"],
            }
            for r in results
        ],
    }, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Validate IGC flight logs in a directory tree.")
    ap.add_argument("directory",
                    help="directory to scan recursively for .igc/.IGC files")
    ap.add_argument("--warnings", action="store_true",
                    help="expand warnings per file instead of tallying them")
    ap.add_argument("--verbose", action="store_true",
                    help="also list conforming files")
    ap.add_argument("--json", action="store_true",
                    help="emit structured findings instead of the text report")
    args = ap.parse_args(argv)

    root = Path(args.directory)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    results = scan(root)
    if not results:
        print(f"No .igc/.IGC files found under {root}")
        return 0

    if args.json:
        print(report_json(root, results))
    else:
        print(report_text(root, results, args.warnings, args.verbose))

    return 1 if any(not r["conform"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
