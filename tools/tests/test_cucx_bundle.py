import json
from pathlib import Path
import pytest
from tools import cucx_bundle as b

FIX = Path("/home/angel/tools/tests/fixtures/comp93")


class FakeFetchers:
    """Serves captured comp93 JSON, mimicking sgp_api signatures."""
    def fetch_competition(self, comp_id):
        return json.loads((FIX / "competition.json").read_text())

    def fetch_pilots(self, comp_id):
        return json.loads((FIX / "pilots.json").read_text())

    def fetch_task(self, comp_id, day_id):
        p = FIX / f"task_{day_id}.json"
        if not p.exists():
            raise FileNotFoundError(day_id)
        return json.loads(p.read_text())

    def fetch_day_results(self, comp_id, day_id):
        p = FIX / f"day_{day_id}.json"
        if not p.exists():
            raise FileNotFoundError(day_id)
        return json.loads(p.read_text())

    def fetch_total_results(self, comp_id, day_id):
        return json.loads((FIX / f"total_{day_id}.json").read_text())


def test_bundle_comp_and_pilots():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    assert d["comp"]["name"] == "Norway SGP 2026"
    assert len(d["pilots"]) == 13
    assert {p["comp_number"] for p in d["pilots"]} >= {"3V", "IGC", "EI"}


def test_bundle_skips_empty_future_days():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    # 6 days have real tasks (2 practice + 4 race); 3 future days are empty.
    assert len(d["tasks"]) == 6
    for t in d["tasks"]:
        assert len(t["turnpoints"]) > 0


def test_bundle_tasks_have_turnpoints_in_degrees():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    t = d["tasks"][0]
    assert t["turnpoints"][0]["role"] == "Start"
    assert 55 < t["turnpoints"][0]["lat_deg"] < 65   # Norway
    assert t["distance_m"] > 100000


def test_practice_days_marked_practice():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    statuses = {t["date"]: t["result_status"] for t in d["tasks"]}
    # 2026-06-26 and 2026-06-27 are practice days
    assert statuses["2026-06-26"] == "practice"
    assert statuses["2026-06-27"] == "practice"


def test_bundle_results_joined_with_totals():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    # Race 1 (2026-06-28, official) is the first fully-scored race.
    race1 = next(t for t in d["tasks"] if t["date"] == "2026-06-28")
    assert race1["result_status"] == "official"
    r = race1["results"][0]
    assert r["rank"] == 1
    assert r["points"] is not None
    assert r["points_total"] is not None


def test_ranks_coerced_to_int_or_none():
    d = b.build_bundle(93, fetchers=FakeFetchers())
    for t in d["tasks"]:
        for r in t["results"]:
            assert r["rank"] is None or isinstance(r["rank"], int)


def test_result_status_map():
    assert b.result_status_map("official") == "official"
    assert b.result_status_map("provisional") == "preliminary"
    assert b.result_status_map("unofficial") == "preliminary"
