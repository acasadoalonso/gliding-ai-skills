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
