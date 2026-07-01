import zipfile
from pathlib import Path
from tools.cucx_hash import content_hash

PAVULLO = Path("/home/angel/pavullo.cucx")


def test_reproduces_pavullo_cup_hash():
    with zipfile.ZipFile(PAVULLO) as z:
        data = z.read("waypoint/29958.cup")
    assert len(data) == 10288
    assert content_hash(data) == "P1jXnrgSI8a2FCf6xulfNifauGG98z3JGadjkkvSDFk"


def test_no_base64_padding():
    assert not content_hash(b"anything").endswith("=")
