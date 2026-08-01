import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from igc_model import parse_lines

BASE = [
    "ANAV240406",
    "HFDTEDATE:130726,01",
    "HFPLTPILOTINCHARGE:Test Pilot",
    "I033638FXA3940SIU4143ENL",
    "B1101355144250N01747333EA0050000550010090500",
    "G0123456789ABCDEF",
]


def test_buckets_records_by_type():
    doc = parse_lines(BASE)
    assert [n for n, _ in doc.by_type["H"]] == [2, 3]
    assert doc.a_record == "ANAV240406"
    assert doc.a_line == 1
    assert doc.first_g == 6


def test_decodes_i_record_extensions():
    doc = parse_lines(BASE)
    assert [(e.tlc, e.start, e.end) for e in doc.i_ext] == [
        ("FXA", 36, 38),
        ("SIU", 39, 40),
        ("ENL", 41, 43),
    ]


def test_decodes_b_fix_with_extensions():
    doc = parse_lines(BASE)
    assert len(doc.fixes) == 1
    fix = doc.fixes[0]
    assert fix.time == 11 * 3600 + 1 * 60 + 35
    assert fix.valid == "A"
    assert fix.palt == 500
    assert fix.galt == 550
    assert fix.ext["ENL"] == "050"
    assert fix.ext["SIU"] == "09"


def test_headers_indexed_by_three_letter_code():
    doc = parse_lines(BASE)
    assert doc.headers["DTE"][0] == 2
    assert doc.headers["PLT"][1].endswith("Test Pilot")
    assert doc.flight_date == "130726"


def test_malformed_b_record_is_recorded_not_decoded():
    doc = parse_lines(["ANAV240406", "BGARBAGE", "G01"])
    assert doc.fixes == []
    assert doc.bad_b == [2]


def test_trailing_blank_lines_ignored_interior_ones_recorded():
    doc = parse_lines(["ANAV240406", "", "G01", "", ""])
    assert doc.empty_lines == [2]
