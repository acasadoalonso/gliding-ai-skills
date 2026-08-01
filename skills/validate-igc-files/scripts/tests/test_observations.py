import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from igc_model import parse_lines
from igc_observations import enl_engine_on, gps_anomaly
from build_fixtures import BASE_LINES, b, START


def _with_fixes(fix_lines):
    head = [l for l in BASE_LINES if not l.startswith("B")]
    return parse_lines(head[:15] + fix_lines + head[15:])


def test_enl_none_when_quiet():
    doc = _with_fixes([b(START + i, enl="050") for i in range(40)])
    assert enl_engine_on(doc) is None


def test_enl_ignores_short_spike():
    fixes = [b(START + i, enl="999" if i < 10 else "050") for i in range(60)]
    assert enl_engine_on(_with_fixes(fixes)) is None


def test_enl_reports_sustained_run():
    fixes = [b(START + i, enl="999" if i < 40 else "050") for i in range(60)]
    obs = enl_engine_on(_with_fixes(fixes))
    assert obs is not None
    assert obs["max"] == 999
    assert obs["n_runs"] == 1
    assert "39s" in obs["longest"]


def test_gps_anomaly_none_for_normal_flight():
    doc = _with_fixes([b(START + i) for i in range(40)])
    assert gps_anomaly(doc) is None


def test_gps_anomaly_flags_impossible_jump():
    lines = [b(START), b(START + 1).replace("5144250N", "5344250N")]
    obs = gps_anomaly(_with_fixes(lines))
    assert obs is not None
    assert obs["events"] == 1
    assert obs["cluster"] is False
    assert obs["max_knots"] > 300


def test_gps_anomaly_marks_cluster():
    lines = []
    for i in range(12):
        lat = "5144250N" if i % 2 == 0 else "5344250N"
        lines.append(b(START + i).replace("5144250N", lat))
    obs = gps_anomaly(_with_fixes(lines))
    assert obs["cluster"] is True
    assert obs["events"] >= 5
