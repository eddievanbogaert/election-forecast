# Project Context — Quick Re-Orientation Guide

Use this file to get up to speed quickly after a context reset or session limit.

---

## What we're building

A FiveThirtyEight-style election forecasting site for the **2026 US Senate midterms**
(33 Class II seats + OH and FL special elections = **35 races total**). The site shows an
interactive US choropleth map, per-race win probabilities, and overall chamber control odds
derived from a 40,000-iteration Monte Carlo simulation.

**GitHub repo**: `eddievanbogaert/election-forecast` (private)
**Local clone**: `/Users/eddievb/Development/election-forecast`
**GCP project**: `election-forecast-489820` (owner: eddie@eddievb.com)
**Live site**: https://elections.eddievb.com (also: https://election-forecast-489820.web.app)

---

## Technology stack

| Layer | Stack |
|---|---|
| Frontend | React 18 + TypeScript + Vite; `react-simple-maps` (map); `recharts` (histogram); Tailwind CSS |
| Backend | Python 3.12 + FastAPI + NumPy (Monte Carlo); served by uvicorn |
| Hosting | Firebase Hosting (frontend) + Cloud Run (backend, scales to 0) |
| CI/CD | GitHub Actions → Artifact Registry → Cloud Run + Firebase Hosting |
| Secrets | GitHub repo secrets: `GCP_SA_KEY`, `FIREBASE_SERVICE_ACCOUNT`, `ADMIN_SECRET` |

---

## Repository layout (key files)

```
backend/
  app/main.py                    — FastAPI app; CORS via CORS_ORIGINS env var
  app/routes/forecast.py         — GET /api/forecast (30 min cache); POST /api/forecast/refresh
  app/model/monte_carlo.py       — 40k-iteration simulation engine; SimulationOutput
  app/model/fundamentals.py      — PVI + incumbency + environment + quality + polling blend
  app/model/environment.py       — National environment model (approval, GDP, sentiment)
  app/model/governors.py         — Gubernatorial coattail signal (beta=0.10, capped)
  app/data/races_2026.json       — Seed data: 35 races (PVI, candidates, polling averages, notes)
  app/data/environment.json      — National environment indicators (approval, GDP, sentiment)
  app/data/polls.csv             — All polls considered (692 entries, 460 included, 28 states)
  app/data/governors.csv         — NYT bulk export of gubernatorial polls (read live)
  app/data/senate.csv            — NYT bulk export of all published Senate polls (~4.2k rows)
  app/data/potus-approval.csv    — NYT bulk export of presidential approval polls (read live)
  app/data/archive/              — Dated snapshots of prior senate.csv / potus-approval.csv drops
  app/data/analysis_notes.md     — Detailed race-by-race analysis, tiered ratings, methodology
  app/data/races_2028.json       — Future cycle data (Class III, not active)

frontend/
  src/App.tsx                    — Layout; top-level state (selectedCode)
  src/components/USMap.tsx       — react-simple-maps choropleth; hover tooltip; click → select
  src/components/ChamberControl.tsx — Probability bar + recharts seat distribution histogram
  src/components/RaceList.tsx    — Races grouped by rating; mini probability bars
  src/components/RaceDetail.tsx  — Selected race: prob bar, candidates, stats, notes
  src/components/Header.tsx      — Title, "Model updated" date, polling weight, environment
  src/hooks/useForecast.ts       — TanStack Query; fetches /api/forecast
  src/types/index.ts             — TypeScript interfaces (Race, ForecastResponse, etc.)
  src/utils/colors.ts            — Color scale (Safe D → Safe R), probToColor
  src/utils/stateUtils.ts        — STATE_NAME_TO_CODE lookup, formatProb/formatLean/formatPvi
  public/favicon.svg             — Bar chart favicon (SVG primary)
  public/favicon.png             — PNG fallback + apple-touch-icon
  public/og-image.svg            — Open Graph share image source (1200×630)
  public/og-image.png            — PNG version for social sharing
  index.html                     — OG/Twitter Card meta tags, favicon links

infrastructure/setup.sh          — One-shot GCP provisioning (already run)
.github/workflows/deploy.yml     — CI/CD: backend (Cloud Run) then frontend (Firebase)
```

