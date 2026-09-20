# Data Refresh Checklist

Status of every input that has to be fetched by hand. Last refreshed **September 20, 2026**
(44 days to the election).

The four economic inputs feed `national_environment_shift()` in
`backend/app/model/environment.py`, currently **D+5.14**. That shift is added to all 35
races, so an error here moves the whole map rather than one state.

| Input | Coefficient | Current value | Contribution | Status |
|---|---|---|---|---|
| Presidential approval | 0.12 / net approval pt | net −18.01 | D+2.16 | ✅ through 9/16/26 |
| Consumer sentiment | 0.04 / pt below 85.0 | 51.7 | D+1.33 | ⚠️ **stale — Aug final; Sept preliminary was due 9/11** |
| GDP growth | 0.3 / pt above 2.0% | 1.5% | D+0.15 | ✅ Q2 second estimate |
| Unemployment | none — display only | 4.1% | — | ⚠️ stale — July; August was due 9/4 (display only) |
| Base midterm penalty | — | — | D+1.50 | constant |

---

## ✅ Done in this refresh

**Presidential approval** — new NYT bulk export, **1,020 polls through 9/16/26** (was 989
through 8/28). 891 fall inside the 540-day window and carry weight. Net approval moved
−17.64 → **−18.01**, slightly *more* favourable to Democrats. The previous file is archived
at `backend/app/data/archive/potus-approval-2026-08-28.csv` (verified byte-identical to the
version it replaced). The new file is a clean superset — 31 polls added, none dropped. No
code or JSON edits were needed; `environment.py` reads this file live at runtime.

**Senate polling** — new NYT bulk export, **629 polls / 4,169 rows** (was 559 / 3,794).
71 new polls curated into `polls.csv`, which now holds 499 rows with **303 included across
25 states** (was 408 / 257 / 24). Previous file archived at
`backend/app/data/archive/senate-2026-08-28.csv`, also verified byte-identical.

**Net effect:** national environment D+5.10 → **D+5.14**. D control probability ~44.2% →
**~43.8%**. Four races changed rating.

| Race | Was | Now | Why |
|---|---|---|---|
| **SC** | Lean R | **Safe R** | two independent polls finally landed — see below |
| **NH** | Safe D | **Likely D** | Sununu won the primary; Brown matchups dropped |
| **TX** | Lean R | **Toss-up** | 9 new polls, average D+1.7 → D+2.0 |
| **IA** | Likely R | **Lean R** | 8 new polls, average R+1.4 → R+0.8 |

---

## ⚠️ Four things worth knowing

### 1. South Carolina is fixed — and it went the other way

SC was the most fragile input in the model: its entire average was one D-sponsored poll at
41-41 in an R+11 seat. Two independent polls of the real matchup have now landed:

- Abacus Data (Aug 26–28, LV n=306): **Graham +13**
- InsiderAdvantage (Sept 8–9, LV n=1200): **Graham +1.9**

The three-poll average is **R+5.0**, up from D+0.0, and the race moves Lean R → **Safe R**
(D win probability 33.7% → 14.0%). The false toss-up is retired. Three polls in an R+11 seat
is still thin, but it is no longer one sponsored poll doing all the work.

### 2. Eight duplicate rows were inflating four state averages

NYT's export lists some pollsters under two names, and both spellings had been curated in as
separate rows — the same physical survey counted twice. Found by matching on
state + field dates + sample size + matchup:

