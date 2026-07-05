"""Generate a SeeYou Competition (.cucx) file for an SGP competition.

Usage:
    python3 tools/make_cucx.py --comp-id 93 [--day ALL|N] [--out norway_sgp_2026.cucx]

--day picks which task goes into the .cup Related Tasks section: ALL (default)
emits every scored day; an integer emits just that day (1-based, matching the
"Day N" shown in the results). The contest.db always keeps every day.

Data is pulled through src/SGP/sgp_api.py (no MCP runtime required).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from tools import cucx_bundle, cucx_package


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()


def generate(comp_id: int, out_path: str = None, fetchers=None, day=None) -> str:
    bundle = cucx_bundle.build_bundle(comp_id, fetchers=fetchers)
    if out_path is None:
        out_path = f"{_slug(bundle['comp']['short_name'])}.cucx"
    return cucx_package.assemble_cucx(bundle, out_path, days=day)


def _parse_day(value: str):
    """ALL (or empty) -> None (every day); otherwise a 1-based task number."""
    if value is None or str(value).upper() == "ALL":
        return None
    return int(value)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate a SeeYou .cucx from an SGP competition.")
    ap.add_argument("--comp-id", type=int, required=True)
    ap.add_argument("--day", default="ALL",
                    help="task day to put in the .cup: ALL (default) or a 1-based number")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    path = generate(args.comp_id, args.out, day=_parse_day(args.day))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
