import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "validate_igc_files.py"
FIXTURES = HERE / "fixtures"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True)


def test_clean_directory_exits_zero(tmp_path):
    (tmp_path / "ok.igc").write_bytes(
        (FIXTURES / "valid_baseline.igc").read_bytes())
    r = run(str(tmp_path))
    assert r.returncode == 0
    assert "1 conform, 0 do not" in r.stdout


def test_error_file_exits_one_and_names_the_rule(tmp_path):
    (tmp_path / "bad.igc").write_bytes((FIXTURES / "G_MISSING.igc").read_bytes())
    r = run(str(tmp_path))
    assert r.returncode == 1
    assert "FAIL bad.igc" in r.stdout
    assert "no G (security) record" in r.stdout


def test_warning_only_file_still_conforms(tmp_path):
    (tmp_path / "warn.igc").write_bytes(
        (FIXTURES / "CHAR_NON_ASCII.igc").read_bytes())
    r = run(str(tmp_path))
    assert r.returncode == 0
    assert "1 conform, 0 do not" in r.stdout
    assert "WARNINGS" in r.stdout
    assert "non-ASCII" in r.stdout


def test_warnings_flag_shows_per_file_detail(tmp_path):
    (tmp_path / "warn.igc").write_bytes(
        (FIXTURES / "CHAR_NON_ASCII.igc").read_bytes())
    plain = run(str(tmp_path)).stdout
    detailed = run(str(tmp_path), "--warnings").stdout
    assert "WARN warn.igc" not in plain
    assert "WARN warn.igc" in detailed


def test_missing_directory_exits_two():
    assert run("/nonexistent/path/xyz").returncode == 2


def test_empty_directory_reports_nothing_found(tmp_path):
    r = run(str(tmp_path))
    assert r.returncode == 0
    assert "No .igc" in r.stdout
