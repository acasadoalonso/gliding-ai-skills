"""Regression against the real 308-file competition corpus.

Skipped when the corpus is absent, so the suite stays portable. Its job is to
catch a rule that starts firing far more or far less often after a refactor -
the failure mode that would quietly ruin the report.

Only the four calibrated contest directories are scanned, not the whole of
IGCfiles/. The tree root also holds a handful of loose one-off downloads that
were never part of the calibration in the spec, and including them would make
every documented hit count approximate instead of exact.
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from validate_igc_files import scan

CORPUS = Path("/home/angel/IGCfiles")
CALIBRATION_DIRS = ("egc2026_2026-07-13", "egc2026_2026-07-10",
                    "WGC2026", "sgp2026")
BASELINE = HERE / "corpus_baseline.json"

pytestmark = pytest.mark.skipif(
    not all((CORPUS / d).is_dir() for d in CALIBRATION_DIRS),
    reason="calibration corpus not present")


def scan_calibration():
    results = []
    for d in CALIBRATION_DIRS:
        results.extend(scan(CORPUS / d))
    return results


@pytest.fixture(scope="module")
def actual():
    results = scan_calibration()
    counts = {}
    for r in results:
        for f in r["findings"]:
            counts[f.rule_id] = counts.get(f.rule_id, 0) + 1
    return {
        "scanned": len(results),
        "conform": sum(1 for r in results if r["conform"]),
        "rule_file_counts": counts,
    }


@pytest.fixture(scope="module")
def expected():
    return json.loads(BASELINE.read_text())


def test_scanned_count_unchanged(actual, expected):
    assert actual["scanned"] == expected["scanned"]


def test_conformance_unchanged(actual, expected):
    assert actual["conform"] == expected["conform"]


def test_no_rule_starts_flooding(actual, expected):
    """A warning firing on more than half the corpus is a calibration failure."""
    half = actual["scanned"] // 2
    grew = {
        rule_id: (expected["rule_file_counts"].get(rule_id, 0), count)
        for rule_id, count in actual["rule_file_counts"].items()
        if count > half and count > expected["rule_file_counts"].get(rule_id, 0)
    }
    assert grew == {}, f"rules now firing on >50% of the corpus: {grew}"


def test_per_rule_counts_match(actual, expected):
    diffs = {
        rule_id: (expected["rule_file_counts"].get(rule_id, 0), count)
        for rule_id, count in actual["rule_file_counts"].items()
        if expected["rule_file_counts"].get(rule_id, 0) != count
    }
    dropped = {
        rule_id: (count, 0)
        for rule_id, count in expected["rule_file_counts"].items()
        if rule_id not in actual["rule_file_counts"]
    }
    assert {**diffs, **dropped} == {}, "per-rule hit counts changed"
