"""Parse an IGC flight log into a decoded document model.

Pure parsing: this module makes no judgements about conformance. Every rule in
igc_rules.py reads the IGCDoc produced here, so a file is read and decoded
exactly once no matter how many rules run.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

B_RECORD_RE = re.compile(
    r"^B(\d{2})(\d{2})(\d{2})"
    r"(\d{7})([NS])"
    r"(\d{8})([EW])"
    r"([AV])"
    r"(-\d{4}|\d{5})"
    r"(-\d{4}|\d{5})"
)


@dataclass(frozen=True)
class Ext:
    """One extension declared in an I, J or M record."""
    tlc: str
    start: int   # 1-based, inclusive
    end: int     # 1-based, inclusive


@dataclass
class Fix:
    line: int
    time: int            # seconds since midnight UTC
    lat: float           # signed degrees
    lon: float           # signed degrees
    valid: str           # 'A' or 'V'
    palt: int
    galt: int
    ext: dict            # TLC -> raw substring
    raw: str


@dataclass
class IGCDoc:
    path: object = None
    lines: list = field(default_factory=list)
    by_type: dict = field(default_factory=dict)
    a_record: str = None
    a_line: int = None
    headers: dict = field(default_factory=dict)
    i_records: list = field(default_factory=list)
    j_records: list = field(default_factory=list)
    m_records: list = field(default_factory=list)
    i_ext: list = field(default_factory=list)
    j_ext: list = field(default_factory=list)
    m_ext: list = field(default_factory=list)
    fixes: list = field(default_factory=list)
    bad_b: list = field(default_factory=list)
    first_g: int = None
    flight_date: str = None
    empty_lines: list = field(default_factory=list)

    def numbered(self):
        """Yield (1-based line number, text) for every line."""
        return enumerate(self.lines, start=1)

    def of_type(self, letter):
        return self.by_type.get(letter, [])


def _decode_ext(text):
    """Decode the extension list shared by I, J and M records.

    Layout is <letter><NN count> then NN groups of SSEETTT: start column, end
    column, three-letter code. Groups that are truncated or non-numeric are
    skipped here; the corresponding rules report them.
    """
    out = []
    m = re.match(r"^[IJM](\d{2})", text)
    if not m:
        return out
    for k in range(int(m.group(1))):
        g = text[3 + k * 7: 10 + k * 7]
        if len(g) == 7 and g[:4].isdigit():
            out.append(Ext(g[4:], int(g[:2]), int(g[2:4])))
    return out


def _dm_to_deg(raw, hemi, deg_digits):
    """Convert DDMMmmm / DDDMMmmm plus hemisphere to signed degrees."""
    deg = int(raw[:deg_digits])
    minutes = int(raw[deg_digits:]) / 1000.0
    value = deg + minutes / 60.0
    return -value if hemi in ("S", "W") else value


def parse_lines(raw_lines, path=None):
    lines = [l.rstrip("\r\n") for l in raw_lines]
    while lines and lines[-1] == "":
        lines.pop()

    doc = IGCDoc(path=path, lines=lines)

    for n, line in doc.numbered():
        if line == "":
            doc.empty_lines.append(n)
            continue
        letter = line[0]
        doc.by_type.setdefault(letter, []).append((n, line))

        if letter == "A" and doc.a_record is None:
            doc.a_record, doc.a_line = line, n
        elif letter == "H":
            if len(line) >= 5:
                doc.headers.setdefault(line[2:5], (n, line))
        elif letter == "I":
            doc.i_records.append((n, line))
        elif letter == "J":
            doc.j_records.append((n, line))
        elif letter == "M":
            doc.m_records.append((n, line))
        elif letter == "G" and doc.first_g is None:
            doc.first_g = n

    if doc.i_records:
        doc.i_ext = _decode_ext(doc.i_records[0][1])
    if doc.j_records:
        doc.j_ext = _decode_ext(doc.j_records[0][1])
    if doc.m_records:
        doc.m_ext = _decode_ext(doc.m_records[0][1])

    dte = doc.headers.get("DTE")
    if dte:
        tail = dte[1].split("DATE:", 1)[-1] if "DATE:" in dte[1] else dte[1][5:]
        m = re.search(r"(\d{6})", tail)
        if m:
            doc.flight_date = m.group(1)

    for n, line in doc.of_type("B"):
        m = B_RECORD_RE.match(line)
        if not m:
            doc.bad_b.append(n)
            continue
        hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if hh > 23 or mm > 59 or ss > 59:
            doc.bad_b.append(n)
            continue
        ext = {}
        for e in doc.i_ext:
            ext[e.tlc] = line[e.start - 1:e.end]
        doc.fixes.append(Fix(
            line=n,
            time=hh * 3600 + mm * 60 + ss,
            lat=_dm_to_deg(m.group(4), m.group(5), 2),
            lon=_dm_to_deg(m.group(6), m.group(7), 3),
            valid=m.group(8),
            palt=int(m.group(9)),
            galt=int(m.group(10)),
            ext=ext,
            raw=line,
        ))

    return doc


def parse(path):
    path = Path(path)
    text = path.read_bytes().decode("ascii", errors="replace")
    return parse_lines(text.splitlines(), path=path)