---

## Model (v0.2.0)

### Current state (Aug 30, 2026, 65 days to election)

The model blends **structural fundamentals** with **polling data** using a time-weighted
ramp. At 65 days out, polling weight `α ≈ 0.62`. The ramp is now **capped at 0.75**, so
Senate polling never exceeds three-quarters of the mix even on election day — the rest
stays with PVI, the national environment, incumbency, candidate quality and the new
gubernatorial signal. A thin state average still moves a race hard, which is why
hypothetical-matchup polls get held out and stale matchups get re-flagged.

### National environment: D+5.10

A four-component data-driven estimate (replaces earlier flat midterm penalty):

| Component | Coefficient | Current Value | Contribution |
|-----------|-------------|---------------|-------------|
| Base midterm penalty | — | — | D+1.50 |
| Presidential approval | 0.12 per net approval pt | −20.43 | D+2.45 |
| GDP growth | 0.3 per pt above 2.0% trend | 1.5% | D+0.15 |
| Consumer sentiment | 0.04 per pt below 85.0 baseline | 48.0 | D+1.48 |

Approval is **computed live** at runtime by `environment.py` from `potus-approval.csv`
(exponential time decay, 21-day half-life, ±2.0 pt partisan-sponsor adjustment, polls older
than 540 days dropped). The `presidential_approval` block in `environment.json` is only a
fallback and is overridden on every run — so dropping a fresh `potus-approval.csv` in is
all that is needed (currently 1,069 polls through 10/18/26). GDP and sentiment are **manual**
entries in `environment.json` (BEA Q2 2026 second estimate, released 8/26; U. Michigan
October 2026 preliminary 48.0, from `tbmics.csv` pulled 10/26). See `DATA-REFRESH.md`.

### Fundamentals lean (per race)

```
fundamentals_lean = −PVI + environment_shift + incumbency(±2.5) + quality_diff × 0.8
                    + governor_coattail (β=0.10 × gov residual, ±2.0 cap, n/(n+2) shrink)
```

### Gubernatorial coattails (new Aug 30)

`app/model/governors.py` reads `governors.csv` live and gives each Senate race a small push
based on how far its state's governor race is running from that state's partisan baseline.

- β estimated from the 45 concurrent Senate+governor races since 2018 (2018 n=20, 2022 n=25)
  by a double-residual fit within each cycle: β = 0.119, SE 0.050, bootstrap 90% CI
  [0.036, 0.241]. Model uses **0.10**, the conservative end.
- Raw Senate~governor margin correlation is r = 0.59, but almost all of that is shared
  partisanship already in PVI — using it directly would double-count.
- Damped by a ±2.0 cap and an n/(n+2) shrink, so a state with one stale governor poll
  barely moves. Largest current effect on a competitive race: **NH −0.97** (Ayotte).
- 28 states currently carry a signal; 19 of them have a 2026 Senate race.

### Alaska: two Dan Sullivans

Incumbent **Dan Sullivan (R)** and **Daniel J. Sullivan Jr.** (a logger, no party
affiliation, 2.5% in the primary, 3-5% in polls) are both on the November ballot. Alaska's
RCV returns most misdirected votes to the incumbent in later rounds; only the share that
never returns helps Peltola:

```
share 0.030 × intent 0.70 × non-return 0.45 ≈ 1.0 pt
```

Applied as `ballot_adjustment: 1.0` on the AK race, post-blend at full strength. Range
+0.4 to +2.3. AK's polling average is read as the RCV final round (head-to-head), so this
does not double-count.

### Blending

```
blended_lean = α × polling_average + (1 − α) × fundamentals_lean + ballot_adjustment
α = 0.75 × max(0, min(1, (365 − days_until_election) / 365))
```

At ≥365 days out, α = 0 (fundamentals only). Ramps linearly to **α = 0.75** on election
day — Senate polling is deliberately capped at three-quarters of the mix. `ballot_adjustment`
applies at full strength (AK only: +1.0 for Peltola, the two-Dan-Sullivan ballot).

### Uncertainty (sigma)

