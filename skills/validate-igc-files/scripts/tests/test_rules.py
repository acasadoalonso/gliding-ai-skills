import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from igc_model import parse, parse_lines
from igc_rules import RULES, r_time_out_of_sequence
import build_fixtures

FIXTURES = HERE / "fixtures"


def _ids(rule):
    return rule.id


@pytest.fixture(scope="session", autouse=True)
def generated_fixtures():
    build_fixtures.main()


@pytest.mark.parametrize("rule", RULES, ids=_ids)
def test_rule_fires_on_its_own_fixture(rule):
    doc = parse(FIXTURES / f"{rule.id}.igc")
    findings = rule.fn(doc)
    assert [f.rule_id for f in findings] == [rule.id], (
        f"{rule.id} did not fire on its fixture"
    )


@pytest.mark.parametrize("rule", RULES, ids=_ids)
def test_rule_silent_on_clean_baseline(rule):
    doc = parse(FIXTURES / "valid_baseline.igc")
    assert rule.fn(doc) == [], f"{rule.id} fired on the conformant baseline"


def test_every_rule_has_a_fixture():
    missing = [r.id for r in RULES if r.id not in build_fixtures.MUTATIONS]
    assert missing == [], f"rules without a fixture: {missing}"


def test_rule_ids_are_unique():
    ids = [r.id for r in RULES]
    assert len(ids) == len(set(ids))


def test_severities_are_valid():
    assert {r.severity for r in RULES} <= {"error", "warning"}


def _sequence_findings(lines):
    return r_time_out_of_sequence(parse_lines(lines))


def _f_stamped(seconds):
    hh, mm, ss = seconds // 3600, seconds % 3600 // 60, seconds % 60
    return f"F{hh:02d}{mm:02d}{ss:02d}010203040506"


def test_time_sequence_catches_backward_f_record():
    """A misplaced F record leaves every B record in order (see AL10)."""
    start = build_fixtures.START
    lines = build_fixtures.replace(
        list(build_fixtures.BASE_LINES),
        lambda l: l.startswith("F"), _f_stamped(start + 300))
    findings = _sequence_findings(lines)
    assert [f.rule_id for f in findings] == ["TIME_OUT_OF_SEQUENCE"]
    assert findings[0].data["count"] == 1


def test_time_sequence_catches_backward_k_record():
    start = build_fixtures.START
    lines = build_fixtures.replace(
        list(build_fixtures.BASE_LINES),
        lambda l: l.startswith("K"), build_fixtures.k(start - 60))
    assert [f.rule_id for f in _sequence_findings(lines)] == ["TIME_OUT_OF_SEQUENCE"]


def test_time_sequence_allows_equal_timestamps_across_types():
    """An F or E record sharing its second with the next fix is normal."""
    start = build_fixtures.START
    lines = build_fixtures.replace(
        list(build_fixtures.BASE_LINES),
        lambda l: l.startswith("F"), _f_stamped(start))
    assert _sequence_findings(lines) == []
