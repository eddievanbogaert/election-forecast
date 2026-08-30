# Data Refresh Checklist

Everything the forecast needs that has to be fetched by hand, as of **August 30, 2026**
(65 days to the election). Ordered by how much it moves the model.

The four economic inputs feed `national_environment_shift()` in
`backend/app/model/environment.py`, which currently reads **D+5.02**. That shift is added
to every one of the 35 races, so an error here moves the whole map, not one state.

| Input | Model coefficient | Current value | Age |
|---|---|---|---|
| Presidential approval | 0.12 pts per net approval pt | net −18.16 → D+2.18 | newest poll 8/3/26 |
| Consumer sentiment | 0.04 pts per pt below 85.0 | 55.2 → D+1.19 | July final |
| GDP growth | 0.3 pts per pt above 2.0% | 1.5% → D+0.15 | Q2 advance |
| Unemployment | none — display only | 4.2% | June |

---

## 1. Presidential approval polls — **highest priority**

**Get:** a fresh NYT bulk export of presidential approval polling, saved over
`backend/app/data/potus-approval.csv`.

**Why it matters most:** this is the single largest environment component (D+2.18 of the
D+5.02 total) and the only one the model recomputes live at runtime. Drop the file in and
the forecast picks it up on the next cache cycle — no code or JSON edits needed.

**Why it is stale:** the newest poll in the file ends **8/3/26 — 27 days ago**. The average
uses a 21-day half-life, so the freshest data we have is already weighted below half. The
file has 953 polls but only 52 ending since July 1, meaning the recent window that actually
drives the number is thin.

**Before overwriting:** move the current file to
`backend/app/data/archive/potus-approval-2026-08-30.csv`. The archive is how each new drop
gets diffed against the last.

---

## 2. Consumer sentiment — August final

**Get:** the University of Michigan Surveys of Consumers August 2026 **final** reading, from
<https://data.sca.isr.umich.edu/>.

**Update:** `economy.consumer_sentiment` and `economy.consumer_sentiment_source` in
`backend/app/data/environment.json`.

**Note:** while researching this I saw the August final reported as **51.7**, down 3.5 points
from July's 55.2, with the preliminary at 51.0 and year-ahead inflation expectations easing
to 4.0%. That came from secondary coverage, not the U. Michigan release itself, so please
confirm it at the primary source before applying. If 51.7 holds, the sentiment contribution
goes from D+1.19 to **D+1.33** and the national environment from D+5.02 to about **D+5.16**
— a real move, and in the Democrats' direction.

---

## 3. GDP — **probably no change needed**

**Get:** BEA Q2 2026 **second** estimate, released 8/26/26
(<https://www.bea.gov/data/gdp/gross-domestic-product>).

**Note:** the second estimate appears to have left real GDP growth **unchanged at 1.5%
annualized**, with consumer spending revised up to 3.4%. If that is right, the model's
`gdp_growth_annualized` is already correct and only `gdp_source` needs its wording updated
from "advance estimate" to "second estimate." Worth confirming, but do not expect the
forecast to move.

**Next release that would matter:** Q2 third estimate (late September) and the Q3 advance
estimate (late October) — the last GDP print before the election.

---

## 4. Unemployment — cosmetic only

**Get:** BLS Employment Situation for July 2026, released 8/7/26
(<https://www.bls.gov/news.release/empsit.nr0.htm>).

**Note:** reporting on that release has the unemployment rate at **4.1%**, down from 4.2%,
though payrolls fell 23,000 and May/June were revised down 103,000 combined.

**Impact: none.** `unemployment_rate` is carried in `environment.json` and echoed in the API
response, but `national_environment_shift()` never reads it — the shift is built only from
the base midterm penalty, approval, GDP and sentiment. Update it for accuracy of the
displayed figure, not because it changes the forecast. If you want unemployment to actually
count, that is a model change, not a data refresh.

---

## 5. Senate and gubernatorial polling

**Get:** fresh NYT bulk exports over `backend/app/data/senate.csv` and
`backend/app/data/governors.csv`, archiving the current ones first.

Both are curated by hand — see the pipeline notes in `README.md`. Two things specifically
worth a new Senate drop:

- **South Carolina** rests on a single D-sponsored poll taken before the nominee was
  certified. It is currently the most fragile input in the model: that one poll is the
  entire difference between Safe R and Lean R there.
- **Massachusetts (Sept 1)** and **New Hampshire (Sept 8)** primaries resolve within days.
  Once they do, the losing candidate's matchups have to be re-flagged `no` in `polls.csv`,
  the way the Craig, Beaudion, Vindman and Priest matchups already were.

---

## Not needed

- **Cook PVI** — the values in `races_2026.json` and the reference table in
  `backend/app/model/governors.py` are current and only change after a presidential election.
- **Candidate quality scores** — hand-set in `races_2026.json`; revisit only when a nominee
  changes.
