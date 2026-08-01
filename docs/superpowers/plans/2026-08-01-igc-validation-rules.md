# IGC Validation Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `skills/validate-igc-files` so it implements every rule in `formulas/IGC_Validation_Rules.md` across two severity tiers, without losing the report's signal-to-noise.

**Architecture:** Parse each IGC file once into an `IGCDoc` document model, then run 53 pure rule functions registered in a single table with their severity. ERROR findings fail conformance and set exit code 1; WARNING findings are always reported but never fail a file. ENL and GPS-anomaly measurements get their own observation sections and affect neither.

**Tech Stack:** Python 3, standard library only. pytest for tests.

**Spec:** `docs/superpowers/specs/2026-08-01-igc-validation-rules-design.md`

## Global Constraints

- Python standard library only. No third-party runtime dependencies. pytest is a test-only dependency.
- The invocation documented in `SKILL.md` must keep working unchanged: `python3 ~/.claude/skills/validate-igc-files/scripts/validate_igc_files.py <directory>`
- Exit code 1 if any ERROR finding exists, 0 otherwise. WARNING findings and observations never change it.
- Every rule emits **at most one Finding per file**, carrying a count and the first offending line. This matches the existing report style (`1 line(s) with control/non-ASCII characters (first at line 17453)`) and stops a rule from emitting thousands of lines.
- Severity strings are exactly `"error"` and `"warning"`.
- All work happens in `/home/angel/gliding-ai-skills`. The repo is the source of truth; `~/.claude/skills/validate-igc-files/` is a deployed copy synced in Task 12.
- Two source-of-truth references live outside the repo: `/home/angel/src/formulas/IGCformat.md` and `/home/angel/src/formulas/IGC_Validation_Rules.md`.
- The 308-file calibration corpus is `/home/angel/IGCfiles/`. It is not in the repo; tests that need it skip when it is absent.

## Spec Addendum

The spec's rule catalogue lists 52 rules but omits one requirement from
§8 of the rules document: *"Declaration time must be non-zero/decodable — a
zero/unknown time is an error."* This plan adds it as `C_ZERO_DECL_TIME`
(ERROR, 0 hits on the corpus), bringing the total to **53 rules: 30 ERROR,
23 WARNING**. Task 12 updates the spec to match.

## File Structure

| File | Responsibility |
|---|---|
| `skills/validate-igc-files/scripts/igc_model.py` | Read and decode one IGC file into `IGCDoc`. No validation logic. |
| `skills/validate-igc-files/scripts/igc_rules.py` | `Finding`, `Rule`, the `@rule` registry, and all 53 rule functions. No I/O. |
| `skills/validate-igc-files/scripts/igc_observations.py` | ENL engine-on and GPS-anomaly measurement. Not pass/fail. |
| `skills/validate-igc-files/scripts/validate_igc_files.py` | CLI entry point, directory walk, text and JSON reporting. |
| `skills/validate-igc-files/scripts/tests/build_fixtures.py` | Generates the baseline fixture and one mutation per rule. |
| `skills/validate-igc-files/scripts/tests/fixtures/*.igc` | Generated; committed so failures are inspectable. |
| `skills/validate-igc-files/scripts/tests/test_model.py` | Parser unit tests. |
| `skills/validate-igc-files/scripts/tests/test_rules.py` | Parametrized: every rule fires on its fixture, stays silent on baseline. |
| `skills/validate-igc-files/scripts/tests/test_corpus.py` | Regression against `/home/angel/IGCfiles/`; skipped if absent. |

Observations are split into their own module rather than living in
`igc_rules.py` because they do not return `Finding` objects and are not part of
the pass/fail registry — mixing them in would blur the one distinction the
whole design rests on.

---

### Task 1: Document model

**Files:**
- Create: `skills/validate-igc-files/scripts/igc_model.py`
- Test: `skills/validate-igc-files/scripts/tests/test_model.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse(path) -> IGCDoc`; `parse_lines(lines, path=None) -> IGCDoc`; dataclasses `Ext(tlc: str, start: int, end: int)`, `Fix(line, time, lat, lon, valid, palt, galt, ext, raw)`, `IGCDoc`. `IGCDoc` fields: `path`, `lines: list[str]`, `numbered() -> Iterator[tuple[int, str]]`, `by_type: dict[str, list[tuple[int, str]]]`, `a_record: str | None`, `a_line: int | None`, `headers: dict[str, tuple[int, str]]`, `i_ext: list[Ext]`, `j_ext: list[Ext]`, `m_ext: list[Ext]`, `i_records`, `j_records`, `m_records` (each `list[tuple[int, str]]`), `fixes: list[Fix]`, `bad_b: list[int]`, `first_g: int | None`, `flight_date: str | None`, `empty_lines: list[int]`. Line numbers are 1-based throughout.

- [ ] **Step 1: Write the failing test**

Create `skills/validate-igc-files/scripts/tests/test_model.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'igc_model'`

- [ ] **Step 3: Write the model**

Create `skills/validate-igc-files/scripts/igc_model.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_model.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_model.py skills/validate-igc-files/scripts/tests/test_model.py
git commit -m "feat(igc): add IGC document model with single-pass decode"
```

---

### Task 2: Rule framework, fixtures, and character rules

Establishes the registry and the test harness that every later task plugs into,
then proves both work by implementing the 7 record-type and character rules.

**Files:**
- Create: `skills/validate-igc-files/scripts/igc_rules.py`
- Create: `skills/validate-igc-files/scripts/tests/build_fixtures.py`
- Create: `skills/validate-igc-files/scripts/tests/test_rules.py`

**Interfaces:**
- Consumes: `igc_model.parse`, `igc_model.parse_lines`.
- Produces: `ERROR = "error"`, `WARNING = "warning"`; `Finding(rule_id, severity, category, message, line=None, data=None)`; `Rule(id, severity, category, fn)`; `RULES: list[Rule]`; decorator `@rule(id, severity, category)`; helper `summarize(rule_id, severity, category, hits, template)` where `hits` is `list[tuple[int, str]]`; `run_all(doc) -> list[Finding]`. `build_fixtures.py` exposes `BASE_LINES: list[str]` and `MUTATIONS: dict[str, callable]`.

- [ ] **Step 1: Write the fixture builder**

Create `skills/validate-igc-files/scripts/tests/build_fixtures.py`. Later tasks
append to `MUTATIONS`; this step creates it with the 7 character-rule entries.

```python
#!/usr/bin/env python3
"""Generate test fixtures: one baseline conformant file plus one mutation per rule.

The baseline is built column-by-column rather than typed by hand, because the
B-record extension columns declared in the I record must line up exactly and an
off-by-one there would silently break half the rules.

Run: python3 build_fixtures.py
"""

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# I record declares FXA 36-38, SIU 39-40, ENL 41-43 -> B records are 43 chars.
I_RECORD = "I033638FXA3940SIU4143ENL"
J_RECORD = "J020810WDI1113WSP"


def b(seconds, valid="A", galt=550, enl="050"):
    """Build one 43-character B record at the given second-of-day."""
    hh, mm, ss = seconds // 3600, seconds % 3600 // 60, seconds % 60
    return (
        "B"
        + f"{hh:02d}{mm:02d}{ss:02d}"
        + "5144250N"
        + "01747333E"
        + valid
        + "00500"
        + f"{galt:05d}"
        + "010"      # FXA
        + "09"       # SIU
        + enl        # ENL
    )


def k(seconds):
    """K record matching J_RECORD's last end pointer (13)."""
    hh, mm, ss = seconds // 3600, seconds % 3600 // 60, seconds % 60
    return "K" + f"{hh:02d}{mm:02d}{ss:02d}" + "270" + "015"


START = 11 * 3600 + 1 * 60 + 35

BASE_LINES = [
    "ANAV240406",
    "HFDTEDATE:130726,01",
    "HFPLTPILOTINCHARGE:Test Pilot",
    "HFCM2CREW2:NIL",
    "HFGTYGLIDERTYPE:LS 7",
    "HFGIDGLIDERID:D-3903",
    "HFDTMGPSDATUM:WGS84",
    "HFRFWFIRMWAREVERSION:1.0",
    "HFRHWHARDWAREVERSION:1.0",
    "HFFTYFRTYPE:Naviter,Oudie N IGC",
    "HFGPSRECEIVER:uBlox,MAX-M8Q,72,50000",
    "HFPRSPRESSALTSENSOR:Bosch,BMP390L,9150",
    "HFFRSSECURITY OK",
    I_RECORD,
    J_RECORD,
    # Declaration: 2 waypoints -> 5 + 2 = 7 C records total.
    "C130726120000130726000102TASK",
    "C5144250N01747333ETAKEOFF",
    "C5144250N01747333ESTART",
    "C5135226N01712760ETP1",
    "C5126569N01749664ETP2",
    "C5142083N01750783EFINISH",
    "C5142083N01750783ELANDING",
    "F110130010203040506",
    b(START + 0),
    b(START + 1),
    b(START + 2),
    "E" + f"{(START + 3) // 3600:02d}{(START + 3) % 3600 // 60:02d}{(START + 3) % 60:02d}" + "ATS",
    b(START + 3),
    b(START + 4),
    k(START + 4),
    b(START + 5),
    "F110230010203040506",
    b(START + 6),
    b(START + 7),
    b(START + 8),
    b(START + 9),
    "LNAVPILOT COMMENT",
    "G0123456789ABCDEF0123456789ABCDEF",
]


def replace(lines, predicate, new):
    """Return a copy with the first line matching predicate replaced."""
    out = list(lines)
    for i, line in enumerate(out):
        if predicate(line):
            out[i] = new
            return out
    raise AssertionError("no line matched the predicate")


def drop(lines, predicate):
    out = [l for l in lines if not predicate(l)]
    assert len(out) < len(lines), "predicate dropped nothing"
    return out


MUTATIONS = {
    # --- Task 2: record type and character set ---
    "RECORD_TYPE_INVALID": lambda L: L[:14] + ["ZBOGUSRECORD"] + L[14:],
    "WILDCARD_DATA": lambda L: replace(L, lambda l: l.startswith("B"), b(START)[:-3] + "0?0"),
    "WILDCARD_META": lambda L: replace(L, lambda l: l.startswith("HFGTY"), "HFGTYGLIDERTYPE:LS ?"),
    "CHAR_CONTROL": lambda L: L[:14] + ["LNAV\x01BAD"] + L[14:],
    "CHAR_NON_ASCII": lambda L: L[:14] + ["LNAVPILOT Jose Ramirezé"] + L[14:],
    "CHAR_EMPTY_LINE": lambda L: L[:14] + [""] + L[14:],
    "CHAR_DISALLOWED": lambda L: L[:14] + ["LNAVBAD$VALUE"] + L[14:],
}


def main():
    # Written as latin-1 bytes, not ASCII text: the CHAR_NON_ASCII fixture needs a
    # real high byte on disk, which is how accented pilot names actually reach us
    # in appended L records. Everything else in these fixtures is plain ASCII.
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / "valid_baseline.igc").write_bytes(
        ("\n".join(BASE_LINES) + "\n").encode("ascii"))
    for rule_id, mutate in MUTATIONS.items():
        lines = mutate(list(BASE_LINES))
        (FIXTURES / f"{rule_id}.igc").write_bytes(
            ("\n".join(lines) + "\n").encode("latin-1", errors="replace"))
    print(f"wrote baseline + {len(MUTATIONS)} fixtures to {FIXTURES}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the failing test harness**

Create `skills/validate-igc-files/scripts/tests/test_rules.py`. These three tests
cover every rule in the registry, now and as later tasks add more.

```python
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
```

`test_rule_silent_on_clean_baseline` is the important one — it is what stops a
rule from firing on 85% of real files, which is the failure mode this whole
design exists to avoid.

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'igc_rules'`