| State | Survey | Entered as |
|---|---|---|
| AK ×3 | Alaska Survey Research (Aug '25, Oct '25, Jan '26) | "AK Survey Research" + "Alaska Survey Research" |
| AK ×1 | PPP (Jan '26) | "PPP" + "Public Policy Polling" |
| ME ×2 | Pan Atlantic (Dec '25, Mar '26) | "Pan Atlantic" + "Pan Atlantic SMS Group" |
| ME ×1 | UNH (Feb '26) | "UNH" + "University of New Hampshire" |
| MI ×1 | Glengariff (Jan '26) | "Glengariff Group" + "Glengariff Group, Inc." |

The rounded-value copy was flagged `no` in each case and the full-precision NYT record kept.
This is the same bug class caught in Aug 2026 with the MN PPP/GQR survey — **it recurs with
every drop**, so re-run the signature check each time. Effect was small (AK and ME each moved
well under a point) but it was systematically double-weighting those pollsters.

### 3. NYT withdrew a Minnesota poll

The Impact Research MN poll (fielded 7/8–7/11/25, Flanagan 48 – Tafoya 45) is **gone from the
9/19 export**. Its source memo was titled "MN Senate Dec-2025" while the field dates were
July, so it looks like a data-quality retraction. It had been included in MN's average; it is
now flagged `no`.

### 4. New Mexico has a contradiction — held out, needs your call

`races_2026.json` records that the only Republican to file was disqualified and that **no
Republican appears on the NM Senate ballot**. But this drop carries a Research &
Polling/Albuquerque Journal *general-election* question (Aug 21–28, n=516 LV) testing
**Luján 53 – Larry Marker (R) 38**, not flagged hypothetical.

Both cannot be right. I left the poll flagged `no`, so NM still has no polling average and
stays Safe D on fundamentals. Including it would actually make an effectively uncontested
seat look *less* safe (D+15 is worse for Luján than unopposed). **Confirm whether Marker
holds a ballot line before including it.**

---

## Primaries resolved since the last refresh

Both landed as expected, and the losers' matchups are now flagged `no`:

- **Massachusetts (Sept 1)** — **Markey** beat Moulton (final polls had him +30). 7 Moulton
  rows excluded; MA average D+23.3 → **D+21.0**, still Safe D.
- **New Hampshire (Sept 8)** — **Pappas** (D) and **Sununu** (R). Brown ran ~12 points weaker
  than Sununu, so dropping the 5 Brown rows is most of the D+6.1 → **D+4.1** move, and the
  rating goes Safe D → **Likely D**. Two post-primary polls are in: co/efficient (Sept 9–11)
  even, InsiderAdvantage (Sept 16–17) D+7.9.

No nominations remain open.

---

## Outstanding — not in this drop

You gave me `senate.csv` and `potus-approval.csv` only, so the economic side is unchanged and
two releases have come due:

| Release | Due | Status | Matters? |
|---|---|---|---|
| U. Michigan September **preliminary** | Sept 11 | ❌ **not incorporated** | **yes** — sentiment is the 2nd-largest contributor (D+1.33) |
| BLS Employment Situation, August | Sept 4 | ❌ not incorporated | display only |

Sentiment is the one to chase. Pull it from
<https://www.sca.isr.umich.edu/files/tbmics.csv> (full monthly history, always current) —
not the per-month `ff<YYYYMM>.pdf`, which lags and is named for the month it *reports*, not
the month it is published.

### Coming up

| Date | Release | Matters? |
|---|---|---|
| Late Sept | BEA Q2 third estimate | rarely moves |
| Early Oct | U. Michigan September **final** | yes — sentiment |
| Oct 2 | BLS Employment Situation, September | display only |
| **Late Oct** | BEA Q3 **advance** estimate | yes — last GDP print before the election |

Approval polling should be re-dropped roughly weekly. The average uses a 21-day half-life, so
a file more than about two weeks stale is materially discounting its own freshest data.

---

## Polling files

**Senate** (`senate.csv`) and **gubernatorial** (`governors.csv`) NYT bulk exports. Archive
the current file before overwriting; both are curated by hand — see the pipeline notes in
`README.md`.

`governors.csv` was **not** refreshed this cycle (still Aug 28). It feeds the β=0.10
gubernatorial coattails term, so it is a second-order input, but it is now the stalest
polling file in the repo.

### Curation reminders for the next drop

1. Diff against the newest file in `archive/` **by `poll_id`**, then group new rows by
   `question_id` and decide include/exclude per question — one survey publishing N questions
   otherwise gets N× weight.
2. Re-run the duplicate signature check (state + field dates + sample size + matchup). It has
   now caught double-counted rows twice running.
3. Multi-screen polls: keep the **LV** screen. This drop had 9 such polls (Abacus ×5,
   YouGov ×3, MSU, TIPP, Targoz, Elon lv/rv/adult).
4. AK: keep the **head-to-head / final RCV round** question, not the first-round or
   full-field forms.
5. Generic-ballot questions are excluded from named-candidate averages (5 this drop).
6. Check whether any poll_ids **vanished** from the export, not just which were added.

---

## Not needed

- **Cook PVI** — values in `races_2026.json` and the reference table in
  `backend/app/model/governors.py` only change after a presidential election.
- **Candidate quality scores** — hand-set in `races_2026.json`; revisit only when a nominee
  changes. No nominations are open.
