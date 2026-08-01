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
    # --- Task 7: timing, F and L records ---
    "TIME_OUT_OF_SEQUENCE": lambda L: [
        b(START - 30) if l == b(START + 5) else l for l in L],
    "TIME_DUPLICATE": lambda L: [
        b(START + 4) if l == b(START + 5) else l for l in L],
    "F_RECORDS_NONE": lambda L: drop(L, lambda l: l.startswith("F")),
    "F_RECORDS_ONE": lambda L: drop(L, lambda l: l.startswith("F1102")),
    "F_INTERVAL_LONG": lambda L: [
        "F120130010203040506" if l.startswith("F1102") else l for l in L],
    # +40s not something larger on purpose: the rule infers the nominal interval
    # from elapsed time over fix count, so an extravagant gap raises the inferred
    # nominal past the 60s cut-off and the rule correctly declines to judge.
    "B_GAPS": lambda L: [b(START + 40) if l == b(START + 9) else l for l in L],
    "L_BAD_PREFIX": lambda L: replace(
        L, lambda l: l.startswith("LNAV"), "LZZZUNKNOWN PREFIX"),
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