- [ ] **Step 4: Write the rule framework and character rules**

Create `skills/validate-igc-files/scripts/igc_rules.py`:

```python
"""Validation rules for IGC flight logs.

Two severity tiers, calibrated in
docs/superpowers/specs/2026-08-01-igc-validation-rules-design.md against a
308-file corpus of real competition logs:

  error   - the file's integrity or scoring validity is in question
  warning - a spec deviation worth reporting that does not invalidate the file

Several rules in formulas/IGC_Validation_Rules.md are classified there as errors
but fire on the overwhelming majority of valid competition files (LXNav's
A-record serial format, F-record intervals, ENL minima). They are warnings here.
Making them errors would push the failure rate to ~98% and bury the real
findings, the same reason the spec's 76-character line limit has never been
enforced.

Every rule returns at most one Finding per file, carrying a count and the first
offending line, so a single malformed file cannot flood the report.
"""

import re
from dataclasses import dataclass, field

ERROR = "error"
WARNING = "warning"


@dataclass
class Finding:
    rule_id: str
    severity: str
    category: str
    message: str
    line: int = None
    data: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    category: str
    fn: object


RULES = []


def rule(rule_id, severity, category):
    """Register a rule. The decorated function takes an IGCDoc and returns
    a list of Findings (empty when the file is clean)."""
    def deco(fn):
        RULES.append(Rule(rule_id, severity, category, fn))
        return fn
    return deco


def summarize(rule_id, severity, category, hits, template):
    """Collapse many occurrences into a single Finding.

    hits: list of (line_number, detail_string), first occurrence first.
    template is formatted with n=count, line=first line, detail=first detail.
    """
    if not hits:
        return []
    line, detail = hits[0]
    return [Finding(
        rule_id, severity, category,
        template.format(n=len(hits), line=line, detail=detail),
        line, {"count": len(hits), "first_line": line, "first_detail": detail},
    )]


def run_all(doc):
    out = []
    for r in RULES:
        out.extend(r.fn(doc))
    return out


# --------------------------------------------------------------------------
# Record type and character set  (IGC_Validation_Rules.md section 1)
# --------------------------------------------------------------------------

VALID_RECORD_TYPES = set("ABCDEFGHIJKLMN")
DATA_RECORDS = set("BCKN")
META_RECORDS = set("ADEFHIJM")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
# igc_model decodes with errors="replace", so a non-ASCII byte arrives as U+FFFD
# rather than as the original character. This matches it either way.
NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")
DISALLOWED_CHARS = set("$*!\\^~")


@rule("RECORD_TYPE_INVALID", ERROR, "record-type")
def r_record_type_invalid(doc):
    hits = [(n, l[0]) for n, l in doc.numbered()
            if l and l[0] not in VALID_RECORD_TYPES]
    return summarize(*_a("RECORD_TYPE_INVALID", ERROR, "record-type"), hits,
                     "{n} record(s) with an invalid type character "
                     "{detail!r} (first at line {line})")


@rule("WILDCARD_DATA", ERROR, "record-type")
def r_wildcard_data(doc):
    hits = [(n, l[0]) for n, l in doc.numbered()
            if l and l[0] in DATA_RECORDS and "?" in l]
    return summarize(*_a("WILDCARD_DATA", ERROR, "record-type"), hits,
                     "{n} data record(s) contain '?' (unavailable/invalid data "
                     "is not allowed in B/C/K/N records; first at line {line})")


@rule("WILDCARD_META", WARNING, "record-type")
def r_wildcard_meta(doc):
    hits = [(n, l[0]) for n, l in doc.numbered()
            if l and l[0] in META_RECORDS and "?" in l]
    return summarize(*_a("WILDCARD_META", WARNING, "record-type"), hits,
                     "{n} record(s) contain '?' and need investigation "
                     "(first at line {line})")


@rule("CHAR_CONTROL", ERROR, "character-set")
def r_char_control(doc):
    hits = [(n, "") for n, l in doc.numbered() if CONTROL_RE.search(l)]
    return summarize(*_a("CHAR_CONTROL", ERROR, "character-set"), hits,
                     "{n} line(s) contain a control character below 0x20 "
                     "(first at line {line}) - probable corruption in transfer")


@rule("CHAR_NON_ASCII", WARNING, "character-set")
def r_char_non_ascii(doc):
    hits = [(n, "") for n, l in doc.numbered()
            if l and NON_ASCII_RE.search(l) and not CONTROL_RE.search(l)]
    return summarize(*_a("CHAR_NON_ASCII", WARNING, "character-set"), hits,
                     "{n} line(s) with non-ASCII characters (first at line "
                     "{line}) - spec para 6 requires transliteration")


@rule("CHAR_EMPTY_LINE", WARNING, "character-set")
def r_char_empty_line(doc):
    hits = [(n, "") for n in doc.empty_lines]
    return summarize(*_a("CHAR_EMPTY_LINE", WARNING, "character-set"), hits,
                     "{n} empty line(s) inside the file (first at line {line})")


@rule("CHAR_DISALLOWED", WARNING, "character-set")
def r_char_disallowed(doc):
    limit = doc.first_g or len(doc.lines) + 1
    hits = [(n, "") for n, l in doc.numbered()
            if n < limit and DISALLOWED_CHARS & set(l)]
    return summarize(*_a("CHAR_DISALLOWED", WARNING, "character-set"), hits,
                     r"{n} line(s) contain disallowed characters ($ * ! \ ^ ~) "
                     "(first at line {line})")


def _a(rule_id, severity, category):
    """Tiny helper so each rule states its identity exactly once."""
    return (rule_id, severity, category)
```

`CHAR_NON_ASCII` skips lines that already tripped `CHAR_CONTROL`, so a corrupted
transfer is reported once as corruption rather than twice.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -v`
Expected: PASS — 7 rules × 2 parametrized tests + 3 registry tests = 17 passing

- [ ] **Step 6: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_rules.py skills/validate-igc-files/scripts/tests/
git commit -m "feat(igc): add rule registry, fixture builder, and character-set rules"
```

---

### Task 3: A-record and H-record rules

14 rules. A-record 4, H-record 10.

**Files:**
- Modify: `skills/validate-igc-files/scripts/igc_rules.py` (append)
- Modify: `skills/validate-igc-files/scripts/tests/build_fixtures.py` (extend `MUTATIONS`)

**Interfaces:**
- Consumes: `rule`, `summarize`, `_a`, `ERROR`, `WARNING`, `Finding` from Task 2; `doc.a_record`, `doc.a_line`, `doc.headers`, `doc.by_type`, `doc.flight_date` from Task 1.
- Produces: no new callables. Adds 14 entries to `RULES`.

- [ ] **Step 1: Add the fixture mutations**

In `build_fixtures.py`, add to `MUTATIONS` before the closing brace:

```python
    # --- Task 3: A record ---
    "A_RECORD_POSITION": lambda L: L[1:],
    "A_NOT_FAI_APPROVED": lambda L: ["AXXX240406"] + L[1:],
    "A_SHORT_SERIAL": lambda L: ["ALXVB0V"] + L[1:],
    "A_BAD_SEPARATOR": lambda L: ["ANAV240406_FLIGHT:1"] + L[1:],
    # --- Task 3: H records ---
    "H_NONE": lambda L: drop(L, lambda l: l.startswith("H")),
    "H_MISSING_MANDATORY": lambda L: drop(L, lambda l: l.startswith("HFCM2")),
    "H_NONCONTIGUOUS": lambda L: L[:5] + ["LNAVINTERRUPTION"] + L[5:],
    "H_DUPLICATE_SUBTYPE": lambda L: L[:6] + ["HFGIDGLIDERID:D-9999"] + L[6:],
    "H_DTE_INVALID": lambda L: replace(L, lambda l: l.startswith("HFDTE"),
                                       "HFDTEDATE:993799,01"),
    "H_DTE_NO_LITERAL": lambda L: replace(L, lambda l: l.startswith("HFDTE"),
                                          "HFDTE130726"),
    "H_DTM_NOT_WGS84": lambda L: replace(L, lambda l: l.startswith("HFDTM"),
                                         "HFDTMGPSDATUM:OSGB36"),
    "H_FTY_NO_COMMA": lambda L: replace(L, lambda l: l.startswith("HFFTY"),
                                        "HFFTYFRTYPE:Naviter Oudie N IGC"),
    "H_FTY_MULTI_COMMA": lambda L: replace(L, lambda l: l.startswith("HFFTY"),
                                           "HFFTYFRTYPE:Naviter,Oudie,N IGC"),
    "H_FTY_NOT_IGC": lambda L: replace(L, lambda l: l.startswith("HFFTY"),
                                       "HFFTYFRTYPE:Naviter,Oudie N"),
```

- [ ] **Step 2: Generate the fixtures and confirm the suite is still green**

Run:
```bash
cd /home/angel/gliding-ai-skills/skills/validate-igc-files/scripts/tests && python3 build_fixtures.py
cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -q
```
Expected: `wrote baseline + 21 fixtures`, then 17 tests still passing. The 14 new
fixtures have no rules yet, so nothing exercises them — Steps 3 and 4 add the
rules, and the parametrized tests pick them up automatically.

- [ ] **Step 3: Append the A-record rules**

