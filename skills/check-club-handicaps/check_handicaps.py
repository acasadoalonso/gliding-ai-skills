#!/usr/bin/env python3
"""Check the handicap assigned to each contestant against an IGC handicap list.

Given a SoaringSpot ``get_class_contestants`` JSON dump and a handicap-list
markdown file from ``formulas/`` (e.g. ``club_class_handicaps.md`` or
``20m_multiseat_handicaps.md``), this:

  1. parses the Appendix handicap table out of the markdown,
  2. matches each contestant's ``aircraft_model`` to a list entry,
  3. compares the assigned ``handicap`` against the list's base handicap, and
  4. writes an RTF report into ``reports/`` and prints a summary to stdout.

The glider-name matcher is best-effort: list rows often group several variants
in one cell (e.g. ``Discus a, b, CS`` or ``ASW 20, F, L``). Anything it cannot
match confidently is flagged ``UNMATCHED`` so a human / the calling agent can
review it. Likewise a handicap that differs from the list base is flagged
``DIFF`` rather than silently treated as an error — under SC3AH the base
handicap can legitimately be adjusted for mass (§1.6.1) and winglets (§1.6.2),
so a difference is a thing to *check*, not necessarily a mistake.

Usage:
    python3 check_handicaps.py \
        --contestants club_contestants.json \
        --handicap-list formulas/club_class_handicaps.md \
        --comp 24-fai-egc --class-name "Club" \
        --out reports/SS.24thFAIEGC_club_handicap_check.rtf \
        --generated 2026-06-07

``--contestants`` accepts either the raw MCP response (with ``_embedded``) or a
plain JSON list of contestant objects. ``--generated`` defaults to the value of
the ``REPORT_DATE`` env var if set (so the agent can pass the real date —
``Date.now`` is intentionally avoided here only by leaving it explicit).
"""
import argparse
import json
import os
import re
import sys

TOL = 0.0005  # handicaps within this are considered equal


