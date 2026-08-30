# Data Refresh Checklist

Status of every input that has to be fetched by hand. Last refreshed **August 30, 2026**
(65 days to the election).

The four economic inputs feed `national_environment_shift()` in
`backend/app/model/environment.py`, currently **D+5.10**. That shift is added to all 35
races, so an error here moves the whole map rather than one state.

| Input | Coefficient | Current value | Contribution | Status |
|---|---|---|---|---|
| Presidential approval | 0.12 / net approval pt | net −17.64 | D+2.12 | ✅ through 8/28/26 |
| Consumer sentiment | 0.04 / pt below 85.0 | 51.7 | D+1.33 | ✅ Aug final |
| GDP growth | 0.3 / pt above 2.0% | 1.5% | D+0.15 | ✅ Q2 second estimate |
| Unemployment | none — display only | 4.1% | — | ✅ July |
| Base midterm penalty | — | — | D+1.50 | constant |

---

## ✅ Done in this refresh

**Presidential approval** — new NYT bulk export in place, 989 polls running through
**8/28/26** (was 8/3/26). 896 fall inside the 540-day window and carry weight. Net approval
moved −18.16 → **−17.64**, slightly *less* favourable to Democrats. The previous file is
archived at `backend/app/data/archive/potus-approval-2026-08-04.csv` (verified byte-identical
to the version it replaced). No code or JSON edits were needed — `environment.py` reads this
file live at runtime.

**Consumer sentiment** — updated 55.2 → **51.7**, the University of Michigan August final
released 8/28/26, down about 6% from July and about 11% below a year ago. Taken from the
Surveys of Consumers monthly series at
<https://www.sca.isr.umich.edu/files/tbmics.csv> and cross-checked against the headline on
<https://www.sca.isr.umich.edu/>. This is the largest single change in the refresh:
sentiment's contribution rose D+1.19 → **D+1.33**.

**GDP** — no value change. The BEA Q2 2026 second estimate (released 8/26/26) left real GDP
growth at **1.5% annualized**, with consumer spending revised up to 3.4%. Only the source
note in `environment.json` was updated from "advance" to "second estimate."

**Unemployment** — updated 4.2% → **4.1%** (BLS July Employment Situation, released 8/7/26).
Display only: `national_environment_shift()` never reads it. Note the decline is not good
news — payrolls fell 23k, May and June were revised down 103k combined, and participation
dropped to 61.4%.

**Net effect:** national environment D+5.02 → **D+5.10**. D control probability moved ~42%
→ ~42%. No race changed rating.

---

## ⚠️ One correction

`backend/app/data/ff202607.pdf` is the **July** report, not August — the `202607` in the
filename is the year-month. Its data table runs Jul 2025 → Jul 2026 and ends at 55.2, which
is the value the model already had. The August figure came from the monthly CSV instead.

For next time, the reliable path is the monthly series rather than the per-month PDF:

- **CSV (best):** <https://www.sca.isr.umich.edu/files/tbmics.csv> — full Index of Consumer
  Sentiment history, one row per month, always current.
- Per-month reports are `ff<YYYYMM>.pdf`, so the August one would be `ff202608.pdf`.

---

## Coming up

| Date | Release | Matters? |
|---|---|---|
| **Sept 4** | BLS Employment Situation, August | display only |
| **Sept 11** | U. Michigan September **preliminary** | yes — sentiment |
| Late Sept | BEA Q2 third estimate | rarely moves |
| Early Oct | U. Michigan September final | yes — sentiment |
| **Late Oct** | BEA Q3 **advance** estimate | yes — last GDP print before the election |

Approval polling should be re-dropped roughly weekly from here. The average uses a 21-day
half-life, so a file more than about two weeks stale is materially discounting its own
freshest data.

---

## Polling files

**Senate** (`senate.csv`) and **gubernatorial** (`governors.csv`) NYT bulk exports. Archive
the current file before overwriting; both are curated by hand — see the pipeline notes in
`README.md`.

Two things specifically worth a new Senate drop:

- **South Carolina** is the most fragile input in the model. Its entire average is one
  D-sponsored poll showing 41-41 in an R+11 seat, and that poll alone is the difference
  between Safe R and Lean R.
- **Massachusetts (Sept 1)** and **New Hampshire (Sept 8)** primaries resolve within days.
  Once they do, the losing candidate's matchups must be re-flagged `no` in `polls.csv`, the
  way the Craig, Beaudion, Vindman and Priest matchups already were.

---

## Not needed

- **Cook PVI** — values in `races_2026.json` and the reference table in
  `backend/app/model/governors.py` only change after a presidential election.
- **Candidate quality scores** — hand-set in `races_2026.json`; revisit only when a nominee
  changes.