```python
# --------------------------------------------------------------------------
# A record  (section 2)
# --------------------------------------------------------------------------

def _a_serial(a_record):
    """Return the serial field: everything after the 3-letter manufacturer
    code, up to the comment separator if there is one."""
    tail = a_record[4:]
    for sep in ("-", "_", ":", " "):
        if sep in tail:
            tail = tail.split(sep, 1)[0]
    return tail


@rule("A_RECORD_POSITION", ERROR, "a-record")
def r_a_record_position(doc):
    a_lines = doc.of_type("A")
    if not a_lines:
        return [Finding("A_RECORD_POSITION", ERROR, "a-record",
                        "no A (manufacturer/serial) record", None, {"count": 0})]
    if len(a_lines) > 1:
        return [Finding("A_RECORD_POSITION", ERROR, "a-record",
                        f"{len(a_lines)} A records; exactly one is allowed",
                        a_lines[1][0], {"count": len(a_lines)})]
    n, line = a_lines[0]
    if n != 1:
        return [Finding("A_RECORD_POSITION", ERROR, "a-record",
                        f"A record is at line {n}, it must be the first record",
                        n, {})]
    if len(line) < 7:
        return [Finding("A_RECORD_POSITION", ERROR, "a-record",
                        f"A record too short for a 3-char manufacturer plus "
                        f"serial: {line!r}", n, {})]
    return []


@rule("A_NOT_FAI_APPROVED", ERROR, "a-record")
def r_a_not_fai_approved(doc):
    if doc.a_record and doc.a_record[1:4].startswith("X"):
        return [Finding("A_NOT_FAI_APPROVED", ERROR, "a-record",
                        f"manufacturer code {doc.a_record[1:4]!r} starts with X "
                        "- recorder is not FAI approved", doc.a_line,
                        {"manufacturer": doc.a_record[1:4]})]
    return []


@rule("A_SHORT_SERIAL", WARNING, "a-record")
def r_a_short_serial(doc):
    if not doc.a_record or len(doc.a_record) < 7:
        return []
    serial = _a_serial(doc.a_record)
    if len(serial) == 3:
        return [Finding("A_SHORT_SERIAL", WARNING, "a-record",
                        f"3-character legacy serial ID {serial!r}; new recorders "
                        "should use a 6-character S/ID", doc.a_line,
                        {"serial": serial})]
    if len(serial) not in (3, 6):
        return [Finding("A_SHORT_SERIAL", WARNING, "a-record",
                        f"badly formed serial ID {serial!r} ({len(serial)} chars; "
                        "expected 6)", doc.a_line, {"serial": serial})]
    return []


@rule("A_BAD_SEPARATOR", WARNING, "a-record")
def r_a_bad_separator(doc):
    if not doc.a_record:
        return []
    tail = doc.a_record[4:]
    if "_" in tail:
        return [Finding("A_BAD_SEPARATOR", WARNING, "a-record",
                        "A record uses '_' before the comment field; the spec "
                        "requires '-'", doc.a_line, {})]
    return []
```

`A_SHORT_SERIAL` and `A_BAD_SEPARATOR` are warnings rather than errors because
LXNav writes `ALXVB0V_FLIGHT:1` — 245 of the 308 corpus files trip both.

- [ ] **Step 4: Append the H-record rules**

```python
# --------------------------------------------------------------------------
# H records  (section 3)
# --------------------------------------------------------------------------

MANDATORY_H = {
    "DTE": "flight date", "PLT": "pilot in charge", "CM2": "crew 2",
    "GTY": "glider type", "GID": "glider ID", "DTM": "GNSS datum",
    "RFW": "firmware version", "RHW": "hardware version",
    "FTY": "FR type", "GPS": "GNSS receiver",
    "PRS": "pressure sensor", "FRS": "security status",
}

OPTIONAL_H = {"ATS", "BEI", "CCL", "CID", "CLB", "DB1", "DB2", "GAL",
              "GLO", "MOP", "OOI", "SIU", "TZN", "FXA"}


@rule("H_NONE", ERROR, "h-record")
def r_h_none(doc):
    if not doc.of_type("H"):
        return [Finding("H_NONE", ERROR, "h-record",
                        "no H (header) records at all", None, {})]
    return []


@rule("H_MISSING_MANDATORY", ERROR, "h-record")
def r_h_missing_mandatory(doc):
    if not doc.of_type("H"):
        return []            # H_NONE already reports this
    missing = [f"{t} ({d})" for t, d in MANDATORY_H.items()
               if t not in doc.headers]
    if missing:
        return [Finding("H_MISSING_MANDATORY", ERROR, "h-record",
                        "missing mandatory H record(s): " + ", ".join(missing),
                        None, {"missing": [m.split(" ")[0] for m in missing]})]
    return []


@rule("H_NONCONTIGUOUS", WARNING, "h-record")
def r_h_noncontiguous(doc):
    nums = [n for n, _ in doc.of_type("H")]
    if nums and nums[-1] - nums[0] + 1 != len(nums):
        return [Finding("H_NONCONTIGUOUS", WARNING, "h-record",
                        f"H records are not contiguous (span lines "
                        f"{nums[0]}-{nums[-1]} but only {len(nums)} of them)",
                        nums[0], {})]
    return []


@rule("H_DUPLICATE_SUBTYPE", WARNING, "h-record")
def r_h_duplicate_subtype(doc):
    seen, dupes = set(), []
    for n, line in doc.of_type("H"):
        if len(line) < 5:
            continue
        tlc = line[2:5]
        if tlc in seen:
            dupes.append((n, tlc))
        seen.add(tlc)
    return summarize(*_a("H_DUPLICATE_SUBTYPE", WARNING, "h-record"), dupes,
                     "{n} duplicate H record subtype(s), first {detail} at "
                     "line {line}")


@rule("H_DTE_INVALID", ERROR, "h-record")
def r_h_dte_invalid(doc):
    entry = doc.headers.get("DTE")
    if not entry:
        return []            # H_MISSING_MANDATORY reports absence
    n, _ = entry
    d = doc.flight_date
    if not d:
        return [Finding("H_DTE_INVALID", ERROR, "h-record",
                        "HFDTE contains no 6-digit date", n, {})]
    day, month = int(d[0:2]), int(d[2:4])
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return [Finding("H_DTE_INVALID", ERROR, "h-record",
                        f"HFDTE date {d!r} is not a valid DDMMYY date", n,
                        {"date": d})]
    return []


@rule("H_DTE_NO_LITERAL", WARNING, "h-record")
def r_h_dte_no_literal(doc):
    entry = doc.headers.get("DTE")
    if entry and "DATE:" not in entry[1]:
        return [Finding("H_DTE_NO_LITERAL", WARNING, "h-record",
                        "HFDTE is missing the literal 'DATE:'", entry[0], {})]
    return []


@rule("H_DTM_NOT_WGS84", ERROR, "h-record")
def r_h_dtm_not_wgs84(doc):
    entry = doc.headers.get("DTM")
    if entry and "WGS84" not in entry[1].upper():
        return [Finding("H_DTM_NOT_WGS84", ERROR, "h-record",
                        f"incorrect geodetic datum: {entry[1]!r} (WGS84 required)",
                        entry[0], {})]
    return []


def _fty_value(doc):
    entry = doc.headers.get("FTY")
    if not entry:
        return None, None
    n, line = entry
    return n, line[5:].split(":", 1)[-1]


@rule("H_FTY_NO_COMMA", ERROR, "h-record")
def r_h_fty_no_comma(doc):
    n, value = _fty_value(doc)
    if value is None:
        return []
    if value.count(",") == 0:
        return [Finding("H_FTY_NO_COMMA", ERROR, "h-record",
                        "HFFTY has no comma separating manufacturer from model",
                        n, {})]
    if value.strip().startswith(",") or value.strip().endswith(","):
        return [Finding("H_FTY_NO_COMMA", ERROR, "h-record",
                        "HFFTY comma is the first or last character of the field",
                        n, {})]
    return []


@rule("H_FTY_MULTI_COMMA", WARNING, "h-record")
def r_h_fty_multi_comma(doc):
    n, value = _fty_value(doc)
    if value is not None and value.count(",") > 1:
        return [Finding("H_FTY_MULTI_COMMA", WARNING, "h-record",
                        f"HFFTY has {value.count(',')} commas; exactly one is "
                        "expected", n, {"commas": value.count(",")})]
    return []


@rule("H_FTY_NOT_IGC", WARNING, "h-record")
def r_h_fty_not_igc(doc):
    entry = doc.headers.get("FTY")
    if entry and not entry[1].rstrip().endswith("IGC"):
        return [Finding("H_FTY_NOT_IGC", WARNING, "h-record",
                        "HFFTY does not end with 'IGC'", entry[0], {})]
    return []
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -v`
Expected: PASS — 21 rules × 2 + 3 = 45 passing

- [ ] **Step 6: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_rules.py skills/validate-igc-files/scripts/tests/
git commit -m "feat(igc): add A-record and H-record rules"
```

---

### Task 4: I, J and M record rules

11 rules, including the pointer-chain check that found 3 genuinely broken files
in the corpus.

**Files:**
- Modify: `skills/validate-igc-files/scripts/igc_rules.py` (append)
- Modify: `skills/validate-igc-files/scripts/tests/build_fixtures.py` (extend `MUTATIONS`)

**Interfaces:**
- Consumes: Task 2 framework; `doc.i_records`, `doc.j_records`, `doc.m_records`, `doc.i_ext`, `doc.j_ext`, `doc.m_ext`, `doc.fixes` from Task 1.
- Produces: `KNOWN_I_TLC`, `KNOWN_J_TLC`, `KNOWN_M_TLC` module constants; 11 entries in `RULES`.

- [ ] **Step 1: Add the fixture mutations**

```python
    # --- Task 4: I / J / M records ---
    "I_RECORD_COUNT": lambda L: L[:14] + [I_RECORD] + L[14:],
    "I_MISSING_EXT": lambda L: [
        l if l != I_RECORD else "I023638FXA3941ENL" for l in L],
    "I_LEN_MISMATCH": lambda L: [
        l if l != I_RECORD else I_RECORD + "XX" for l in L],
    "I_PTR_CHAIN": lambda L: [
        l if l != I_RECORD else "I033739FXA4041SIU4244ENL" for l in L],
    "TLC_UNKNOWN_I": lambda L: [
        l if l != I_RECORD else "I033638FXA3940SIU4143ZZZ" for l in L],
    "J_RECORD_COUNT": lambda L: L[:15] + [J_RECORD] + L[15:],
    "TLC_UNKNOWN_J": lambda L: [
        l if l != J_RECORD else "J020810QQQ1113WSP" for l in L],
    "M_RECORD_COUNT": lambda L: L[:15] + ["M010810HRT", "M010810HRT"] + L[15:],
    "TLC_UNKNOWN_M": lambda L: L[:15] + ["M010810ZZZ"] + L[15:],
    "ENL_MOP_ALL_ZERO": lambda L: [
        b(START + i, enl="000") if l.startswith("B") else l
        for i, l in enumerate(L)],
    "ENL_MOP_MIN_LOW": lambda L: replace(
        L, lambda l: l.startswith("B"), b(START, enl="005")),
```

`ENL_MOP_ALL_ZERO`'s comprehension re-times every B record from its list index,
which is fine for a fixture: the rule under test only reads ENL values, and the
timing rules are not the ones being exercised here.

- [ ] **Step 2: Run the fixture builder and confirm the new rules are unregistered**

Run: `cd /home/angel/gliding-ai-skills/skills/validate-igc-files/scripts/tests && python3 build_fixtures.py`
Expected: `wrote baseline + 32 fixtures to .../fixtures`

- [ ] **Step 3: Append the I/J/M rules**

```python
# --------------------------------------------------------------------------
# I, J and M records  (sections 4, 5, 7)
# --------------------------------------------------------------------------

KNOWN_I_TLC = {"ACX", "ACY", "ACZ", "ANX", "ANY", "ANZ", "AOP", "AOR", "AOA",
               "ENL", "FXA", "GSP", "LAD", "LOD", "MOP", "NET", "OAT", "RPM",
               "SIU", "TAS", "TRT", "VAT", "VXA", "CUR", "HDT", "HDM", "EGT",
               "FFL", "FLE", "VOL", "WDI", "WSP"}

