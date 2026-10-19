# Data Refresh Checklist

Status of every input that has to be fetched by hand. Last refreshed **October 19, 2026**
(15 days to the election).

The four economic inputs feed `national_environment_shift()` in
`backend/app/model/environment.py`, currently **D+5.43**. That shift is added to all 35
races, so an error here moves the whole map rather than one state.

| Input | Coefficient | Current value | Contribution | Status |
|---|---|---|---|---|
| Presidential approval | 0.12 / net approval pt | net −20.43 | D+2.45 | ✅ through 10/18/26 |
| Consumer sentiment | 0.04 / pt below 85.0 | 51.7 | D+1.33 | ❌ **stale — Aug final; Sept prelim, Sept final and Oct prelim all out** |
| GDP growth | 0.3 / pt above 2.0% | 1.5% | D+0.15 | ⚠️ Q2 second estimate; third estimate out late Sept |
| Unemployment | none — display only | 4.1% | — | ⚠️ stale — July (display only) |
| Base midterm penalty | — | — | D+1.50 | constant |

---

## ✅ Done in this refresh

**Presidential approval** — new NYT bulk export, **1,069 polls through 10/18/26** (was 1,020
through 9/16). 881 fall inside the 540-day window. Net approval moved −18.01 → **−20.43**,
worth +0.29 to the environment. Previous file
archived at `backend/app/data/archive/potus-approval-2026-09-20.csv` (verified
byte-identical). Clean superset: 49 polls added, none dropped, no values revised.

**Senate polling** — new NYT bulk export, **787 polls / 4,940 rows** (was 629 / 4,169).
158 new polls; none vanished. Previous file archived at
`backend/app/data/archive/senate-2026-09-20.csv`, also verified byte-identical.
`polls.csv` now holds **692 rows with 460 included across 28 states** (was 499 / 303 / 25).
Baseline reconciled to 0.01 against the stored averages, and the duplicate-signature check
was clean, before any edits.

**Net effect:** D control **~44% → ~54%** (53.9–54.4% across seeds; 40k sims each).
Expected D seats 50.1 → **50.7**. This is the first run with Democrats favored.

Attribution, all run at today's date so α drift is held constant (old inputs alone give
45.7% today):

| Step | D control | Δ |
|---|---|---|
| Old inputs, today's date | 45.7% | — |
| + new approval | 46.7% | +1.0 |
| + 158 new Senate polls, NM/ID/IL/LA resolved | 52.6% | +5.9 |
| + nominee cleanup (see §1) | 53.9% | +1.3 |

| Race | Was | Now | Why |
|---|---|---|---|
| **OH** | Toss-up | **Lean D** | 11 new polls avg D+3.0; Brown led 9. Average D+1.1 → D+1.8 |
| **SC** | Safe R | **Likely R** | four straight polls within 3 pts. Average R+5.0 → R+3.3 |
| **ME** | Lean D | **Likely D** | the cleanup, not new polls — see §1. D+1.3 → D+2.6 |
| **AK** | Toss-up | **Lean D** | α drift alone; already Lean D at today's date on old inputs |

---

## ⚠️ Five things worth knowing

### 1. 55 non-nominee rows were still in the averages — fixed