# --------------------------------------------------------------------------- #
# Handicap-list parsing
# --------------------------------------------------------------------------- #
def parse_handicap_list(md_path):
    """Return (entries, meta) parsed from the Appendix table of a list .md.

    entries: list of dicts {handicap: float, types: str, flaps: str,
                            mass: str, remarks: str, aliases: set[str]}
    meta:    dict with 'title' and 'source' best-effort from the file header.
    """
    with open(md_path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    meta = {"title": os.path.basename(md_path), "source": ""}
    for ln in lines[:12]:
        if ln.startswith("# "):
            meta["title"] = ln[2:].strip()
        if ln.lower().startswith("**source:**"):
            meta["source"] = re.sub(r"\*\*", "", ln).replace("Source:", "").strip()

    # Collect the markdown table whose header mentions "Glider".
    rows, in_table, header_seen = [], False, False
    for ln in lines:
        s = ln.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not header_seen and any("glider" in c.lower() for c in cells) \
                    and any("handicap" in c.lower() for c in cells):
                header_seen = in_table = True
                continue
            if in_table:
                if set("".join(cells)) <= set("-: "):  # separator row
                    continue
                rows.append(cells)
        elif in_table and header_seen:
            break  # table ended

    entries = []
    for cells in rows:
        if len(cells) < 2:
            continue
        hc_raw = cells[0].replace("\\", "").strip()
        m = re.search(r"\d+(?:\.\d+)?", hc_raw)
        if not m:
            continue
        handicap = float(m.group(0))
        types = cells[1].strip()
        flaps = cells[2].strip() if len(cells) > 2 else ""
        mass = cells[3].strip() if len(cells) > 3 else ""
        remarks = cells[4].strip() if len(cells) > 4 else ""
        entries.append({
            "handicap": handicap,
            "types": types,
            "flaps": flaps,
            "mass": mass,
            "remarks": remarks,
            "aliases": aliases_for(types),
        })
    return entries, meta


def _norm(s):
    """Normalise a glider name for comparison: upper-case alphanumerics only."""
    return re.sub(r"[^A-Za-z0-9]", "", s).upper()


def aliases_for(typestr):
    """Expand a list cell like 'ASW 20, F, L' into a set of normalised keys.

    Over-generates rather than under-generates; spurious aliases rarely collide
    with another glider's real name. Aliases shorter than 3 chars are dropped.
    """
    parts = [p.strip() for p in typestr.split(",") if p.strip()]
    if not parts:
        return set()
    base = parts[0]
    raw = {base}
    pre_letters = re.sub(r"[A-Za-z]+$", "", base).strip()      # 'ASW 20B' -> 'ASW 20'
    pre_space = re.sub(r"\s+[A-Za-z]{1,3}$", "", base).strip()  # 'Discus a' -> 'Discus'
    for p in parts[1:]:
        if re.fullmatch(r"[A-Za-z0-9]{1,4}", p):  # short variant suffix: a, b, CS, 2M, 3M1
            for pre in (pre_letters, pre_space):
                if pre:
                    raw.add(pre + p)
                    raw.add(pre + " " + p)
            raw.add(base + p)
        else:  # looks like a full standalone model name
            raw.add(p)
            if pre_space:
                raw.add(pre_space + " " + p)
    return {a for a in (_norm(x) for x in raw) if len(a) >= 3}


# --------------------------------------------------------------------------- #
# Contestant loading + matching
# --------------------------------------------------------------------------- #
def load_contestants(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    emb = data.get("_embedded", {})
    for key, val in emb.items():
        if "contestant" in key.lower() and isinstance(val, list):
            return val
    if isinstance(data, dict) and "name" in data:
        return [data]
    raise SystemExit(f"Could not find a contestants list in {path}")


def match_entry(model, entries):
    """Return (entry, confidence) where confidence is 'exact'|'partial'|None."""
    key = _norm(model)
    if not key:
        return None, None
    # exact alias match
    for e in entries:
        if key in e["aliases"]:
            return e, "exact"
    # partial: longest alias that is a prefix of the model (or vice-versa)
    best, best_len = None, 0
    for e in entries:
        for a in e["aliases"]:
            if (key.startswith(a) or a.startswith(key)) and len(a) > best_len:
                best, best_len = e, len(a)
    if best is not None and best_len >= 3:
        return best, "partial"
    return None, None


def fmt_h(x):
    if x is None:
        return ""
    return f"{x:.3f}"


def build_rows(contestants, entries):
    out = []
    for c in contestants:
        model = c.get("aircraft_model", "") or ""
        assigned = c.get("handicap", None)
        try:
            assigned = float(assigned) if assigned is not None else None
        except (TypeError, ValueError):
            assigned = None
        entry, conf = match_entry(model, entries)
        list_h = entry["handicap"] if entry else None
        list_type = entry["types"] if entry else ""
        if entry is None:
            status, note = "UNMATCHED", "glider not found in list — verify name/eligibility"
        elif assigned is None or assigned == 0:
            status, note = "NO_HANDICAP", "no handicap assigned in entry"
        elif abs(assigned - list_h) <= TOL:
            status = "OK"
            note = "" if conf == "exact" else "matched on partial name — verify"
        else:
            status = "DIFF"
            delta = assigned - list_h
            note = (f"assigned {fmt_h(assigned)} vs list {fmt_h(list_h)} "
                    f"({delta:+.3f}); "
                    f"check mass/winglet adjustment (SC3AH §1.6)")
            if conf == "partial":
                note += " — partial name match"
        out.append({
            "number": c.get("contestant_number", ""),
            "pilot": c.get("name", ""),
            "team": c.get("team", ""),
            "glider": model,
            "registration": c.get("aircraft_registration", ""),
            "assigned": assigned,
            "list_handicap": list_h,
            "list_type": list_type,
            "confidence": conf,
            "status": status,
            "note": note,
        })
    return out


# --------------------------------------------------------------------------- #
# RTF rendering
# --------------------------------------------------------------------------- #
def rtf_escape(s):
    out = []
    for ch in str(s):
        o = ord(ch)
        if ch in "\\{}":
            out.append("\\" + ch)
        elif o < 128:
            out.append(ch)
        else:
            out.append(f"\\u{o}?")
    return "".join(out)


def _cells(widths):
    return "".join(f"\\cellx{w}" for w in widths)


def render_rtf(rows, meta, args):
    widths = [900, 4200, 2300, 4400, 6100, 7000, 8000, 9300]
    headers = ["#", "Pilot", "Glider", "Registration",
               "Assigned", "List H", "Status", "Note"]

    n = len(rows)
    n_ok = sum(1 for r in rows if r["status"] == "OK")
    n_diff = sum(1 for r in rows if r["status"] == "DIFF")
    n_unm = sum(1 for r in rows if r["status"] == "UNMATCHED")
    n_noh = sum(1 for r in rows if r["status"] == "NO_HANDICAP")

    p = []
    p.append(r"{\rtf1\ansi\ansicpg1252\deff0")
    p.append(r"{\fonttbl{\f0\fswiss Helvetica;}}")
    p.append(r"\paperw16838\paperh11906\margl1134\margr1134\margt1134\margb1134")  # landscape
    p.append(r"\f0\fs20")
    title = f"{args.class_name} Class — Handicap Check"
    p.append(r"\pard\sa160\f0\fs32 \b " + rtf_escape(title) + r"\par")
    if args.comp:
        p.append(r"\pard\sa40\f0\fs22 \b " + rtf_escape(args.comp) + r"\par")
    p.append(r"\pard\sa40\f0\fs18 Handicap list: " + rtf_escape(meta["title"]) + r"\par")
    if meta["source"]:
        p.append(r"\pard\sa40\f0\fs16 Source: " + rtf_escape(meta["source"]) + r"\par")
    p.append(r"\pard\sa200\f0\fs16 Contestant glider data from the soaringspot MCP "
             r"(get_class_contestants). Generated " + rtf_escape(args.generated) + r".\par")

    # Summary
    p.append(r"\pard\sa80\f0\fs24 \b Summary\par")
    summary = (f"{n} contestants checked: {n_ok} OK, {n_diff} differ from list, "
               f"{n_unm} not matched to the list, {n_noh} with no handicap.")
    p.append(r"\pard\sa120\f0\fs18 " + rtf_escape(summary) + r"\par")
    p.append(r"\pard\sa200\f0\fs16 \i OK = assigned handicap equals the list base handicap. "
             r"DIFF = differs from the base handicap; this may be a legitimate mass or "
             r"winglet adjustment (SC3AH \u167?1.6) \u8212? verify against the entry's "
             r"declared takeoff mass before treating it as an error.\i0\par")

    # Full table
    p.append(r"\pard\sa80\f0\fs24 \b All contestants\par")
    p.append(r"\trowd\trgaph80\trleft0" + _cells(widths))
    for h in headers:
        p.append(r"\pard\intbl\f0\fs16 \b " + rtf_escape(h) + r"\cell")
    p.append(r"\row")
    for r in rows:
        p.append(r"\trowd\trgaph80\trleft0" + _cells(widths))
        vals = [r["number"], r["pilot"], r["glider"], r["registration"],
                fmt_h(r["assigned"]), fmt_h(r["list_handicap"]), r["status"], r["note"]]
        for i, v in enumerate(vals):
            bold = r" \b " if (i == 6 and r["status"] != "OK") else " "
            p.append(r"\pard\intbl\f0\fs16" + bold + rtf_escape(v) + r"\cell")
        p.append(r"\row")

    # Differences-only section
    flagged = [r for r in rows if r["status"] != "OK"]
    p.append(r"\pard\sa80\sb160\f0\fs24 \b Differences & items to review\par")
    if not flagged:
        p.append(r"\pard\sa120\f0\fs18 None \u8212? every contestant's assigned handicap "
                 r"matches the list base handicap.\par")
    else:
        for r in flagged:
            line = (f"{r['number']}  {r['pilot']}  —  {r['glider']} "
                    f"({r['registration']}): {r['status']}. {r['note']}")
            p.append(r"\pard\sa80\f0\fs18 \bullet  " + rtf_escape(line) + r"\par")

    p.append("}")
    return "\n".join(p)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--contestants", required=True,
                    help="JSON file: get_class_contestants response or a list")
    ap.add_argument("--handicap-list", default="formulas/club_class_handicaps.md")
    ap.add_argument("--comp", default="", help="competition label for the report header")
    ap.add_argument("--class-name", default="Club")
    ap.add_argument("--out", default="", help="output RTF path (default reports/SS.<comp>_handicap_check.rtf)")
    ap.add_argument("--generated", default=os.environ.get("REPORT_DATE", ""),
                    help="generation date string for the report footer (YYYY-MM-DD)")
    args = ap.parse_args()

    entries, meta = parse_handicap_list(args.handicap_list)
    if not entries:
        sys.exit(f"No handicap entries parsed from {args.handicap_list}")
    contestants = load_contestants(args.contestants)
    rows = build_rows(contestants, entries)

    if not args.out:
        slug = re.sub(r"[^A-Za-z0-9]+", "", args.comp) or "comp"
        args.out = f"reports/SS.{slug}_{args.class_name.lower()}_handicap_check.rtf"
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(render_rtf(rows, meta, args))

    # stdout summary for the calling agent
    print(f"Parsed {len(entries)} handicap-list entries from {args.handicap_list}")
    print(f"Checked {len(rows)} contestants")
    for r in rows:
        if r["status"] != "OK":
            print(f"  [{r['status']}] {r['number']} {r['pilot']} | "
                  f"{r['glider']} | assigned={fmt_h(r['assigned'])} "
                  f"list={fmt_h(r['list_handicap'])} | {r['note']}")
    print(f"Report written to {args.out}")


if __name__ == "__main__":
    main()