KNOWN_J_TLC = {"AOA", "COT", "CUR", "CU1", "CU2", "DAE", "DAN", "EGT", "FLE",
               "FFL", "FXA", "GSP", "HDM", "HDT", "HUM", "IAS", "JPT", "LEB",
               "LE1", "LE2", "MOT", "NET", "MXR", "OAT", "RAI", "REX", "RPM",
               "TAS", "TDS", "TRT", "VAR", "VOL", "VAT", "VO1", "VO2", "VXA",
               "WDI", "WSP", "WVE"} | KNOWN_I_TLC

KNOWN_M_TLC = {"HRT", "OXY"}

MANDATORY_I_EXT = ("FXA", "ENL", "SIU")
ENL_MOP_MIN = 10


def _unknown_tlc(exts, known):
    # 'Xnn' is a documented wildcard form in J records.
    return [e.tlc for e in exts
            if e.tlc not in known and not re.fullmatch(r"X..", e.tlc)]


@rule("I_RECORD_COUNT", ERROR, "i-record")
def r_i_record_count(doc):
    n = len(doc.i_records)
    if n == 0:
        return [Finding("I_RECORD_COUNT", ERROR, "i-record",
                        "no I record detected", None, {"count": 0})]
    if n > 1:
        return [Finding("I_RECORD_COUNT", ERROR, "i-record",
                        f"{n} I records; exactly one is allowed - B record "
                        "extension decoding is unreliable",
                        doc.i_records[1][0], {"count": n})]
    return []


@rule("I_MISSING_EXT", ERROR, "i-record")
def r_i_missing_ext(doc):
    if not doc.i_records:
        return []
    have = {e.tlc for e in doc.i_ext}
    missing = [t for t in MANDATORY_I_EXT if t not in have]
    if missing:
        return [Finding("I_MISSING_EXT", ERROR, "i-record",
                        "I record missing mandatory extension(s): "
                        + ", ".join(missing),
                        doc.i_records[0][0], {"missing": missing})]
    return []


@rule("I_LEN_MISMATCH", ERROR, "i-record")
def r_i_len_mismatch(doc):
    if not doc.i_records:
        return []
    n, line = doc.i_records[0]
    m = re.match(r"^I(\d{2})", line)
    if not m:
        return [Finding("I_LEN_MISMATCH", ERROR, "i-record",
                        "I record has no 2-digit item count", n, {})]
    expected = int(m.group(1)) * 7 + 3
    if len(line) != expected:
        return [Finding("I_LEN_MISMATCH", ERROR, "i-record",
                        f"I record declares {m.group(1)} items so should be "
                        f"{expected} chars, but is {len(line)}", n,
                        {"declared": expected, "actual": len(line)})]
    return []


@rule("I_PTR_CHAIN", ERROR, "i-record")
def r_i_ptr_chain(doc):
    if not doc.i_records or not doc.i_ext:
        return []
    n = doc.i_records[0][0]
    prev = 35          # the fixed B-record fields occupy columns 1-35
    for idx, e in enumerate(doc.i_ext, start=1):
        if e.start != prev + 1:
            return [Finding("I_PTR_CHAIN", ERROR, "i-record",
                            f"I record column pointers broken: item {idx} "
                            f"({e.tlc}) starts at {e.start}, expected "
                            f"{prev + 1}", n,
                            {"item": idx, "start": e.start,
                             "expected": prev + 1})]
        if e.end < e.start:
            return [Finding("I_PTR_CHAIN", ERROR, "i-record",
                            f"I record item {idx} ({e.tlc}) ends at {e.end} "
                            f"before it starts at {e.start}", n, {"item": idx})]
        prev = e.end
    return []


@rule("TLC_UNKNOWN_I", WARNING, "i-record")
def r_tlc_unknown_i(doc):
    unknown = _unknown_tlc(doc.i_ext, KNOWN_I_TLC)
    if unknown:
        return [Finding("TLC_UNKNOWN_I", WARNING, "i-record",
                        f"{len(unknown)} unrecognised I record TLC(s): "
                        + ", ".join(unknown),
                        doc.i_records[0][0], {"tlcs": unknown})]
    return []


@rule("J_RECORD_COUNT", ERROR, "j-record")
def r_j_record_count(doc):
    n = len(doc.j_records)
    if n > 1:
        return [Finding("J_RECORD_COUNT", ERROR, "j-record",
                        f"there are {n} J records and there must only be one",
                        doc.j_records[1][0], {"count": n})]
    return []


@rule("TLC_UNKNOWN_J", WARNING, "j-record")
def r_tlc_unknown_j(doc):
    unknown = _unknown_tlc(doc.j_ext, KNOWN_J_TLC)
    if unknown:
        return [Finding("TLC_UNKNOWN_J", WARNING, "j-record",
                        f"{len(unknown)} unrecognised J record TLC(s): "
                        + ", ".join(unknown),
                        doc.j_records[0][0], {"tlcs": unknown})]
    return []


@rule("M_RECORD_COUNT", ERROR, "m-record")
def r_m_record_count(doc):
    n = len(doc.m_records)
    if n > 1:
        return [Finding("M_RECORD_COUNT", ERROR, "m-record",
                        f"there are {n} M records and there must only be one",
                        doc.m_records[1][0], {"count": n})]
    return []


@rule("TLC_UNKNOWN_M", WARNING, "m-record")
def r_tlc_unknown_m(doc):
    unknown = _unknown_tlc(doc.m_ext, KNOWN_M_TLC)
    if unknown:
        return [Finding("TLC_UNKNOWN_M", WARNING, "m-record",
                        f"{len(unknown)} unrecognised M record TLC(s): "
                        + ", ".join(unknown),
                        doc.m_records[0][0], {"tlcs": unknown})]
    return []


def _ext_values(doc, tlc):
    return [int(f.ext[tlc]) for f in doc.fixes
            if tlc in f.ext and f.ext[tlc].isdigit()]


@rule("ENL_MOP_ALL_ZERO", ERROR, "engine")
def r_enl_mop_all_zero(doc):
    for tlc in ("ENL", "MOP"):
        values = _ext_values(doc, tlc)
        if values and max(values) == 0:
            return [Finding("ENL_MOP_ALL_ZERO", ERROR, "engine",
                            f"{tlc} is zero across all {len(values)} fixes - "
                            "possibly faulty hardware", None,
                            {"tlc": tlc, "fixes": len(values)})]
    return []


@rule("ENL_MOP_MIN_LOW", WARNING, "engine")
def r_enl_mop_min_low(doc):
    for tlc in ("ENL", "MOP"):
        values = _ext_values(doc, tlc)
        if values and 0 < min(values) < ENL_MOP_MIN:
            first = next(f for f in doc.fixes
                         if f.ext.get(tlc, "").isdigit()
                         and int(f.ext[tlc]) == min(values))
            return [Finding("ENL_MOP_MIN_LOW", WARNING, "engine",
                            f"minimum {tlc} is {min(values)}, below the "
                            f"expected floor of {ENL_MOP_MIN}", first.line,
                            {"tlc": tlc, "min": min(values)})]
    return []
```

`ENL_MOP_MIN_LOW` requires `min > 0` so it does not double-report a file that
`ENL_MOP_ALL_ZERO` has already flagged as a dead sensor.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -v`
Expected: PASS — 32 rules × 2 + 3 = 67 passing

- [ ] **Step 5: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_rules.py skills/validate-igc-files/scripts/tests/
git commit -m "feat(igc): add I/J/M record structure and ENL/MOP sensor rules"
```

---

### Task 5: B, K and G record rules

7 rules, including the two carried over from the current implementation.

**Files:**
- Modify: `skills/validate-igc-files/scripts/igc_rules.py` (append)
- Modify: `skills/validate-igc-files/scripts/tests/build_fixtures.py` (extend `MUTATIONS`)

**Interfaces:**
- Consumes: Task 2 framework; `doc.fixes`, `doc.bad_b`, `doc.first_g`, `doc.i_ext`, `doc.j_ext` from Task 1.
- Produces: 7 entries in `RULES`.

- [ ] **Step 1: Add the fixture mutations**

```python
    # --- Task 5: B / K / G records ---
    "B_MALFORMED": lambda L: replace(L, lambda l: l.startswith("B"),
                                     "B999999XXXXXXXNXXXXXXXXEA0050000550010090500"),
    "B_LEN_MISMATCH": lambda L: replace(L, lambda l: l.startswith("B"),
                                        b(START)[:-2]),
    "B_V_FLAG_NONZERO_ALT": lambda L: replace(L, lambda l: l.startswith("B"),
                                              b(START, valid="V", galt=550)),
    "K_LEN_MISMATCH": lambda L: replace(L, lambda l: l.startswith("K"),
                                        "K1101390"),
    "K_NON_NUMERIC": lambda L: replace(L, lambda l: l.startswith("K"),
                                       "K110139ABC015"),
    "G_MISSING": lambda L: drop(L, lambda l: l.startswith("G")),
    "G_TRAILING_RECORDS": lambda L: L + [b(START + 20)],
```

- [ ] **Step 2: Run the fixture builder**

Run: `cd /home/angel/gliding-ai-skills/skills/validate-igc-files/scripts/tests && python3 build_fixtures.py`
Expected: `wrote baseline + 39 fixtures to .../fixtures`

- [ ] **Step 3: Append the B/K/G rules**

```python
# --------------------------------------------------------------------------
# B, K and G records  (sections 6, 11)
# --------------------------------------------------------------------------

@rule("B_MALFORMED", ERROR, "b-record")
def r_b_malformed(doc):
    if not doc.of_type("B"):
        return [Finding("B_MALFORMED", ERROR, "b-record",
                        "no B (fix) records", None, {"count": 0})]
    hits = [(n, "") for n in doc.bad_b]
    return summarize(*_a("B_MALFORMED", ERROR, "b-record"), hits,
                     "{n} malformed or truncated B record(s) - bad time, "
                     "N/S, E/W, A/V or altitude field (first at line {line})")


@rule("B_LEN_MISMATCH", ERROR, "b-record")
def r_b_len_mismatch(doc):
    if not doc.fixes:
        return []
    expected = doc.i_ext[-1].end if doc.i_ext else 35
    hits = [(f.line, str(len(f.raw))) for f in doc.fixes
            if len(f.raw) != expected]
    return summarize(*_a("B_LEN_MISMATCH", ERROR, "b-record"), hits,
                     "{n} B record(s) are " + str(expected) +
                     " chars per the I record but measure {detail} "
                     "(first at line {line})")


@rule("B_V_FLAG_NONZERO_ALT", WARNING, "b-record")
def r_b_v_flag_nonzero_alt(doc):
    hits = [(f.line, str(f.galt)) for f in doc.fixes
            if f.valid == "V" and f.galt != 0]
    return summarize(*_a("B_V_FLAG_NONZERO_ALT", WARNING, "b-record"), hits,
                     "{n} fix(es) flagged invalid (V) carry a non-zero GNSS "
                     "altitude, first {detail} m at line {line}")


