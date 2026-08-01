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
