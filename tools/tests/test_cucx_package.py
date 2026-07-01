from tools import cucx_package as pkg
from tools import cucx_bundle as b
from tools.tests.test_cucx_bundle import FakeFetchers


def _bundle():
    return b.build_bundle(93, fetchers=FakeFetchers())


def test_cup_header_and_turnpoints():
    text = pkg.build_cup(_bundle())
    lines = text.splitlines()
    assert lines[0].startswith("name,code,country,lat,lon,elev,style")
    assert any("Starmoen" in ln for ln in lines)
    assert "-----Related Tasks-----" in text


def test_cup_dedupes_shared_turnpoints():
    text = pkg.build_cup(_bundle())
    names = [ln.split(",")[0].strip('"') for ln in text.splitlines()
             if ln and not ln.startswith("name,") and not ln.startswith("---")]
    assert len(names) == len(set(names))