def _k_expected_len(doc):
    return max((e.end for e in doc.j_ext), default=None)


@rule("K_LEN_MISMATCH", ERROR, "k-record")
def r_k_len_mismatch(doc):
    expected = _k_expected_len(doc)
    if expected is None or len(doc.j_records) != 1:
        return []
    hits = [(n, str(len(l))) for n, l in doc.of_type("K") if len(l) != expected]
    return summarize(*_a("K_LEN_MISMATCH", ERROR, "k-record"), hits,
                     "{n} K record(s) should be " + str(expected) +
                     " chars per the J record but measure {detail} "
                     "(first at line {line})")


@rule("K_NON_NUMERIC", ERROR, "k-record")
def r_k_non_numeric(doc):
    if len(doc.j_records) != 1:
        return []
    hits = [(n, "") for n, l in doc.of_type("K")
            if len(l) > 7 and not l[7:].isdigit()]
    return summarize(*_a("K_NON_NUMERIC", ERROR, "k-record"), hits,
                     "{n} K record(s) contain non-numeric data after the "
                     "timestamp (first at line {line})")


@rule("G_MISSING", ERROR, "g-record")
def r_g_missing(doc):
    if doc.first_g is None:
        return [Finding("G_MISSING", ERROR, "g-record",
                        "no G (security) record - the file is truncated or its "
                        "security data was stripped, so it cannot be validated",
                        None, {})]
    return []


@rule("G_TRAILING_RECORDS", ERROR, "g-record")
def r_g_trailing_records(doc):
    if doc.first_g is None:
        return []
    hits = [(n, l[0]) for n, l in doc.numbered()
            if n > doc.first_g and l and l[0] not in "GL"]
    return summarize(*_a("G_TRAILING_RECORDS", ERROR, "g-record"), hits,
                     "{n} non-G/L record(s) after the first G record, first a "
                     "{detail} record at line {line} - truncated or "
                     "concatenated file")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -v`
Expected: PASS — 39 rules × 2 + 3 = 81 passing

- [ ] **Step 5: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_rules.py skills/validate-igc-files/scripts/tests/
git commit -m "feat(igc): add B, K and G record rules"
```

---

### Task 6: C-record and E-record rules

7 rules. Includes `C_ZERO_DECL_TIME`, the spec addendum.

**Files:**
- Modify: `skills/validate-igc-files/scripts/igc_rules.py` (append)
- Modify: `skills/validate-igc-files/scripts/tests/build_fixtures.py` (extend `MUTATIONS`)

**Interfaces:**
- Consumes: Task 2 framework; `doc.of_type("C")`, `doc.of_type("E")`, `doc.lines`, `doc.fixes`, `doc.flight_date` from Task 1.
- Produces: `KNOWN_E_CODES`, `PEV_FAST_FIX_COUNT`; 7 entries in `RULES`.

- [ ] **Step 1: Add the fixture mutations**

```python
    # --- Task 6: C and E records ---
    "C_DECL_AFTER_FLIGHT": lambda L: replace(
        L, lambda l: l.startswith("C1307"), "C140726120000130726000102TASK"),
    "C_ZERO_DECL_TIME": lambda L: replace(
        L, lambda l: l.startswith("C1307"), "C130726000000130726000102TASK"),
    "C_FLIGHTDATE_MISMATCH": lambda L: replace(
        L, lambda l: l.startswith("C1307"), "C130726120000110726000102TASK"),
    "C_COUNT_MISMATCH": lambda L: replace(
        L, lambda l: l.startswith("C1307"), "C130726120000130726000104TASK"),
    "E_UNKNOWN_CODE": lambda L: replace(
        L, lambda l: l.startswith("E"), "E110138ZZZ"),
    "E_NOT_FOLLOWED_BY_B": lambda L: replace(
        L, lambda l: l.startswith("E"), "E110159ATS"),
    "E_PEV_NO_FAST_FIX": lambda L: replace(
        L, lambda l: l.startswith("E"), "E110138PEV"),
```

`C_COUNT_MISMATCH` declares 4 waypoints, so 9 C records are expected where the
baseline has 7. `E_PEV_NO_FAST_FIX` reuses the baseline's E-record slot, which is
followed by a matching B record but only 6 further fixes — short of the 30
required inside 30 seconds.

- [ ] **Step 2: Run the fixture builder**

Run: `cd /home/angel/gliding-ai-skills/skills/validate-igc-files/scripts/tests && python3 build_fixtures.py`
Expected: `wrote baseline + 46 fixtures to .../fixtures`

- [ ] **Step 3: Append the C-record rules**

```python
# --------------------------------------------------------------------------
# C records - task declaration  (section 8)
# --------------------------------------------------------------------------

C_HEADER_RE = re.compile(
    r"^C(\d{6})(\d{6})(\d{6})(\d{4})(\d{2})")


def _c_header(doc):
    """Return (line_no, match) for the declaration header C record, or None.

    A file with no C records is not a finding - declarations are optional.
    """
    c = doc.of_type("C")
    if not c:
        return None
    n, line = c[0]
    m = C_HEADER_RE.match(line)
    return (n, m) if m else None


def _ddmmyy_key(d):
    """Sortable YYMMDD key from a DDMMYY string."""
    return d[4:6] + d[2:4] + d[0:2]


@rule("C_DECL_AFTER_FLIGHT", ERROR, "c-record")
def r_c_decl_after_flight(doc):
    hdr = _c_header(doc)
    if not hdr or not doc.flight_date:
        return []
    n, m = hdr
    if _ddmmyy_key(m.group(1)) > _ddmmyy_key(doc.flight_date):
        return [Finding("C_DECL_AFTER_FLIGHT", ERROR, "c-record",
                        f"declaration date {m.group(1)} is after the flight "
                        f"date {doc.flight_date}", n,
                        {"declared": m.group(1), "flight": doc.flight_date})]
    return []


@rule("C_ZERO_DECL_TIME", ERROR, "c-record")
def r_c_zero_decl_time(doc):
    hdr = _c_header(doc)
    if not hdr:
        return []
    n, m = hdr
    if m.group(2) == "000000":
        return [Finding("C_ZERO_DECL_TIME", ERROR, "c-record",
                        "declaration time is zero or undecodable", n, {})]
    return []


@rule("C_FLIGHTDATE_MISMATCH", ERROR, "c-record")
def r_c_flightdate_mismatch(doc):
    hdr = _c_header(doc)
    if not hdr or not doc.flight_date:
        return []
    n, m = hdr
    embedded = m.group(3)
    if embedded != "000000" and embedded != doc.flight_date:
        return [Finding("C_FLIGHTDATE_MISMATCH", ERROR, "c-record",
                        f"flight date in the declaration ({embedded}) does not "
                        f"match HFDTE ({doc.flight_date})", n,
                        {"declared": embedded, "hfdte": doc.flight_date})]
    return []


@rule("C_COUNT_MISMATCH", ERROR, "c-record")
def r_c_count_mismatch(doc):
    hdr = _c_header(doc)
    if not hdr:
        return []
    n, m = hdr
    expected = int(m.group(5)) + 5
    actual = len(doc.of_type("C"))
    if actual != expected:
        return [Finding("C_COUNT_MISMATCH", ERROR, "c-record",
                        f"declaration says {m.group(5)} waypoints so {expected} "
                        f"C records are expected, found {actual}", n,
                        {"expected": expected, "actual": actual})]
    return []
```

- [ ] **Step 4: Append the E-record rules**

```python
# --------------------------------------------------------------------------
# E records - events  (section 10)
# --------------------------------------------------------------------------

KNOWN_E_CODES = {"ATS", "BFI", "CGD", "FIN", "FLP", "GSP", "LOV", "MAC",
                 "OA1", "OA2", "OA3", "ONT", "PEV", "STA", "TPC", "TRT", "UND"}

PEV_FAST_FIX_COUNT = 30


@rule("E_UNKNOWN_CODE", WARNING, "e-record")
def r_e_unknown_code(doc):
    hits = [(n, l[7:10]) for n, l in doc.of_type("E")
            if len(l) >= 10 and l[7:10] not in KNOWN_E_CODES]
    return summarize(*_a("E_UNKNOWN_CODE", WARNING, "e-record"), hits,
                     "{n} E record(s) with an unrecognised event code, first "
                     "{detail!r} at line {line}")


@rule("E_NOT_FOLLOWED_BY_B", ERROR, "e-record")
def r_e_not_followed_by_b(doc):
    hits = []
    for n, line in doc.of_type("E"):
        nxt = doc.lines[n] if n < len(doc.lines) else ""
        if not nxt.startswith("B"):
            hits.append((n, "no B record follows"))
        elif nxt[1:7] != line[1:7]:
            hits.append((n, f"timestamp {nxt[1:7]} != {line[1:7]}"))
    return summarize(*_a("E_NOT_FOLLOWED_BY_B", ERROR, "e-record"), hits,
                     "{n} E record(s) not followed by a B record with a "
                     "matching timestamp ({detail}, first at line {line})")


@rule("E_PEV_NO_FAST_FIX", WARNING, "e-record")
def r_e_pev_no_fast_fix(doc):
    """After a pilot event the recorder must switch to fast fixing: at least
    PEV_FAST_FIX_COUNT fixes within that many seconds (spec 3.6)."""
    hits = []
    for n, line in doc.of_type("E"):
        if len(line) < 10 or line[7:10] != "PEV":
            continue
        after = [f for f in doc.fixes if f.line > n]
        if not after:
            continue
        window = [f for f in after
                  if f.time - after[0].time < PEV_FAST_FIX_COUNT]
        if len(window) < PEV_FAST_FIX_COUNT:
            hits.append((n, f"{len(window)} fixes"))
    return summarize(*_a("E_PEV_NO_FAST_FIX", WARNING, "e-record"), hits,
                     "{n} PEV event(s) not followed by fast fixing - expected "
                     + str(PEV_FAST_FIX_COUNT) +
                     " fixes in the next " + str(PEV_FAST_FIX_COUNT) +
                     "s, got {detail} (first at line {line})")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -v`
Expected: PASS — 46 rules × 2 + 3 = 95 passing