```
σ_fundamentals = 7.0 × (1 − α)     # large early, shrinks as polls arrive
σ_polling       = 2.5 × α           # pure polling error
σ_residual      = 2.8               # state-specific floor
σ_total         = √(σ_f² + σ_p² + σ_r² + 1.5² if open seat)
```

### Monte Carlo simulation

```python
# Per simulation (40,000 total):
nat_error  ~ N(0, 2.5)              # national wave — all states move together
state_err  ~ N(0, σ_total)          # independent per state
margin_i   = blended_lean_i + nat_error + state_err_i
D_wins_i   = margin_i > 0
```

Win probabilities = empirical means across 40k sims.
Chamber control = P(D total seats ≥ 51).

---

## Current forecast snapshot (Oct 19, 2026 — 15 days out)

| Metric | Value |
|--------|-------|
| Expected D seats | ~50.7 / 100 |
| D Senate control probability | ~54% (53.9–54.4% across seeds) |
| Net national environment | D+5.58 (net approval −20.43 through 10/18; sentiment 48.0, Oct prelim) |
| Polling weight | ~72% Senate polls / 28% everything else (cap 75%) |
| D seats not up | 34 |
| R seats not up | 31 |

Control requires 51 (no D tie-breaker this cycle). This is the first run with D control
above 50%.

### Race ratings

| Rating | Races |
|--------|-------|
| **Safe D** | NC, GA, MN, and 9 others |
| **Likely D** | NH, ME |
| **Lean D** | MI, AK, OH-Special |
| **Toss-up** | TX |
| **Lean R** | IA |
| **Likely R** | SC |
| **Safe R** | KS, NE, FL, LA, MS, SD, and 9 others |

Changes from the Sept 20 run. Re-running the old inputs at today's date gives 45.7% (the
Sept 20 run itself showed ~44%; the gap is α drift as the election nears). From there:
approval +1.0 pt, the Oct 19 NYT drop +5.9 pts, nominee cleanup +1.3 pts → ~54%.
- **OH Toss-up → Lean D** (54% → 58%): 11 new polls average D+3.0; Brown led nine.
- **SC Safe R → Likely R** (14% → 20%): four straight polls within 3 points; average
  R+5.0 → R+3.3.
- **ME Lean D → Likely D** (68% → 76%): driven by the cleanup, not new polls — 30
  Platner/Mills rows were still in the average. The Jackson-only average is D+2.6.
- **AK Toss-up → Lean D** happened through α drift alone (already Lean D at today's date
  on the old inputs).
- **KS** moved R+2.8 → D+0.4 on eight new polls but stays Safe R (14%) on R+20 PVI.

Note: rating labels come from `prob_to_rating()` in `monte_carlo.py`, whose cutoffs
(Safe ≥85%) are looser than the scale documented in `analysis_notes.md` (Safe >95%).
That is why NC/GA/MN read "Safe D" at ~87–94%. Unreconciled — see priorities.

### Key battlegrounds

| Race | PVI | Polling Avg | D Win Prob | Rating |
|------|-----|-------------|-----------|--------|
| NC (Cooper vs Whatley) | R+3 | D+8.4 | ~94% | Safe D |
| GA (Ossoff vs Mike Collins) | R+4 | D+6.7 | ~91% | Safe D |
| MN (Flanagan vs Tafoya) | D+3 | D+3.7 | ~87% | Safe D |
| NH (Pappas vs Sununu) | D+1 | D+4.1 | ~82% | Likely D |
| ME (Jackson vs Collins) | D+3 | D+2.6 | ~76% | Likely D |
| MI (El-Sayed vs Rogers) | R+1 | D+1.5 | ~68% | Lean D |
| AK (Peltola vs Sullivan) | R+9 | D+2.2 | ~60% | Lean D |
| OH Special (Brown vs Husted) | R+8 | D+1.8 | ~58% | Lean D |
| TX (Talarico vs Paxton) | R+10 | D+2.1 | ~50% | Toss-up |
| IA (Turek vs Hinson) | R+10 | D+0.2 | ~40% | Lean R |
| SC Special (Andrews vs D. Graham) | R+11 | R+3.3 | ~20% | Likely R |
| KS (Hamilton vs Marshall) | R+20 | D+0.4 | ~14% | Safe R |
| NE (Osborn I vs Ricketts) | R+22 | R+0.2 | ~12% | Safe R |
| FL Special (Nixon vs Moody) | R+5 | R+6.9 | ~9% | Safe R |

