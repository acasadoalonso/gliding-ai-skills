import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from validate_igc_files import scan, report_json

FIXTURES = HERE / "fixtures"


def _payload(tmp_path, *fixture_names):
    for name in fixture_names:
        (tmp_path / name).write_bytes((FIXTURES / name).read_bytes())
    return json.loads(report_json(tmp_path, scan(tmp_path)))


def test_top_level_shape(tmp_path):
    p = _payload(tmp_path, "valid_baseline.igc", "G_MISSING.igc")
    assert set(p) == {"root", "scanned", "conform", "non_conform",
                      "warning_tally", "files"}
    assert p["scanned"] == 2
    assert p["conform"] == 1
    assert p["non_conform"] == 1


def test_finding_shape(tmp_path):
    p = _payload(tmp_path, "G_MISSING.igc")
    finding = next(f for f in p["files"][0]["findings"]
                   if f["rule"] == "G_MISSING")
    assert set(finding) == {"rule", "severity", "category", "message",
                            "line", "data"}
    assert finding["severity"] == "error"
    assert finding["category"] == "g-record"


def test_warning_only_file_is_conformant(tmp_path):
    p = _payload(tmp_path, "CHAR_NON_ASCII.igc")
    assert p["files"][0]["conform"] is True
    assert p["non_conform"] == 0
    assert p["warning_tally"]["CHAR_NON_ASCII"] == 1


def test_output_is_valid_json_from_the_cli(tmp_path):
    import subprocess
    (tmp_path / "x.igc").write_bytes(
        (FIXTURES / "valid_baseline.igc").read_bytes())
    r = subprocess.run(
        [sys.executable, str(HERE.parent / "validate_igc_files.py"),
         str(tmp_path), "--json"],
        capture_output=True, text=True)
    assert r.returncode == 0
    json.loads(r.stdout)