Rule 3 (re-flag a primary loser's matchups `no`) was applied to MN, SD, MA and NH but never
to the earlier primaries. Checking every included row's candidates against
`races_2026.json` found **55 rows** still counted:

| State | Rows | What |
|---|---|---|
| ME | 30 | Platner, Mills, Kleban, Smeriglio — incl. a UNH Smeriglio 1 – Collins 66 R-subsample row |
| GA | 13 | Carter, King, Dooley |
| IA | 5 | Sage, Wahls, Ernst, generic D |
| KS | 2 | Schmidt |
| KY | 2 | Cameron, Morris |
| NH | 1 | Innis |
| AK, MN | 1 each | generic candidate |

All flagged `no` with the reason in `notes`. Biggest moves: **ME D+1.4 → D+2.6**,
**KY R+7.0 → R+10.0**, IA +0.4, KS +0.9. The pre-flight mean check and the duplicate
check both pass with these rows present, so neither catches it. A **nominee check** now
belongs alongside them (see the reminders below).

### 2. New Mexico is resolved — Marker is on the ballot

The JSON note was wrong. After the only filed Republican was disqualified, Roswell
businessman **Larry Marker ran a write-in primary campaign and took 4,470 votes, above the
2,351 needed** to claim the Republican line
([Roswell Daily Record](https://www.rdrnews.com/news/local/results-of-the-new-mexico-primary-2026-write-in-campaign-gets-marker-gop-nomination-in/article_af4014da-b950-4d3c-a8f2-17bda428111d.html),
[Source NM](https://sourcenm.com/2026/09/11/new-mexico-election-2026-us-senator/)).
The August Research & Polling poll is now included, alongside two new ones: average
**D+16.3** across 3 polls. Rep candidate set to Marker, quality score **2** (was 0 for
"None (disqualified)", which had been handing Luján a 4.8-pt quality bonus). Still Safe D.

### 3. Idaho changed shape — Roth is out, Achilles is on the D side

Democrat **David Roth ended his campaign on July 28 and filed his withdrawal Aug 28**
([Idaho Capital Sun](https://idahocapitalsun.com/2026/07/28/idaho-democrat-david-roth-ends-campaign-for-us-senate-seat-held-by-risch/),
[Spokesman-Review](https://www.spokesman.com/stories/2026/jul/29/democrat-david-roth-to-withdraw-from-idaho-senate-/)).
Every poll since has been Risch vs independent **Todd Achilles**. Achilles is now modeled on
the D side, as Osborn and Bengs are, and only post-withdrawal polls are used (4 polls,
avg **R+19.5** — IND-sponsored Bullfinch Achilles +5, R-sponsored Peak Risch +34 / +25,
Change Risch +24). Two of those (Bullfinch Aug, Peak Aug) had sat in the export uncurated
since September. Still Safe R.

**Needs your call:** Achilles' **quality score is set to 4 by hand** (Roth was 2; Bengs 2,
Osborn 7). It does not move the rating at R+32, but it isn't data-driven.

### 4. Two new single-poll states — LA is the fragile one

- **Louisiana**: first general-election poll, Hart Research (Sept 17-19, **D-sponsored**),
  Letlow 48 – Davis 44. D win 0% → ~5%. One sponsored poll in an R+20 seat — the same
  shape as the old SC problem, though the PVI keeps it Safe R.
- **Illinois**: PPP (Oct, RV) Stratton 49 – Tracy 36. Safe D either way.

IL, LA, OK and TN now each rest on a single poll.

### 5. Kansas now polls even in an R+20 state

Eight new polls moved KS **R+2.8 → D+0.4**. Hamilton led 6 of 8, including nonpartisan
YouGov D+3 and Wedgewood D+2. NYT/Siena had Marshall +0.3. The model holds it Safe R
(~14%) on R+20 PVI. That is the cap and the fundamentals working as designed, but if
KS polling holds, it is the race most likely to embarrass the rating.

---

## Curation decisions this drop

Usual rules, plus three clarifications now written into CONTEXT.md:

1. **Head-to-head over minor-party multi-way.** When a survey asked both, the
   head-to-head is kept unless a *viable* independent is on the ballot (MT/Bodnar,
   MS/Pinkins). 11 surveys this drop: KS ×3, OH ×2, MI ×2, MN, NE, IA, and ID/Bullfinch.
   Matches the July TX precedent.
2. **Two LV screens from one YouGov survey → keep the tighter (smaller-n) one** (GA, NC),
   following the Sept IA precedent. RV screens dropped in 11 more polls (Marist ×2, Fox ×3,
   Big Data Poll ×5, Targoz).
3. **AK full-field-only polls are excluded.** Trafalgar (Sept 22-24) published only a
   first-round question with the name-alike Dan J. Sullivan at 2.8 and Heikes at 0.7, which
   understates Sullivan's final-round number. Flagged `no`. ASR's round-3 numbers and three
   head-to-heads used as normal.

Also:
- 5 generic-ballot questions excluded (FL, ME, MI, NE, OH).
- **PA skipped**: two Bravo Group/PennLive rows list only Fetterman, whose seat is not up
  until 2028.
- **ActiVote** appears for the first time (FL, OH, TX). Included as normal — it reports
  forced two-party shares, but the margins are usable. Flag it if you'd rather exclude it.
- NYT revised the Change Research ID survey (Risch 42 → 43 in the Roth form, 43 → 45 in
  the no-Roth form). Both applied.
- Older polls newly published: NE GBAO ×3 (Apr, Jul, Sept; pro-Osborn PAC), SD Lake
  Research (Aug, D-sponsored), all included.

Candidate fields fixed in `races_2026.json`: NH rep "TBD (primary Sept 8…)" → **John
Sununu**; MA rep "TBD (primary Sept 1…)" → **John Deaton**. Names only; scores unchanged.

Race notes rewritten for 26 races. Several
were stale before this drop (ME and OH notes still said "Toss-up", NC "Likely D").

---

## Outstanding — not in this drop

You gave me `senate.csv` and `potus-approval.csv` only, so the economic side is unchanged —
and it is now **two months stale** on sentiment, the second-largest contributor:

| Release | Status | Matters? |
|---|---|---|
| U. Michigan Sept preliminary, Sept final, **Oct preliminary** | ❌ not incorporated | **yes** |
| BEA Q2 third estimate | ❌ not incorporated | rarely moves |
| BLS Employment Situation, Aug and Sept | ❌ not incorporated | display only |

Pull sentiment from <https://www.sca.isr.umich.edu/files/tbmics.csv>.

### Coming up

| Date | Release | Matters? |
|---|---|---|
| **~Oct 29** | BEA Q3 **advance** estimate | yes — last GDP print before the election |
| ~Oct 30 | U. Michigan October **final** | yes — sentiment |

Approval polling should be re-dropped roughly weekly from here. With 15 days left, one
more Senate drop around Oct 28 – Nov 1 would catch the final wave of public polls.

---

## Polling files

**Senate** (`senate.csv`) and **gubernatorial** (`governors.csv`) NYT bulk exports. Archive
the current file before overwriting; both are curated by hand — see the pipeline notes in
`README.md`.

`governors.csv` was **not** refreshed this cycle (still Aug 28). It feeds the β=0.10
gubernatorial coattails term — second-order, but now nearly two months stale.

### Curation reminders for the next drop

1. Diff against the newest file in `archive/` **by `poll_id`**, then group new rows by
   `question_id` and decide include/exclude per question — one survey publishing N questions
   otherwise gets N× weight.
2. Re-run the duplicate signature check (state + field dates + sample size + matchup).
3. **New: run the nominee check** — every `yes` row's D and R last names must match the
   candidates in `races_2026.json` (independents on the D side in NE/SD/ID). It caught 55
   rows this time that both other checks pass.
4. Multi-screen polls: keep the **LV** screen; two LV screens → the tighter one.
5. Head-to-head over minor-party multi-way; multi-way only for a viable independent.
6. AK: keep the **head-to-head / final RCV round**; exclude full-field-only polls.
7. Generic-ballot questions are excluded from named-candidate averages.
8. Check whether any poll_ids **vanished** from the export, not just which were added.
9. Check for **older polls newly added** to the export (this drop: NE GBAO ×3 from Apr–Sept,
   SD Lake Research from Aug), and for archived polls that were never curated (ID had two).

---

## Not needed

- **Cook PVI** — values in `races_2026.json` and the reference table in
  `backend/app/model/governors.py` only change after a presidential election.
- **Candidate quality scores** — hand-set in `races_2026.json`; revisit only when a nominee
  changes. Two changed this time (NM Marker → 2, ID Achilles → 4).
