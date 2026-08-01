import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from igc_model import parse
from igc_rules import RULES
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