- [ ] **Step 6: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_rules.py skills/validate-igc-files/scripts/tests/
git commit -m "feat(igc): add C-record declaration and E-record event rules"
```

---

### Task 7: Timing, F-record and L-record rules

The final 7 rules. Five of these are the high-frequency ones the warning tier
exists for.

**Files:**
- Modify: `skills/validate-igc-files/scripts/igc_rules.py` (append)
- Modify: `skills/validate-igc-files/scripts/tests/build_fixtures.py` (extend `MUTATIONS`)

**Interfaces:**
- Consumes: Task 2 framework; `doc.fixes`, `doc.of_type("F")`, `doc.of_type("L")`, `doc.a_record`, `doc.first_g` from Task 1.
- Produces: `F_MAX_INTERVAL_SECONDS`, `B_GAP_TOLERANCE_SECONDS`, `L_PREFIX_REPORT_CAP`, `GENERIC_L_PREFIXES`; 7 entries in `RULES`.

- [ ] **Step 1: Add the fixture mutations**

```python
    # --- Task 7: timing, F and L records ---
    "TIME_OUT_OF_SEQUENCE": lambda L: [
        b(START - 30) if l == b(START + 5) else l for l in L],
    "TIME_DUPLICATE": lambda L: [
        b(START + 4) if l == b(START + 5) else l for l in L],
    "F_RECORDS_NONE": lambda L: drop(L, lambda l: l.startswith("F")),
    "F_RECORDS_ONE": lambda L: drop(L, lambda l: l.startswith("F1102")),
    "F_INTERVAL_LONG": lambda L: [
        "F120130010203040506" if l.startswith("F1102") else l for l in L],
    "B_GAPS": lambda L: [b(START + 40) if l == b(START + 9) else l for l in L],
    "L_BAD_PREFIX": lambda L: replace(
        L, lambda l: l.startswith("LNAV"), "LZZZUNKNOWN PREFIX"),
```

`B_GAPS` moves the last fix to +40s rather than something larger on purpose. The
rule infers the nominal interval from elapsed time over fix count, so an
extravagant gap raises the inferred nominal above the 60s cut-off and the rule
correctly declines to judge the file. At +40s the inferred nominal is 4s and the
32s gap fires. This is the one fixture where a bigger break makes the test weaker.

- [ ] **Step 2: Run the fixture builder**

Run: `cd /home/angel/gliding-ai-skills/skills/validate-igc-files/scripts/tests && python3 build_fixtures.py`
Expected: `wrote baseline + 53 fixtures to .../fixtures`

- [ ] **Step 3: Append the timing and L-record rules**

```python
# --------------------------------------------------------------------------
# Sequence, timing, F records and L records  (sections 9, 12)
# --------------------------------------------------------------------------

F_MAX_INTERVAL_SECONDS = 300
B_GAP_TOLERANCE_SECONDS = 1
L_PREFIX_REPORT_CAP = 20
GENERIC_L_PREFIXES = {"PLT", "OOI", "PFC", "SOF", "FLA", "SEE", "CU:"}


@rule("TIME_OUT_OF_SEQUENCE", ERROR, "timing")
def r_time_out_of_sequence(doc):
    hits = []
    for prev, cur in zip(doc.fixes, doc.fixes[1:]):
        if cur.time < prev.time:
            hits.append((cur.line, _hms(cur.time)))
    return summarize(*_a("TIME_OUT_OF_SEQUENCE", ERROR, "timing"), hits,
                     "{n} fix(es) with a timestamp earlier than the previous "
                     "fix, first {detail} at line {line}")


@rule("TIME_DUPLICATE", WARNING, "timing")
def r_time_duplicate(doc):
    hits = []
    for prev, cur in zip(doc.fixes, doc.fixes[1:]):
        if cur.time == prev.time and cur.valid == "A" and prev.valid == "A":
            hits.append((cur.line, _hms(cur.time)))
    return summarize(*_a("TIME_DUPLICATE", WARNING, "timing"), hits,
                     "{n} duplicate timestamp(s) between consecutive valid "
                     "fixes, first {detail} at line {line}")


def _f_times(doc):
    out = []
    for n, line in doc.of_type("F"):
        if len(line) >= 7 and line[1:7].isdigit():
            hh, mm, ss = int(line[1:3]), int(line[3:5]), int(line[5:7])
            out.append((n, hh * 3600 + mm * 60 + ss))
    return out


@rule("F_RECORDS_NONE", ERROR, "f-record")
def r_f_records_none(doc):
    if not doc.of_type("F"):
        return [Finding("F_RECORDS_NONE", ERROR, "f-record",
                        "no F (satellite constellation) records - regular F "
                        "records are mandatory", None, {})]
    return []


@rule("F_RECORDS_ONE", WARNING, "f-record")
def r_f_records_one(doc):
    if len(doc.of_type("F")) == 1:
        return [Finding("F_RECORDS_ONE", WARNING, "f-record",
                        "only one F record in the whole file", 
                        doc.of_type("F")[0][0], {})]
    return []


@rule("F_INTERVAL_LONG", WARNING, "f-record")
def r_f_interval_long(doc):
    times = _f_times(doc)
    hits = []
    for (_, t0), (n1, t1) in zip(times, times[1:]):
        if t1 - t0 > F_MAX_INTERVAL_SECONDS:
            hits.append((n1, f"{t1 - t0}s"))
    hits.sort(key=lambda h: -int(h[1][:-1]))
    return summarize(*_a("F_INTERVAL_LONG", WARNING, "f-record"), hits,
                     "{n} F record interval(s) longer than " +
                     str(F_MAX_INTERVAL_SECONDS) +
                     "s, longest {detail} ending at line {line}")


@rule("B_GAPS", WARNING, "timing")
def r_b_gaps(doc):
    """Gaps relative to the file's own nominal fix interval.

    The nominal rate is inferred from elapsed time over fix count rather than
    assumed, because recorders log at anything from 1 to 10 seconds. Files whose
    inferred interval exceeds 60s are treated as unmeasurable and skipped.
    """
    if len(doc.fixes) < 3:
        return []
    span = doc.fixes[-1].time - doc.fixes[0].time
    if span <= 0:
        return []
    nominal = round(span / (len(doc.fixes) - 1))
    if nominal <= 0 or nominal > 60:
        return []
    hits = []
    for prev, cur in zip(doc.fixes, doc.fixes[1:]):
        gap = cur.time - prev.time
        if gap > nominal + B_GAP_TOLERANCE_SECONDS:
            hits.append((cur.line, f"{gap}s"))
    hits.sort(key=lambda h: -int(h[1][:-1]))
    return summarize(*_a("B_GAPS", WARNING, "timing"), hits,
                     "{n} gap(s) in B record fixing beyond the nominal " +
                     str(nominal) + "s interval, longest {detail} at line {line}")


@rule("L_BAD_PREFIX", WARNING, "l-record")
def r_l_bad_prefix(doc):
    own = doc.a_record[1:4] if doc.a_record else ""
    limit = doc.first_g or len(doc.lines) + 1
    hits = []
    for n, line in doc.of_type("L"):
        if n >= limit:
            break
        prefix = line[1:4]
        if prefix != own and prefix not in GENERIC_L_PREFIXES:
            hits.append((n, prefix))
        if len(hits) >= L_PREFIX_REPORT_CAP:
            break
    return summarize(*_a("L_BAD_PREFIX", WARNING, "l-record"), hits,
                     "{n} L record(s) with an unrecognised manufacturer prefix, "
                     "first {detail!r} at line {line}")


