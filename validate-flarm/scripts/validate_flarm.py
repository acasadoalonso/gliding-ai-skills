#!/usr/bin/env python3
"""validate_flarm.py — validate the FLARM/OGN trackers of every contestant in a
SoaringSpot competition against the Ktrax range analyser.

Walks the SoaringSpot v1 REST API (HMAC-SHA256 auth, per-competition
credentials read from src/SoaringSpot/<comp>/): contest → classes →
contestants, takes each contestant's live_track_id (NEVER the
flight_recorders field), queries Ktrax with the last 6 hexadecimal digits
(https://ktrax.kisstech.ch/plot?device=<last6>), and saves per track-id:

    src/reports/flarm_<comp>/<CN>_<device>.md               range-report data + pilot info
    src/reports/flarm_<comp>/<CN>_<device>-rssi.svg         RSSI plot
    src/reports/flarm_<comp>/<CN>_<device>-distances.svg    distances plot

(<CN> is the contestant's competition number; omitted when the contestant has
none.)

plus a summary at src/reports/<comp>_flarm_validation.md.

Stdlib only (urllib), so it runs under any Python 3 without extra packages.

Usage (from the repo root, /home/angel):
    python3 .claude/skills/validate-flarm/scripts/validate_flarm.py --comp egc2026
"""

import argparse
import base64
import datetime
import hashlib
import hmac
import html
import json
import os
import re
import string
import sys
import urllib.request

API_ROOT = "http://api.soaringspot.com/v1"
KTRAX_ROOT = "https://ktrax.kisstech.ch"


