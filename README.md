# gliding-ai-skills

Claude Code skills and Python tooling for gliding-championship workflows:
generating SeeYou Competition files from Sailplane Grand Prix data, and
validating pilot IGC ranking-list IDs in competition entry sheets.

## What's inside

| Path | Contents |
|---|---|
| `.claude/skills/gen_cucx_from_sgp/` | Skill: build a SeeYou `.cucx` from an SGP competition (includes a `.cucx` format reference) |
| `.claude/skills/validate-igc-id/` | Skill: validate the `Igc id` column of an entry spreadsheet against the IGC Ranking database |
| `tools/` | The `.cucx` generator — CLI (`make_cucx.py`) and modules, plus a pytest suite with recorded SGP fixtures |
| `SGP/norway_sgp.cucx` | Example generated output (SGP Norway 2026) |
| `docs/superpowers/` | Design spec and implementation plan for the cucx generator |
| `.claude/projects/.../memory/` | Claude memory notes documenting the skills and their gotchas |

## Skills

### gen_cucx_from_sgp

Generates a SeeYou Competition `.cucx` file from a Sailplane Grand Prix
competition on [crosscountry.aero](https://www.crosscountry.aero): pilots,
tasks, turnpoints and results, with the task definitions carried in the
embedded `.cup` waypoint file. In Claude Code just ask, e.g. *"generate the
cucx for SGP competition 93"*; the skill prompts for the competition number
and the day (a specific day or `ALL`).

Direct CLI:

```bash
python3 tools/make_cucx.py --comp-id 93 --day ALL --out norway_sgp_2026.cucx
```

The generator itself is pure standard library. Data is fetched through
`src/SGP/sgp_api.py` from the
[SGP.Aero.AI](https://github.com/acasadoalonso/SGP.Aero.AI) project, which
must be present in the workspace (the test suite runs without it, using the
recorded fixtures in `tools/tests/fixtures/`).

`docs/superpowers/` and `.claude/skills/gen_cucx_from_sgp/references/cucx_format.md`
document the reverse-engineered `.cucx` format: a ZIP holding a SQLite
`contest.db` (radian coordinates, content hash) plus the registered `.cup`
contest file.

### validate-igc-id

Validates each entrant's IGC ranking-list ID (the `Igc id` column) against the
official IGC Ranking database REST API
(`https://rankingdata.fai.org/rest/api/rlpilot?id=N`). An ID is only accepted
when it exists **and** the registered pilot's name matches the row —
accent-, hyphen- and name-order-tolerant. Takes a local `.xlsx` or a Google
Sheets URL (converted to an xlsx export automatically).

```bash
python3 .claude/skills/validate-igc-id/scripts/validate_igc_ids.py \
  --excel "<entries.xlsx or Google Sheets URL>"
```

Outputs a markdown report (`reports/<stem>_igc_id_validation.md`) with
valid / wrong / not-supplied sections, and a copy of the workbook with the
`Igc id` cells coloured green (valid) or red (wrong). Requires `openpyxl`.

## Running the tests

```bash
pip install pytest
pytest tools/tests/
```

The suite covers the cucx geometry conversion, SQLite schema, content hash,
packaging, and an end-to-end generation from the recorded competition-93
fixtures — no network needed.

## License

[MIT](LICENSE)