### Polling data coverage

28 states have polling data incorporated: AK, AL, AR, FL, GA, IA, ID, IL, KS, KY, LA, MA,
ME, MI, MN, MS, MT, NC, NE, NH, NM, OH, OK, RI, SC, SD, TN, TX. IL and LA joined with the
Oct 19 drop (one poll each), and NM joined once Marker's ballot line was confirmed.

All polls tracked in `polls.csv` (692 entries, 460 included in averages). Bulk NYT export
in `senate.csv`; prior drops in `app/data/archive/`.

**How a polling average is produced** (there is no script — this is done by hand):
`senate.csv` (raw NYT bulk export, one row per candidate per question) → `polls.csv`
(one curated row per matchup, with an `included_in_average` yes/no flag and a reason in
`notes`) → `polling_average` in `races_2026.json` is the **unweighted mean of
`dem_pct − rep_pct` across rows flagged `yes`** for that state. No time decay, no
sample-size or pollster weighting. Multi-matchup surveys contribute one row per matchup,
so a single poll testing five opponents counts five times — watch for that when one
sponsored survey is the only data (it is why SC and OK are currently held out).

**NM resolved (Oct 19).** Larry Marker won the Republican line through a write-in
primary campaign (4,470 votes, above the 2,351 threshold) after the only filed Republican
was disqualified. The Aug poll is now included alongside two October polls (avg D+16.3).

**ID changed shape (Oct 19).** Democrat David Roth withdrew (announced Jul 28, filed
Aug 28). Independent Todd Achilles is now modeled on the D side like Osborn and Bengs,
with quality score 4 (set by hand — review). Only post-withdrawal polls are used.

Curation rules applied through the Oct 19 drop:
- One row per distinct matchup. Where a survey published several population screens of
  the same matchup, the LV screen is kept and the others flagged `no` (NC/Elon published
  three, NC/High Point and MI/TIPP two each).
- Where a survey asked both a two-party and a ballot-realistic multi-way question, the
  multi-way one is kept **only when a viable independent is on the ballot** (MT with
  Bodnar, MS with Pinkins). When the extra names are minor-party candidates (Libertarian,
  Green, etc.), the head-to-head is kept. Where YouGov publishes two LV screens, the
  tighter (smaller-n) one is kept.
- AK: a poll that publishes only a first-round full-field question is excluded (Trafalgar,
  Sept '26) — the minor R candidates' votes transfer to Sullivan in the final round.
- Where a nomination is genuinely unresolved, every live matchup is kept (NH Sununu+Brown,
  MA Markey+Moulton). Where the only data is one sponsored poll of an undecided field, the
  state is held out entirely (SC, OK).
- When a primary resolves, the loser's matchups are re-flagged `no` (MN: four Craig rows
  dropped after Aug 11; SD: three Beaudion rows dropped after his withdrawal; MA: seven
  Moulton rows after Sept 1; NH: five Brown rows after Sept 8). **This had not been
  applied to the earlier primaries:** the Oct 19 pass found 55 still-included rows testing
  non-nominees or generic candidates (ME x30 Platner/Mills/others, GA x13, IA x5, KS x2,
  KY x2, NH x1 Innis, plus generic rows in AK/IA/ME/MN). Check every included row's
  candidate names against `races_2026.json` on every drop.
- **Check for duplicate surveys every drop.** NYT lists some pollsters under two names and
  both spellings get curated in, double-counting one survey. The Sept 19 pass found eight
  such rows (AK x4, ME x3, MI x1) that had been inflating those averages, on top of the
  MN PPP/GQR pair caught in August. Match on state + field dates + sample size + matchup.
- **Check for withdrawn polls too.** The Sept 19 export dropped an MN Impact Research poll
  that had been in the average (its source memo and field dates disagreed).

---

## Races (35 seats)