def _hms(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"
```

`L_BAD_PREFIX` stops counting at `L_PREFIX_REPORT_CAP`. Some corpus files carry
over 900,000 L records, and counting every one costs time for a number nobody
reads.

- [ ] **Step 4: Run tests to verify all 53 rules pass**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_rules.py -v`
Expected: PASS — 53 rules × 2 + 3 = 109 passing

- [ ] **Step 5: Verify the tier split matches the spec**

Run:
```bash
cd /home/angel/gliding-ai-skills/skills/validate-igc-files/scripts
python3 -c "
import igc_rules as r
e=[x.id for x in r.RULES if x.severity=='error']
w=[x.id for x in r.RULES if x.severity=='warning']
print(f'{len(r.RULES)} rules: {len(e)} error, {len(w)} warning')
assert len(r.RULES)==53 and len(e)==30 and len(w)==23, 'tier split does not match the spec'
print('OK')
"
```
Expected: `53 rules: 30 error, 23 warning` then `OK`

- [ ] **Step 6: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_rules.py skills/validate-igc-files/scripts/tests/
git commit -m "feat(igc): add timing, F-record and L-record rules - all 53 rules complete"
```

---

### Task 8: Observations — ENL and GPS anomaly

Measurements, not pass/fail. ENL carries over unchanged; GPS anomaly is new.

**Files:**
- Create: `skills/validate-igc-files/scripts/igc_observations.py`
- Create: `skills/validate-igc-files/scripts/tests/test_observations.py`

**Interfaces:**
- Consumes: `igc_model.parse_lines`, `Fix`.
- Produces: `enl_engine_on(doc) -> dict | None` with keys `max`, `high`, `fixes`, `n_runs`, `longest`; `gps_anomaly(doc) -> dict | None` with keys `events`, `cluster`, `max_knots`, `first`; constants `ENL_ENGINE_ON = 500`, `ENL_MIN_RUN_SECONDS = 30`, `SPOOF_MAX_KNOTS = 300`, `SPOOF_CLUSTER = 5`.

- [ ] **Step 1: Write the failing test**

Create `skills/validate-igc-files/scripts/tests/test_observations.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_observations.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'igc_observations'`

- [ ] **Step 3: Write the observations module**

Create `skills/validate-igc-files/scripts/igc_observations.py`:

```python
"""Per-file measurements that are reported but never affect conformance.

These answer 'what should a scrutineer look at?' rather than 'is this file
well formed?', so they are deliberately kept out of the rule registry.
"""

import math

# A running engine reads 700+; aerotow noise sits around 400-500. Isolated
# high readings are radio calls, gear warnings or vario beeps, so engine-on is
# only declared for a continuous run - a bare threshold flags ~75% of pure
# glider files.
ENL_ENGINE_ON = 500
ENL_MIN_RUN_SECONDS = 30

# Above this speed between consecutive valid fixes the position data is not
# physically plausible. A handful of events is flight-recorder clock tolerance;
# a cluster suggests GPS jamming or spoofing.
SPOOF_MAX_KNOTS = 300
SPOOF_CLUSTER = 5

_EARTH_RADIUS_NM = 3440.065          # nautical miles
# Below this coordinate delta no pair can exceed SPOOF_MAX_KNOTS at a 1s
# interval, so the trigonometry can be skipped. Keeps the sweep cheap across
# ~19,000 fixes per file.
_DELTA_PREFILTER_DEG = 0.05


def _hms(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def enl_engine_on(doc):
    """Return engine-noise stats when the file shows a sustained run, else None."""
    values = [(f.time, int(f.ext["ENL"]))
              for f in doc.fixes
              if f.ext.get("ENL", "").isdigit()]
    if not values:
        return None

    runs, start, end = [], None, None
    high = 0
    for t, v in values:
        if v > ENL_ENGINE_ON:
            high += 1
            if start is None:
                start = t
            end = t
        elif start is not None:
            runs.append((start, end))
            start = end = None
    if start is not None:
        runs.append((start, end))

    long_runs = [(s, e) for s, e in runs if e - s >= ENL_MIN_RUN_SECONDS]
    if not long_runs:
        return None

    s, e = max(long_runs, key=lambda r: r[1] - r[0])
    return {
        "max": max(v for _, v in values),
        "high": high,
        "fixes": len(values),
        "n_runs": len(long_runs),
        "longest": f"{_hms(s)}-{_hms(e)} UTC ({e - s}s)",
    }


def _distance_nm(lat1, lon1, lat2, lon2):
    """Great-circle distance on the IGC sphere, which the rules document
    permits in place of Vincenty."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * _EARTH_RADIUS_NM * math.asin(min(1.0, math.sqrt(a)))


def gps_anomaly(doc):
    """Return groundspeed-anomaly stats, or None when the track is plausible."""
    valid = [f for f in doc.fixes if f.valid == "A"]
    events, max_knots, first = 0, 0.0, None

    for prev, cur in zip(valid, valid[1:]):
        dt = cur.time - prev.time
        if dt <= 0:
            continue
        if (abs(cur.lat - prev.lat) < _DELTA_PREFILTER_DEG * dt
                and abs(cur.lon - prev.lon) < _DELTA_PREFILTER_DEG * dt):
            continue
        knots = _distance_nm(prev.lat, prev.lon, cur.lat, cur.lon) / (dt / 3600.0)
        if knots > SPOOF_MAX_KNOTS:
            events += 1
            if knots > max_knots:
                max_knots = knots
            if first is None:
                first = _hms(cur.time)

    if not events:
        return None
    return {
        "events": events,
        "cluster": events >= SPOOF_CLUSTER,
        "max_knots": round(max_knots),
        "first": first,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_observations.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/igc_observations.py skills/validate-igc-files/scripts/tests/test_observations.py
git commit -m "feat(igc): add ENL engine-on and GPS anomaly observations"
```

---

### Task 9: CLI and text reporting

**Files:**
- Modify: `skills/validate-igc-files/scripts/validate_igc_files.py` (full rewrite)
- Create: `skills/validate-igc-files/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `igc_model.parse`, `igc_rules.run_all`, `igc_rules.RULES`, `igc_observations.enl_engine_on`, `igc_observations.gps_anomaly`.
- Produces: `scan(root) -> list[dict]` where each dict has `path` (relative str), `findings` (list of `Finding`), `enl`, `gps`, `conform` (bool); `report_text(root, results, show_warnings, verbose) -> str`; `main(argv=None) -> int`.

- [ ] **Step 1: Write the failing test**

Create `skills/validate-igc-files/scripts/tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_cli.py -v`
Expected: FAIL — the old script has no `--warnings` flag and treats non-ASCII as
an error, so `test_warning_only_file_still_conforms` and
`test_warnings_flag_shows_per_file_detail` fail

- [ ] **Step 3: Rewrite the CLI**

Replace `skills/validate-igc-files/scripts/validate_igc_files.py` entirely:

```python
#!/usr/bin/env python3
"""Scan a directory recursively for .igc/.IGC files and validate each against
the FAI/IGC flight-log format.

References:
  /home/angel/src/formulas/IGCformat.md
  /home/angel/src/formulas/IGC_Validation_Rules.md

Findings come in two tiers. ERROR means the file's integrity or scoring validity
is in question and sets exit code 1. WARNING is a spec deviation worth knowing
about that does not invalidate the file; warnings are collapsed into a tally by
default and expanded per file with --warnings.

Separately, two observations are reported that are never conformance failures:
sustained ENL (engine noise) and implausible groundspeed suggesting GPS
jamming or spoofing.

Usage:
    python3 validate_igc_files.py <directory> [--warnings] [--verbose] [--json]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from igc_model import parse
from igc_rules import run_all, ERROR, WARNING
from igc_observations import (
    enl_engine_on, gps_anomaly, ENL_ENGINE_ON, ENL_MIN_RUN_SECONDS,
    SPOOF_MAX_KNOTS,
)


def scan(root):
    """Validate every IGC file under root. Returns one dict per file."""
    files = sorted(p for p in root.rglob("*")
                   if p.is_file() and p.suffix.lower() == ".igc")
    results = []
    for path in files:
        doc = parse(path)
        findings = run_all(doc)
        results.append({
            "path": str(path.relative_to(root)),
            "findings": findings,
            "enl": enl_engine_on(doc),
            "gps": gps_anomaly(doc),
            "conform": not any(f.severity == ERROR for f in findings),
        })
    return results


def _by_severity(findings, severity):
    return [f for f in findings if f.severity == severity]


def report_text(root, results, show_warnings=False, verbose=False):
    out = []

    for r in results:
        errors = _by_severity(r["findings"], ERROR)
        warnings = _by_severity(r["findings"], WARNING)
        if errors:
            out.append(f"FAIL {r['path']}")
            out.extend(f"     - {f.message}" for f in errors)
        elif verbose:
            out.append(f"OK   {r['path']}")
        if show_warnings and warnings:
            out.append(f"WARN {r['path']}")
            out.extend(f"     - {f.message}" for f in warnings)

    if not show_warnings:
        tally = {}
        affected = 0
        for r in results:
            warnings = _by_severity(r["findings"], WARNING)
            if warnings:
                affected += 1
            for f in warnings:
                tally[f.rule_id] = tally.get(f.rule_id, 0) + 1
        if tally:
            out.append("")
            out.append(f"WARNINGS (do not affect conformance) — "
                       f"{affected} file(s) affected")
            first_message = {}
            for r in results:
                for f in _by_severity(r["findings"], WARNING):
                    first_message.setdefault(f.rule_id, f.message)
            for rule_id, count in sorted(tally.items(), key=lambda kv: -kv[1]):
                out.append(f"  {count:5d}  {_headline(first_message[rule_id])}")
            out.append("         (run with --warnings for per-file detail)")

    enl = [r for r in results if r["enl"]]
    if enl:
        enl.sort(key=lambda r: -_run_seconds(r["enl"]["longest"]))
        out.append("")
        out.append(f"ENL engine-on evidence (ENL > {ENL_ENGINE_ON} sustained "
                   f">= {ENL_MIN_RUN_SECONDS}s) in {len(enl)} file(s):")
        for r in enl:
            e = r["enl"]
            out.append(f"ENL  {r['path']}: max ENL {e['max']}, "
                       f"{e['n_runs']} run(s), longest {e['longest']}, "
                       f"{e['high']}/{e['fixes']} fixes > {ENL_ENGINE_ON}")

    gps = [r for r in results if r["gps"]]
    if gps:
        gps.sort(key=lambda r: (not r["gps"]["cluster"], -r["gps"]["events"]))
        out.append("")
        out.append(f"GPS anomaly (groundspeed > {SPOOF_MAX_KNOTS} kt) in "
                   f"{len(gps)} file(s):")
        for r in gps:
            g = r["gps"]
            flag = ("CLUSTER, possible jamming/spoofing — other findings in "
                    "this file may be compromised" if g["cluster"]
                    else "isolated, consistent with recorder clock tolerance")
            out.append(f"GPS  {r['path']}: {g['events']} event(s) — {flag}; "
                       f"max {g['max_knots']} kt at {g['first']} UTC")

    bad = sum(1 for r in results if not r["conform"])
    out.append("")
    out.append(f"Scanned {len(results)} IGC file(s) under {root}: "
               f"{len(results) - bad} conform, {bad} do not.")
    return "\n".join(out)


_HEADLINE_CUTS = (" (first at line", ", first", " (line", " ending at line",
                  ", longest", " at line")


def _headline(message):
    """Strip the per-file specifics so the tally reads as one line per rule."""
    for cut in _HEADLINE_CUTS:
        message = message.split(cut)[0]
    return message


def _run_seconds(longest):
    """Pull the duration out of a '10:00:00-10:05:00 UTC (300s)' string."""
    try:
        return int(longest.rsplit("(", 1)[1].rstrip("s)"))
    except (IndexError, ValueError):
        return 0


def report_json(root, results):
    tally = {}
    for r in results:
        for f in _by_severity(r["findings"], WARNING):
            tally[f.rule_id] = tally.get(f.rule_id, 0) + 1
    bad = sum(1 for r in results if not r["conform"])
    return json.dumps({
        "root": str(root),
        "scanned": len(results),
        "conform": len(results) - bad,
        "non_conform": bad,
        "warning_tally": tally,
        "files": [
            {
                "path": r["path"],
                "conform": r["conform"],
                "findings": [
                    {
                        "rule": f.rule_id,
                        "severity": f.severity,
                        "category": f.category,
                        "message": f.message,
                        "line": f.line,
                        "data": f.data,
                    }
                    for f in r["findings"]
                ],
                "enl": r["enl"],
                "gps_anomaly": r["gps"],
            }
            for r in results
        ],
    }, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Validate IGC flight logs in a directory tree.")
    ap.add_argument("directory",
                    help="directory to scan recursively for .igc/.IGC files")
    ap.add_argument("--warnings", action="store_true",
                    help="expand warnings per file instead of tallying them")
    ap.add_argument("--verbose", action="store_true",
                    help="also list conforming files")
    ap.add_argument("--json", action="store_true",
                    help="emit structured findings instead of the text report")
    args = ap.parse_args(argv)

    root = Path(args.directory)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    results = scan(root)
    if not results:
        print(f"No .igc/.IGC files found under {root}")
        return 0

    if args.json:
        print(report_json(root, results))
    else:
        print(report_text(root, results, args.warnings, args.verbose))

    return 1 if any(not r["conform"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_cli.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Smoke-test against the real corpus**

Run: `cd /home/angel && python3 gliding-ai-skills/skills/validate-igc-files/scripts/validate_igc_files.py IGCfiles/egc2026_2026-07-13`
Expected: a FAIL block per erroring file, a WARNINGS tally, the ENL section with
4 files, and a summary line. No traceback.

- [ ] **Step 6: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/validate_igc_files.py skills/validate-igc-files/scripts/tests/test_cli.py
git commit -m "feat(igc): rewrite CLI with two-tier reporting, --warnings and --json"
```

---

### Task 10: JSON output test

The JSON contract is what the report generator depends on, so it gets its own
tests rather than riding on the CLI smoke test.

**Files:**
- Create: `skills/validate-igc-files/scripts/tests/test_json_output.py`

**Interfaces:**
- Consumes: `validate_igc_files.scan`, `validate_igc_files.report_json`.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run the test**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_json_output.py -v`
Expected: PASS, 4 tests.

These are characterisation tests rather than TDD — Task 9 already built
`report_json`, and their job is to pin the contract so a later refactor cannot
silently break the report generator that consumes it. If any fails, the bug is in
Task 9's `report_json`, not in the test.

- [ ] **Step 3: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/tests/test_json_output.py
git commit -m "test(igc): pin the --json output contract"
```

---

### Task 11: Corpus regression test

**Files:**
- Create: `skills/validate-igc-files/scripts/tests/test_corpus.py`
- Create: `skills/validate-igc-files/scripts/tests/corpus_baseline.json`

**Interfaces:**
- Consumes: `validate_igc_files.scan`.
- Produces: nothing new.

- [ ] **Step 1: Write the regression test**

```python
"""Regression against the real 308-file competition corpus.

Skipped when the corpus is absent, so the suite stays portable. Its job is to
catch a rule that starts firing far more or far less often after a refactor -
the failure mode that would quietly ruin the report.
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from validate_igc_files import scan

CORPUS = Path("/home/angel/IGCfiles")
BASELINE = HERE / "corpus_baseline.json"

pytestmark = pytest.mark.skipif(
    not CORPUS.is_dir(), reason="calibration corpus not present")


@pytest.fixture(scope="module")
def actual():
    results = scan(CORPUS)
    counts = {}
    for r in results:
        for f in r["findings"]:
            counts[f.rule_id] = counts.get(f.rule_id, 0) + 1
    return {
        "scanned": len(results),
        "conform": sum(1 for r in results if r["conform"]),
        "rule_file_counts": counts,
    }


@pytest.fixture(scope="module")
def expected():
    return json.loads(BASELINE.read_text())


def test_scanned_count_unchanged(actual, expected):
    assert actual["scanned"] == expected["scanned"]


def test_conformance_unchanged(actual, expected):
    assert actual["conform"] == expected["conform"]


def test_no_rule_starts_flooding(actual, expected):
    """A warning firing on more than half the corpus is a calibration failure."""
    half = actual["scanned"] // 2
    grew = {
        rule_id: (expected["rule_file_counts"].get(rule_id, 0), count)
        for rule_id, count in actual["rule_file_counts"].items()
        if count > half and count > expected["rule_file_counts"].get(rule_id, 0)
    }
    assert grew == {}, f"rules now firing on >50% of the corpus: {grew}"


def test_per_rule_counts_match(actual, expected):
    diffs = {
        rule_id: (expected["rule_file_counts"].get(rule_id, 0), count)
        for rule_id, count in actual["rule_file_counts"].items()
        if expected["rule_file_counts"].get(rule_id, 0) != count
    }
    dropped = {
        rule_id: (count, 0)
        for rule_id, count in expected["rule_file_counts"].items()
        if rule_id not in actual["rule_file_counts"]
    }
    assert {**diffs, **dropped} == {}, "per-rule hit counts changed"
```

- [ ] **Step 2: Generate the baseline snapshot**

```bash
cd /home/angel/gliding-ai-skills/skills/validate-igc-files/scripts
python3 -c "
import json, sys
from pathlib import Path
sys.path.insert(0, '.')
from validate_igc_files import scan
results = scan(Path('/home/angel/IGCfiles'))
counts = {}
for r in results:
    for f in r['findings']:
        counts[f.rule_id] = counts.get(f.rule_id, 0) + 1
snap = {
    'scanned': len(results),
    'conform': sum(1 for r in results if r['conform']),
    'rule_file_counts': dict(sorted(counts.items())),
}
Path('tests/corpus_baseline.json').write_text(json.dumps(snap, indent=2) + '\n')
print(json.dumps(snap, indent=2))
"
```

- [ ] **Step 3: Verify the snapshot against the spec before trusting it**

Read the printed JSON and check it against the spec's calibration table. These
must hold, or a rule is misimplemented and the snapshot would enshrine the bug:

- `scanned` is 308
- `conform` is 273 (so 35 non-conformant)
- `I_MISSING_EXT` is 29
- `H_DTM_NOT_WGS84` is 14
- `I_PTR_CHAIN`, `I_LEN_MISMATCH`, `B_LEN_MISMATCH`, `H_FTY_NO_COMMA` are each 3
- `C_FLIGHTDATE_MISMATCH` is 4
- `CHAR_NON_ASCII` is 65, `CHAR_EMPTY_LINE` is 9
- `A_SHORT_SERIAL` and `A_BAD_SEPARATOR` are each 245
- `F_INTERVAL_LONG` is 262, `ENL_MOP_MIN_LOW` is 250, `H_FTY_NOT_IGC` is 250
- `B_GAPS` is 114, `TIME_DUPLICATE` is 93, `B_V_FLAG_NONZERO_ALT` is 44
- `L_BAD_PREFIX` is 25, `H_DTE_NO_LITERAL` is 17, `ENL_MOP_ALL_ZERO` is 12
- `G_MISSING`, `G_TRAILING_RECORDS`, `B_MALFORMED`, `TIME_OUT_OF_SEQUENCE` are
  each absent or 0

If a count is off, fix the rule and regenerate — do not adjust the expectation.
`H_MISSING_MANDATORY` has no predicted value (the spec measured CM2 and FRS
separately, at 14 and 22, without computing their union); anything from 22 to 36
is consistent. Record whatever it is.

- [ ] **Step 4: Run the regression test**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/test_corpus.py -v`
Expected: PASS, 4 tests

- [ ] **Step 5: Run the whole suite**

Run: `cd /home/angel/gliding-ai-skills && python3 -m pytest skills/validate-igc-files/scripts/tests/ -v`
Expected: PASS — 109 rule tests + 6 model + 6 observations + 6 CLI + 4 JSON + 4 corpus

- [ ] **Step 6: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/scripts/tests/test_corpus.py skills/validate-igc-files/scripts/tests/corpus_baseline.json
git commit -m "test(igc): add corpus regression pinned to measured hit counts"
```

---

### Task 12: Update SKILL.md, the spec, and deploy

**Files:**
- Modify: `skills/validate-igc-files/SKILL.md`
- Modify: `docs/superpowers/specs/2026-08-01-igc-validation-rules-design.md`
- Sync: `~/.claude/skills/validate-igc-files/`

**Interfaces:**
- Consumes: the finished implementation.
- Produces: nothing.

- [ ] **Step 1: Rewrite the SKILL.md body**

Replace everything from `## Checks performed` through the end of
`## ENL engine-on reporting` with:

```markdown
## Two severity tiers

Findings come in two tiers, calibrated against 308 real competition files so the
default report stays readable.

**ERROR** — the file's integrity or scoring validity is in question. These fail
conformance and set exit code 1: missing or malformed A/H/I/J/M records, a
missing mandatory header or B-record extension, broken I-record column pointers,
a wrong-length B or K record, a task declaration inconsistent with the flight
date, a missing G security record, records after the G record, out-of-sequence
timestamps, and a dead ENL or MOP sensor.

**WARNING** — a real spec deviation that does not invalidate the file. Always
reported, never fails: non-ASCII characters, empty lines, LXNav's 3-character
serial and `_` separator, F-record intervals over 5 minutes, gaps in fixing,
duplicate timestamps, a non-zero GNSS altitude on an invalid fix, unrecognised
three-letter codes, and unregistered L-record prefixes.

Warnings are collapsed into a per-rule tally by default. Pass `--warnings` to see
them per file.

Several of these are classified as errors in `IGC_Validation_Rules.md` but fire
on most valid files — LXNav's A-record format alone accounts for 245 of 308
files. Treating them as errors would fail ~98% of every contest's logs. The same
reasoning keeps the spec's 76-character line limit unenforced.

## Options

| Flag | Effect |
|------|--------|
| *(none)* | Errors per file, warnings as a tally, observation sections, summary |
| `--warnings` | Expand warnings per file |
| `--verbose` | Also list conforming files |
| `--json` | Structured findings for report generation |

## Observations — never conformance failures

**ENL engine-on** — ENL > 500 sustained for at least 30 continuous seconds. The
sustain requirement matters: isolated high-ENL fixes are radio calls, gear
warnings or vario beeps, and a raw threshold flags ~75% of pure-glider files.
Aerotow reads 400–500; an onboard engine reads 700+.

**GPS anomaly** — groundspeed above 300 kt between consecutive valid fixes. One
to four events is flight-recorder clock tolerance; five or more is flagged as a
cluster suggesting jamming or spoofing, in which case other findings in that file
may be unreliable. Relevant for contests in regions with active GPS interference.

Both are findings to investigate, not failures.
```

- [ ] **Step 2: Update the report-generation guidance in SKILL.md**

Replace step 3 of `## Procedure` with:

```markdown
3. Report to the user: the summary counts, then the non-conforming files grouped
   by failure type so patterns stand out — e.g. every file from one logger model
   missing the same record. Then the ENL engine-on files, most-sustained first,
   then any GPS anomalies. Do not list conforming files unless asked.

4. When the user wants a written report, re-run with `--json` and build
   `reports/<comp>_IGC_conformance_report.md` from the structured output rather
   than from the printed text. Group by failure type, put serious findings first,
   and keep the ENL and GPS tables at the end, matching the existing
   `24th-fai-egc_IGC_conformance_report.md` layout.
```

- [ ] **Step 3: Update the "deliberately not checked" note in SKILL.md**

```markdown
Deliberately **not** checked: the spec's 76-character line limit. Virtually every
modern IGC-approved recorder exceeds it (I/B records with extensions, L records),
so it would flag 100% of real files and drown the true findings. For the same
reason, "no MOP extension declared" is not reported at all — it would fire on 245
of 308 files while telling you nothing.
```

- [ ] **Step 4: Reconcile the spec with the implementation**

In `docs/superpowers/specs/2026-08-01-igc-validation-rules-design.md`:

- Change `52 rules: 29 ERROR, 23 WARNING` to `53 rules: 30 ERROR, 23 WARNING`.
- Add `C_ZERO_DECL_TIME` to the ERROR table: *"Declaration time is zero or
  undecodable | 0"*.
- Delete the **Spec Addendum** section from the plan's rationale by noting in the
  spec that the rule was added on 2026-08-01 to close a gap against §8 of the
  rules document.
- Add `igc_observations.py` to the file-structure listing.
- Replace the `fixtures/<rule_id>.igc` line with a note that fixtures are
  generated by `build_fixtures.py` from a baseline plus one mutation per rule,
  and committed so failures stay inspectable.

- [ ] **Step 5: Deploy to the live skill directory**

```bash
rsync -a --delete \
  /home/angel/gliding-ai-skills/skills/validate-igc-files/ \
  /home/angel/.claude/skills/validate-igc-files/
python3 /home/angel/.claude/skills/validate-igc-files/scripts/validate_igc_files.py \
  /home/angel/IGCfiles/egc2026_2026-07-13
```
Expected: the documented invocation path works and prints the two-tier report.

- [ ] **Step 6: Full verification**

```bash
cd /home/angel/gliding-ai-skills
python3 -m pytest skills/validate-igc-files/scripts/tests/ -q
python3 skills/validate-igc-files/scripts/validate_igc_files.py /home/angel/IGCfiles | tail -3
```
Expected: all tests pass; the summary reads `273 conform, 35 do not`.

- [ ] **Step 7: Commit**

```bash
cd /home/angel/gliding-ai-skills
git add skills/validate-igc-files/SKILL.md docs/superpowers/specs/
git commit -m "docs(igc): document two-tier validation, new flags and GPS anomalies"
```

---

## Success Criteria

1. `python3 -m pytest skills/validate-igc-files/scripts/tests/` passes, with a fixture for every registered rule.
2. `validate_igc_files.py /home/angel/IGCfiles` reports 273 conform / 35 non-conform.
3. Every failing file fails on a structural rule — none fails solely on non-ASCII characters or empty lines.
4. `--json` output matches the contract in `test_json_output.py`.
5. `python3 ~/.claude/skills/validate-igc-files/scripts/validate_igc_files.py <dir>` works unchanged.
6. No third-party runtime dependencies.
7. The registry holds exactly 53 rules: 30 error, 23 warning.
