#!/usr/bin/env python3
"""download_all_igc.py — download every IGC file for all classes of a
SoaringSpot competition day.

Walks the SoaringSpot v1 REST API (HMAC-SHA256 auth, credentials are
per-competition): contests → classes → task matching the date → task results,
then downloads each flight's IGC file. Files are saved per class:

    IGCfiles/<comp>_<date>/<class>/<name>.igc

Stdlib only (urllib), so it runs under any Python 3 without extra packages.

Usage:
    python3 tools/download_all_igc.py \
        --comp egc2026 \
        --clientid <clientid> --secret <secretkey> \
        --date 2026-07-10
"""

import argparse
import base64
import datetime
import hashlib
import hmac
import json
import os
import sys
import urllib.request

API_ROOT = "http://api.soaringspot.com/v1"


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


def api_get(url: str, client_id: str, secret: bytes) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/hal+json",
            "Authorization": auth_header(client_id, secret),
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def get_json(url: str, client_id: str, secret: bytes) -> dict:
    data, _ = api_get(url, client_id, secret)
    return json.loads(data)


def embedded(doc: dict, rel: str) -> list:
    """Return the embedded list for a rel (…/rel/<rel>), tolerating key variants."""
    for key, value in doc.get("_embedded", {}).items():
        if key.rstrip("/").endswith(rel):
            return value if isinstance(value, list) else [value]
    return []


def href(doc: dict, rel: str) -> str | None:
    for key, value in doc.get("_links", {}).items():
        if key.rstrip("/").endswith(rel):
            return value["href"]
    return None


def basename(name: str) -> str:
    """IGC filenames from the API may carry a Windows path, e.g. '67A\\67A_FL.igc'."""
    return name.replace("\\", "/").rstrip("/").split("/")[-1]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Download all IGC files for every class of a competition day."
    )
    ap.add_argument("--comp", required=True, help="Competition name, e.g. egc2026 (used to name the output directory).")
    ap.add_argument("--clientid", required=True, help="SoaringSpot API client ID for the competition.")
    ap.add_argument("--secret", required=True, help="SoaringSpot API secret key for the competition.")
    ap.add_argument("--date", required=True, help="Competition day, YYYY-MM-DD.")
    ap.add_argument("--out-dir", default="IGCfiles", help="Base output directory (default: IGCfiles).")
    args = ap.parse_args()

    try:
        datetime.date.fromisoformat(args.date)
    except ValueError:
        sys.exit(f"Invalid date '{args.date}' — expected YYYY-MM-DD.")

    client_id, secret = args.clientid, args.secret.encode("utf-8")

    # Per-competition client IDs are prefixed with the contest ID (e.g. 5337_…),
    # which is the only reliable way to find "our" contest — the plain
    # /contests listing returns other public contests too.
    contest_id = client_id.split("_")[0]
    if not contest_id.isdigit():
        sys.exit(f"Client ID '{client_id}' has no <contest-id>_ prefix — "
                 "cannot determine the contest.")
    contest = get_json(f"{API_ROOT}/contests/{contest_id}", client_id, secret)
    print(f"Contest: {contest.get('name', '?')} (id {contest.get('id', '?')})")

    classes = embedded(contest, "classes")
    if not classes:
        sys.exit("Contest has no classes.")

    base_dir = os.path.join(args.out_dir, f"{args.comp}_{args.date}")
    total_saved = total_skipped = total_failed = 0
    summary = []

    for cls in classes:
        cls_name = cls.get("type") or f"class_{cls['id']}"
        tasks = embedded(get_json(href(cls, "tasks"), client_id, secret), "tasks")
        day_tasks = [t for t in tasks if t.get("task_date") == args.date]
        # Prefer a scored day over practice when both exist on the same date.
        scored = [t for t in day_tasks if t.get("result_status") != "practice"]
        task = (scored or day_tasks or [None])[0]
        if task is None:
            summary.append((cls_name, "no task", 0, 0, 0))
            print(f"\n[{cls_name}] no task on {args.date}")
            continue

        task_id = href(task, "self").rstrip("/").split("/")[-1]
        status = task.get("result_status", "?")
        print(f"\n[{cls_name}] task {task_id} ({status})")

        results = embedded(get_json(href(task, "results"), client_id, secret), "results")
        out_dir = os.path.join(base_dir, cls_name)
        saved = skipped = failed = 0

        for res in results:
            contestant = embedded(res, "contestant")
            who = contestant[0].get("name", "?") if contestant else "?"
            igc_file = res.get("igc_file")
            flight_url = href(res, "flight")
            if not igc_file or not flight_url:
                skipped += 1
                print(f"  skip  {who} (no IGC file)")
                continue
            fname = basename(igc_file)
            try:
                data, ctype = api_get(flight_url, client_id, secret)
            except (urllib.error.URLError, OSError) as e:
                failed += 1
                print(f"  FAIL  {fname} ({who}): {e}")
                continue
            # Guard against saving an auth-error JSON/HTML body as an .igc.
            head = data[:64].lstrip()
            if head.startswith(b"{") or head.startswith(b"<"):
                failed += 1
                print(f"  FAIL  {fname} ({who}): non-IGC response ({ctype})")
                continue
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, fname), "wb") as f:
                f.write(data)
            saved += 1
            print(f"  saved {fname} ({len(data):,} bytes)")

        summary.append((cls_name, task_id, saved, skipped, failed))
        total_saved += saved
        total_skipped += skipped
        total_failed += failed

    print(f"\n{'class':<20} {'task':<12} {'saved':>6} {'skipped':>8} {'failed':>7}")
    for cls_name, task_id, saved, skipped, failed in summary:
        print(f"{cls_name:<20} {task_id:<12} {saved:>6} {skipped:>8} {failed:>7}")
    print(f"\nTotal: {total_saved} saved, {total_skipped} skipped, "
          f"{total_failed} failed -> {os.path.abspath(base_dir)}")
    if total_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