def auth_header(client_id: str, secret: bytes) -> str:
    """Build a fresh HMAC-SHA256 Authorization header (one per request)."""
    created = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    nonce = base64.b64encode(os.urandom(36))
    message = nonce + created.encode("utf-8") + client_id.encode("utf-8")
    digest = hmac.new(secret, msg=message, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()
    return (
        f'{API_ROOT}/hmac/v1 ClientID="{client_id}",Signature="{signature}",'
        f'Nonce="{nonce.decode()}",Created="{created}"'
    )


def get_json(url: str, client_id: str, secret: bytes) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/hal+json",
            "Authorization": auth_header(client_id, secret),
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def embedded(doc: dict, rel: str) -> list:
    for key, value in doc.get("_embedded", {}).items():
        if key.rstrip("/").endswith(rel):
            return value if isinstance(value, list) else [value]
    return []


def href(doc: dict, rel: str) -> str | None:
    for key, value in doc.get("_links", {}).items():
        if key.rstrip("/").endswith(rel):
            return value["href"]
    return None


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "validate-flarm/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def device_from_track_id(track_id: str) -> str | None:
    """Last 6 hexadecimal digits of the live_track_id, e.g.
    'OGNC30A84:FLRD03425' -> 'D03425', 'FLADDD93F' -> 'DDD93F'."""
    tail = track_id.strip()[-6:].upper()
    if len(tail) == 6 and all(c in string.hexdigits for c in tail):
        return tail
    return None


# Matched against the tag-stripped, whitespace-collapsed page text.
FIELD_RE = {
    "callsign": re.compile(r"KTrax range report:\s*(\S+)"),
    "last_measurement": re.compile(r"Last measurement:\s*([0-9][0-9T:Z\-]*)"),
    "versions": re.compile(r"Versions:\s*(Hardware:[^)]*\))"),
}
SVG_RE = re.compile(r'src="(tmp/[^"]+\.svg)"')


def ktrax_report(device: str) -> dict:
    """Fetch the Ktrax plot page for a device and pull out the report fields
    and the server-generated SVG plot paths."""
    page = fetch(f"{KTRAX_ROOT}/plot?device={device}").decode("utf-8", "replace")
    out = {"svgs": SVG_RE.findall(page)}
    text = " ".join(html.unescape(re.sub(r"<[^>]*>", " ", page)).split())
    for name, rx in FIELD_RE.items():
        m = rx.search(text)
        out[name] = m.group(1).strip() if m else ""
    return out


def norm_reg(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Validate contestant FLARM trackers against Ktrax."
    )
    ap.add_argument("--comp", required=True,
                    help="Competition directory name under src/SoaringSpot, e.g. egc2026.")
    ap.add_argument("--credentials-dir", default=None,
                    help="Override credentials directory (default: src/SoaringSpot/<comp>).")
    ap.add_argument("--out-dir", default="src/reports",
                    help="Base report directory (default: src/reports).")
    args = ap.parse_args()

    cred_dir = args.credentials_dir or os.path.join("src", "SoaringSpot", args.comp)
    try:
        client_id = open(os.path.join(cred_dir, "clientid")).read().strip()
        secret = open(os.path.join(cred_dir, "secretkey")).read().strip().encode()
    except OSError as e:
        sys.exit(f"Cannot read credentials in {cred_dir}: {e}")

    contest_id = client_id.split("_")[0]
    if not contest_id.isdigit():
        sys.exit(f"Client ID '{client_id}' has no <contest-id>_ prefix.")
    contest = get_json(f"{API_ROOT}/contests/{contest_id}", client_id, secret)
    print(f"Contest: {contest.get('name', '?')} (id {contest_id})")

    plot_dir = os.path.join(args.out_dir, f"flarm_{args.comp}")
    os.makedirs(plot_dir, exist_ok=True)
    for old in os.listdir(plot_dir):  # drop files from previous runs (names may differ)
        os.remove(os.path.join(plot_dir, old))
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    rows = []            # (class, pilot, cn, reg, track_id, device, callsign, last_meas, status, note)
    seen_devices = {}    # device -> ktrax report (fetch once per device)

    for cls in embedded(contest, "classes"):
        cls_name = cls.get("type") or f"class_{cls['id']}"
        contestants = embedded(get_json(href(cls, "contestants"), client_id, secret),
                               "contestants")
        print(f"\n[{cls_name}] {len(contestants)} contestants")
        for con in contestants:
            pilot = con.get("name", "?")
            cn = con.get("contestant_number", "?")
            reg = con.get("aircraft_registration", "")
            track_id = (con.get("live_track_id") or "").strip()
            if not track_id:
                rows.append((cls_name, pilot, cn, reg, "", "", "", "",
                             "NO TRACK ID", "no live_track_id in SoaringSpot"))
                print(f"  skip  {cn:>4} {pilot} (no live_track_id)")
                continue
            device = device_from_track_id(track_id)
            if not device:
                rows.append((cls_name, pilot, cn, reg, track_id, "", "", "",
                             "BAD TRACK ID", "last 6 characters are not hexadecimal"))
                print(f"  BAD   {cn:>4} {pilot}: '{track_id}'")
                continue

            if device in seen_devices:
                rep = seen_devices[device]
            else:
                try:
                    rep = ktrax_report(device)
                except OSError as e:
                    rows.append((cls_name, pilot, cn, reg, track_id, device, "", "",
                                 "FETCH ERROR", str(e)))
                    print(f"  FAIL  {cn:>4} {pilot}: {e}")
                    continue
                seen_devices[device] = rep

                # Save the plots and the per-device report file (once per device).
                # File names carry the contestant's competition number (CN) so
                # they identify the glider at a glance, e.g. AC_D03425.md.
                safe_cn = re.sub(r"[^A-Za-z0-9-]", "", cn or "")
                stem = f"{safe_cn}_{device}" if safe_cn else device
                rep["md_file"] = f"{stem}.md"
                svg_files = []
                for svg_path in rep["svgs"]:
                    kind = "rssi" if "rssi" in svg_path else "distances"
                    fname = f"{stem}-{kind}.svg"
                    try:
                        data = fetch(f"{KTRAX_ROOT}/{svg_path}")
                        with open(os.path.join(plot_dir, fname), "wb") as f:
                            f.write(data)
                        svg_files.append(fname)
                    except OSError as e:
                        print(f"  warn  {device}: could not save {svg_path}: {e}")
                rep["svg_files"] = svg_files
                with open(os.path.join(plot_dir, rep["md_file"]), "w",
                          encoding="utf-8") as f:
                    f.write(f"# Ktrax range report — device {device}\n\n")
                    f.write(f"- **Pilot:** {pilot} ({cls_name}, CN {cn})\n")
                    f.write(f"- **Aircraft registration:** {reg}\n")
                    f.write(f"- **live_track_id:** `{track_id}`\n")
                    f.write(f"- **Ktrax callsign/ID:** {rep['callsign']}\n")
                    f.write(f"- **Last measurement:** {rep['last_measurement'] or '(none)'}\n")
                    f.write(f"- **Versions:** {rep['versions'] or '(none)'}\n")
                    f.write(f"- **Source:** {KTRAX_ROOT}/plot?device={device} (fetched {now})\n\n")
                    for fname in svg_files:
                        f.write(f"![{fname}]({fname})\n\n")

            status = "OK" if rep["last_measurement"] else "NO DATA"
            note = ""
            callsign = rep["callsign"].split("/")[0].strip()
            if status == "OK" and callsign and norm_reg(reg) and \
                    norm_reg(callsign) not in norm_reg(reg) and \
                    norm_reg(reg) not in norm_reg(callsign):
                note = f"Ktrax callsign '{callsign}' differs from registration '{reg}'"
            rows.append((cls_name, pilot, cn, reg, track_id, device,
                         rep["callsign"], rep["last_measurement"], status, note))
            print(f"  {status:<8}{cn:>4} {pilot} -> {device} ({rep['callsign']})"
                  + (f"  [{note}]" if note else ""))

    # Summary report.
    counts = {}
    for r in rows:
        counts[r[8]] = counts.get(r[8], 0) + 1
    summary_path = os.path.join(args.out_dir, f"{args.comp}_flarm_validation.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# FLARM tracker validation — {contest.get('name', args.comp)}\n\n")
        f.write(f"Generated {now} from SoaringSpot contest {contest_id} "
                f"and the Ktrax range analyser.\n\n")
        f.write("## 1. Summary\n\n| Status | Count |\n| :--- | ---: |\n")
        for status in ("OK", "NO DATA", "NO TRACK ID", "BAD TRACK ID", "FETCH ERROR"):
            if status in counts:
                f.write(f"| {status} | {counts[status]} |\n")
        f.write(f"| **Total** | **{len(rows)}** |\n")
        f.write("\n## 2. Contestants\n\n")
        f.write("| Class | CN | Pilot | Registration | Device | Ktrax callsign | "
                "Last measurement | Status | Note |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for cls_name, pilot, cn, reg, track_id, device, callsign, last, status, note in rows:
            # Link to the saved report; a shared device is saved once, under the
            # first contestant's CN, and FETCH ERROR devices have no file at all.
            if device and device in seen_devices:
                dev = f"[{device}](flarm_{args.comp}/{seen_devices[device]['md_file']})"
            else:
                dev = device
            f.write(f"| {cls_name} | {cn} | {pilot} | {reg} | {dev} | "
                    f"{callsign} | {last} | {status} | {note} |\n")

    print(f"\nStatus counts: {counts}")
    print(f"Summary: {os.path.abspath(summary_path)}")
    print(f"Per-device reports and plots: {os.path.abspath(plot_dir)}")


if __name__ == "__main__":
    main()
