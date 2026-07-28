#!/usr/bin/env python3
"""
download_igc.py — fetch an IGC flight file from the SoaringSpot v1 REST API.

The SoaringSpot flight endpoint (…/v1/flights/{id}) returns the raw IGC file
content (Content-Type: application/vnd.flight+igc) behind HMAC-SHA256 auth.
This helper builds that auth header — identically to server.py — and writes the
file to disk. Stdlib only (urllib), so it runs under any Python 3 without extra
packages.

Credentials are per-competition and live in:
    SoaringSpot/<comp>/clientid
    SoaringSpot/<comp>/secretkey

Usage:
    python3 download_igc.py --comp wgc2026 \
        --url http://api.soaringspot.com/v1/flights/10541334728 \
        --filename 65T_FL.igc

    # or give just the flight id instead of the full url:
    python3 download_igc.py --comp wgc2026 --flight-id 10541334728 \
        --filename 65T_FL.igc
"""

import argparse
import base64
import datetime
import hashlib
import hmac
import os
import sys
import urllib.request

API_ROOT = "http://api.soaringspot.com/v1"


def _repo_root() -> str:
    """Repository root = two levels up from .claude/skills/download-igc/."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _resolve_comp(comp: str | None, root: str) -> str:
    ss_dir = os.path.join(root, "SoaringSpot")
    if comp:
        return comp
    # Auto-detect when exactly one competition has credentials.
    if os.path.isdir(ss_dir):
        subs = [
            d for d in sorted(os.listdir(ss_dir))
            if os.path.isfile(os.path.join(ss_dir, d, "clientid"))
        ]
        if len(subs) == 1:
            return subs[0]
        if not subs:
            sys.exit(f"No competition credentials found under {ss_dir}")
        sys.exit(
            "Multiple competitions have credentials "
            f"({', '.join(subs)}). Pass --comp to choose one."
        )
    sys.exit(f"SoaringSpot credentials directory not found: {ss_dir}")


def _load_credentials(comp: str, root: str, client_id: str, secretkey: str) -> tuple[str, bytes]:
    base = os.path.join(root, "SoaringSpot", comp)
    secret = b""
    if not client_id or not secretkey:
       try:
           client_id = open(os.path.join(base, "clientid")).read().strip()
           secret = open(os.path.join(base, "secretkey")).read().strip().encode("utf-8")
       except FileNotFoundError as e:
           sys.exit(f"Missing credential file for comp '{comp}': {e.filename}")
    if not client_id or not secretkey:
        sys.exit(f"Empty credentials for comp '{comp}'")
    return client_id, secretkey.encode("utf-8") if isinstance(secretkey, str) else secretkey


def _auth_header(client_id: str, secret: bytes) -> str:
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


def _basename(name: str) -> str:
    """IGC filenames from the API may carry a Windows path, e.g. '65T\\65T_FL.igc'."""
    return name.replace("\\", "/").rstrip("/").split("/")[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Download an IGC file from SoaringSpot.")
    ap.add_argument("--comp", help="Competition name (SoaringSpot/<comp>). Auto-detected if only one exists.")
    ap.add_argument("--clientid", help="ClientID")
    ap.add_argument("--secretkey", help="Secretkey")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Full flight download URL (…/v1/flights/{id}).")
    src.add_argument("--flight-id", help="Flight id; expands to the standard flights URL.")
    ap.add_argument("--filename", required=True, help="IGC filename (the 'igc_file' field from task results).")
    ap.add_argument("--out-dir", default="IGCfiles", help="Output directory (default: IGCfiles).")
    args = ap.parse_args()

    root = _repo_root()
    comp = _resolve_comp(args.comp, root)
    client_id, secret = _load_credentials(comp, root, args.clientid, args.secretkey)

    url = args.url or f"{API_ROOT}/flights/{args.flight_id}"
    fname = _basename(args.filename)

    out_dir = args.out_dir
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(root, out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, fname)

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/hal+json",
            "Authorization": _auth_header(client_id, secret),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} fetching {url}: {e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error fetching {url}: {e.reason}")

    # Guard against accidentally saving an auth-error JSON body as an .igc.
    head = data[:64].lstrip()
    if head.startswith(b"{") or head.startswith(b"<"):
        sys.exit(
            f"Endpoint returned {ctype or 'non-IGC'} content "
            f"({len(data)} bytes) — not an IGC file. First bytes: {head[:80]!r}"
        )

    with open(out_path, "wb") as f:
        f.write(data)

    print(f"Saved {len(data):,} bytes -> {out_path}  (comp={comp}, type={ctype})")


if __name__ == "__main__":
    main()