33 Class II seats (last elected 2020) + 2 special elections:
- **OH Special**: Vance vacated upon becoming VP. Brown (D) vs Husted (R).
- **FL Special**: Rubio vacated upon becoming Secretary of State. TBD (D) vs Moody (R, appointed).

### Senate composition going into 2026

- D holds 34 seats not up for election
- R holds 31 seats not up for election
- 35 seats contested: D defends ~13 (mostly safe), R defends ~22

### All 35 races

| State | Inc. | Party | PVI | Polling | Key notes |
|---|---|---|---|---|---|
| AL | Open | R | R+27 | R+18 | Tuberville → Gov race. Moore (R) vs Wess (D). Safe R |
| AK | Sullivan | R | R+9 | D+2.24 | Peltola led top-4 primary 49.5-41.4. TWO Dan Sullivans on ballot; +1.0 ballot adj; RCV. Lean D |
| AR | Cotton | R | R+24 | R+9.6 | Two Oct polls Cotton +9/+11. Safe R |
| CO | Hickenlooper | D | D+4 | — | Baisley (R) nominee. Safe D |
| DE | Coons | D | D+8 | — | Safe D |
| FL | Moody (appt) | R | R+5 | R+6.88 | Rubio vacancy. Nixon upset Vindman 56-44. Moody has led all 17 polls. Safe R |
| GA | Ossoff | D | R+4 | D+6.69 | Top R target. Ossoff vs Mike Collins; 13 Carter/King/Dooley rows dropped Oct 19. Safe D |
| ID | Risch | R | R+32 | R+19.5 | Roth (D) withdrew; Achilles (I) modeled D-side. 4 polls, split by sponsor. Safe R |
| IL | Open | D | D+17 | D+13 | Durbin retired. Stratton vs Tracy. First poll (PPP, Oct) D+13. Safe D |
| IA | Open | R | R+10 | D+0.24 | Ernst retired. Hinson (R) vs Turek (D). Average crossed to Turek; Lean R on PVI |
| KS | Marshall | R | R+20 | D+0.37 | Marshall vs Hamilton. 8 new polls, Hamilton led 6. Safe R on R+20 PVI (~14%) |
| KY | Open | R | R+26 | R+10 | McConnell retired. Barr (R) vs Booker (D). Cameron/Morris rows dropped Oct 19 |
| LA | Open | R | R+20 | R+4 | Cassidy LOST primary. Letlow (R) vs Davis (D). One D-sponsored poll, R+4. Safe R |
| ME | Collins | R | D+3 | D+2.65 | Jackson (D) vs Collins. 30 non-nominee rows dropped Oct 19. Likely D |
| MA | Markey | D | D+30 | D+22.65 | Markey vs Deaton. Safe D |
| MI | Open | D | R+1 | D+1.52 | Peters retired. El-Sayed vs Rogers. Led 16 of 19 polls since mid-Sept. Lean D |
| MN | Open | D | D+3 | D+3.66 | Smith retired. Flanagan vs Tafoya. Safe D |
| MS | Hyde-Smith | R | R+18 | R+4.33 | First nonpartisan poll (Wedgewood, Oct) R+4. Safe R |
| MT | Open | R | R+18 | R+23.26 | Daines withdrew. Alme (R) vs Bankhead (D) + Bodnar (I) — multi-way questions |
| NE | Ricketts (appt) | R | R+22 | R+0.2 | Osborn (I) tied in polls. Modeled on D side. Safe R on PVI |
| NH | Open | D | D+1 | D+4.08 | Shaheen retired. Pappas vs Sununu; post-primary polls avg D+6.1. Likely D |
| NJ | Booker | D | D+14 | — | Safe D |
| NM | Luján | D | D+4 | D+16.33 | Marker (R) on ballot via write-in primary. 3 polls. Safe D |
| NC | Open | R | R+3 | D+8.45 | Tillis retired. Cooper vs Whatley. Cooper led 40 of 41. Safe D |
| OK | Open | R | R+26 | R+24 | Mullin → DHS. Hern (R) vs Thomas (D), who won the Aug 25 runoff. Safe R |
| OR | Merkley | D | D+8 | — | Safe D |
| RI | Reed | D | D+18 | D+22.67 | Safe D |
| SC | Open | R | R+11 | R+3.33 | Graham seat vacant. Four straight polls within 3 pts; Safe R -> Likely R |
| SD | Rounds | R | R+27 | R+4.4 | Beaudion (D) withdrew Aug 4; Bengs (I) modeled D-side. 5 polls disagree wildly |
| TN | Hagerty | R | R+26 | R+25 | Bradshaw (D) won Aug 6 primary. First poll arrived Sept 19 — single-poll average |
| TX | Open | R | R+10 | D+2.1 | Cornyn LOST primary. Paxton (R) vs Talarico (D). 56 polls; coin flip on PVI |
| VA | Warner | D | D+3 | — | Mizusawa (R) won Aug 4 primary. Safe D |
| WV | Capito | R | R+30 | — | Anderson (D) won the May 12 primary. No polling. Safe R |
| WY | Open | R | R+35 | — | Lummis retired. Hageman won Aug 18 primary 64.9% vs Byrd (D). Safe R |
| OH | Open | R | R+8 | D+1.77 | Vance vacancy. Brown (D) vs Husted (R, appt). Brown led 9 of 11 new polls. Lean D |

---

## Deployment

The site is **deployed and live**. CI/CD auto-deploys on push to `main`.

- **Backend**: Cloud Run (us-central1), scales to 0, 512Mi/1 CPU
- **Frontend**: Firebase Hosting (CDN)
- **CI/CD**: `.github/workflows/deploy.yml` — builds Docker image → Artifact Registry → Cloud Run, then builds React app → Firebase

**Local dev:**
```bash
# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8080

# Frontend (separate terminal)
cd frontend && npm run dev
# Vite proxies /api/* to localhost:8080
```

**Force cache refresh:**
```bash
curl -X POST "https://<CLOUD_RUN_URL>/api/forecast/refresh?secret=<ADMIN_SECRET>"
```

---

## Next development priorities

1. **Final economic refresh** — sentiment is current through the October preliminary (48.0,
   pulled Oct 26). The October final (~Oct 30) and the BEA Q3 advance GDP estimate
   (~Oct 29) are the last releases before the election. Pull sentiment from
   <https://www.sca.isr.umich.edu/files/tbmics.csv>. See `DATA-REFRESH.md`.
2. **Weight polling averages by depth** — every state's average counts the same whether it
   rests on 56 polls or 1. SC was the live example until Sept, when going from 1 poll to 3
   moved it two rating steps (Lean R → Safe R) — exactly the fragility this addresses. IL, LA,
   OK and TN now sit on a single poll each (LA's is D-sponsored). Widening σ when a state's average is thin
   is the biggest accuracy win still available, and the natural companion to the 0.75 cap.
3. **Review Achilles' quality score (ID)** — set to 4 by hand when he replaced Roth on the
   D side; no effect on the rating at R+32, but not data-driven.
4. **Refresh `governors.csv`** — not updated since Aug 28, now the stalest polling file in
   the repo. It feeds the β=0.10 coattails term, so second-order but drifting.
5. **Rewrite analysis_notes.md** — badly stale: it still discusses Platner in Maine and
   describes the race "at 601 days out". Ratings have moved twice since.
6. **Model documentation** — living document detailing forecasting methodology
6. **Regional correlation** — improve correlation structure in `monte_carlo.py` with state clusters
7. **Candidate quality pipeline** — integrate FEC fundraising data to auto-update quality scores
8. **Undecided allocation** — currently assumes even split; add challenger-lean adjustment
9. **Bayesian blending** — replace linear polling ramp with Bayesian update framework
10. **Historical model validation** — back-test against 2018, 2020, 2022 Senate results
11. **Methodology page** — add `/methodology` route explaining the model in detail
12. **Mobile responsive polish** — map is functional but could use mobile-optimised layout

---

## Security notes

- Service account key (`GCP_SA_KEY`) stored only in GitHub Secrets — never committed
- Cloud Run runs as a non-root user (see `backend/Dockerfile`)
- CORS restricted to Firebase Hosting domains only
- Admin refresh endpoint requires `ADMIN_SECRET` query param
- `.gitignore` blocks all `*.json` key files and `.env` files
