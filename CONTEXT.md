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
  app/data/races_2026.json       — Seed data: 35 races (PVI, candidates, polling averages, notes)
  app/data/environment.json      — National environment indicators (approval, GDP, sentiment)
  app/data/polls.csv             — All polls considered (408 entries, 25 states), with tracking metadata
  app/data/senate.csv            — NYT bulk export of all published Senate polls (~3.8k rows)
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

### Current state (Aug 28, 2026, 67 days to election)

The model blends **structural fundamentals** with **polling data** using a time-weighted
ramp. At 67 days out, polling weight `α ≈ 0.82`: the model is roughly
**18% fundamentals / 82% polling**. Polling now dominates, so a bad or thin state average
moves a race hard — that is why hypothetical-matchup polls get held out (see SC, OK).

### National environment: D+5.02

A four-component data-driven estimate (replaces earlier flat midterm penalty):

| Component | Coefficient | Current Value | Contribution |
|-----------|-------------|---------------|-------------|
| Base midterm penalty | — | — | D+1.50 |
| Presidential approval | 0.12 per net approval pt | −18.16 | D+2.18 |
| GDP growth | 0.3 per pt above 2.0% trend | 1.5% | D+0.15 |
| Consumer sentiment | 0.04 per pt below 85.0 baseline | 55.2 | D+1.19 |

Approval is **computed live** at runtime by `environment.py` from `potus-approval.csv`
(exponential time decay, 21-day half-life, ±2.0 pt partisan-sponsor adjustment, polls older
than 540 days dropped). The `presidential_approval` block in `environment.json` is only a
fallback and is overridden on every run — so dropping a fresh `potus-approval.csv` in is
all that is needed. GDP and sentiment are **manual** entries in `environment.json`
(BEA Q2 2026 advance estimate, released 7/30; U. Michigan July 2026 final, released 7/31).

### Fundamentals lean (per race)

```
fundamentals_lean = −PVI + environment_shift + incumbency(±2.5) + quality_diff × 0.8
```

### Blending

```
blended_lean = α × polling_average + (1 − α) × fundamentals_lean
α = max(0, min(1, (365 − days_until_election) / 365))
```

At ≥365 days out, α = 0 (fundamentals only). Ramps linearly to α = 1 on election day.

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

## Current forecast snapshot (Aug 28, 2026 — 67 days out)

| Metric | Value |
|--------|-------|
| Expected D seats | ~50.2 / 100 |
| D Senate control probability | ~45% |
| Net national environment | D+5.02 |
| Polling weight | ~82% polls / 18% fundamentals |
| D seats not up | 34 |
| R seats not up | 31 |

Control requires 51 (no D tie-breaker this cycle), which is why expected seats
sit above 50 while control probability sits below 50%.

### Race ratings

| Rating | Races |
|--------|-------|
| **Safe D** | NC, GA, NH, MN, and 9 others |
| **Lean D** | ME |
| **Toss-up** | AK, TX, OH-Special, MI |
| **Lean R** | IA |
| **Likely R** | NE |
| **Safe R** | FL, SC, MS, KS, KY, and 11 others |

Changes from the Aug 5 run: **OH-Special moved Lean R → Toss-up** (the average
crossed to Brown for the first time) and **NE moved Safe R → Likely R**.

Note: rating labels come from `prob_to_rating()` in `monte_carlo.py`, whose cutoffs
(Safe ≥85%) are looser than the scale documented in `analysis_notes.md` (Safe >95%).
That is why NC/GA/NH/MN read "Safe D" at ~88–94%. Unreconciled — see priorities.

### Key battlegrounds

| Race | PVI | Polling Avg | D Win Prob | Rating |
|------|-----|-------------|-----------|--------|
| NC (Cooper vs Whatley) | R+3 | D+7.7 | ~94% | Safe D |
| GA (Ossoff vs Mike Collins) | R+4 | D+6.6 | ~92% | Safe D |
| NH (Pappas vs Sununu/Brown) | D+1 | D+6.5 | ~91% | Safe D |
| MN (Flanagan vs Tafoya) | D+3 | D+4.6 | ~88% | Safe D |
| ME (Jackson vs Collins) | D+3 | D+1.3 | ~66% | Lean D |
| AK (Peltola vs Sullivan) | R+9 | D+1.9 | ~55% | Toss-up |
| TX (Talarico vs Paxton) | R+10 | D+1.6 | ~53% | Toss-up |
| OH Special (Brown vs Husted) | R+8 | D+0.4 | ~51% | Toss-up |
| MI (El-Sayed vs Rogers) | R+1 | R+0.7 | ~50% | Toss-up |
| IA (Turek vs Hinson) | R+10 | R+1.4 | ~32% | Lean R |
| NE (Osborn I vs Ricketts) | R+22 | R+0.7 | ~19% | Likely R |

### Polling data coverage

22 states have polling data incorporated: AK, AL, AR, FL, GA, IA, ID, KS, KY, MA, ME,
MI, MN, MS, MT, NC, NE, NH, OH, RI, SD, TX. (SC and OK have polling but both are held
out — see below.)

All polls tracked in `polls.csv` (408 entries, 274 included in averages). Bulk NYT export
in `senate.csv`; prior drops in `app/data/archive/`.

**How a polling average is produced** (there is no script — this is done by hand):
`senate.csv` (raw NYT bulk export, one row per candidate per question) → `polls.csv`
(one curated row per matchup, with an `included_in_average` yes/no flag and a reason in
`notes`) → `polling_average` in `races_2026.json` is the **unweighted mean of
`dem_pct − rep_pct` across rows flagged `yes`** for that state. No time decay, no
sample-size or pollster weighting. Multi-matchup surveys contribute one row per matchup,
so a single poll testing five opponents counts five times — watch for that when one
sponsored survey is the only data (it is why SC and OK are currently held out).

Curation rules applied to the Aug 28 drop:
- One row per distinct matchup. Where a survey published several population screens of
  the same matchup, the LV screen is kept and the others flagged `no` (NC/Elon published
  three, NC/High Point and MI/TIPP two each).
- Where a survey asked both a two-party and a ballot-realistic multi-way question, the
  multi-way one is kept (MT with Bodnar, MS with Pinkins).
- Where a nomination is genuinely unresolved, every live matchup is kept (NH Sununu+Brown,
  MA Markey+Moulton). Where the only data is one sponsored poll of an undecided field, the
  state is held out entirely (SC, OK).
- When a primary resolves, the loser's matchups are re-flagged `no` (MN: four Craig rows
  dropped after Aug 11; SD: three Beaudion rows dropped after his withdrawal).

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
| AL | Open | R | R+27 | R+15 | Tuberville → Gov race. Moore (R) vs Wess (D). Safe R |
| AK | Sullivan | R | R+9 | D+1.91 | Peltola challenging. Aug 18 top-4 primary result not yet in data; RCV in Nov |
| AR | Cotton | R | R+24 | R+9.4 | Safe R |
| CO | Hickenlooper | D | D+4 | — | Baisley (R) nominee. Safe D |
| DE | Coons | D | D+8 | — | Safe D |
| FL | Moody (appt) | R | R+5 | R+6.79 | Rubio vacancy. Moody (R, appt). Aug 18 D primary result not yet in data |
| GA | Ossoff | D | R+4 | D+6.55 | Top R target. Ossoff vs Mike Collins |
| ID | Risch | R | R+32 | R+17 | Safe R |
| IL | Open | D | D+17 | — | Durbin retired. Stratton vs Tracy. Safe D |
| IA | Open | R | R+10 | R+1.39 | Ernst retired. Hinson (R) vs Turek (D). Very close |
| KS | Marshall | R | R+20 | R+4.25 | Marshall vs Hamilton. Safe R |
| KY | Open | R | R+26 | R+6.33 | McConnell retired. Barr (R) vs Booker (D) |
| LA | Open | R | R+20 | — | Cassidy LOST primary. Letlow (R) vs Davis (D). Safe R |
| ME | Collins | R | D+3 | D+1.32 | Platner withdrew; Jackson (D) nominated Jul 25. Toss-up |
| MA | Markey | D | D+30 | D+23.32 | Markey vs Moulton primary Sept 1. Safe D |
| MI | Open | D | R+1 | R+0.69 | Peters retired. El-Sayed won Aug 4 primary vs Rogers |
| MN | Open | D | D+3 | D+4.6 | Smith retired. Flanagan won the Aug 11 primary over Craig; vs Tafoya |
| MS | Hyde-Smith | R | R+18 | R+4.5 | Safe R |
| MT | Open | R | R+18 | R+20.5 | Daines withdrew. Alme (R) vs Bankhead (D) + Bodnar (I) — 3-way |
| NE | Ricketts (appt) | R | R+22 | R+0.67 | Osborn (I) tied in polls. Modeled on D side |
| NH | Open | D | D+1 | D+6.48 | Shaheen retired. Pappas vs Sununu/Brown (primary Sept 8) |
| NJ | Booker | D | D+14 | — | Safe D |
| NM | Luján | D | D+4 | — | R candidate disqualified. Unopposed |
| NC | Open | R | R+3 | D+7.72 | Tillis retired. Cooper vs Whatley. Top D pickup |
| OK | Open | R | R+26 | — | Mullin → DHS. Hern (R) nominee. D nominee unresolved; first poll held out |
| OR | Merkley | D | D+8 | — | Safe D |
| RI | Reed | D | D+18 | D+18.5 | Safe D |
| SC | Open | R | R+11 | — | Graham seat vacant. Aug 25 R runoff (Graham/Norman) result not yet in data. Polling held out |
| SD | Rounds | R | R+27 | R+11.5 | Beaudion (D) withdrew Aug 4; Bengs (I) modeled D-side. 2 polls disagree wildly |
| TN | Hagerty | R | R+26 | — | Safe R |
| TX | Open | R | R+10 | D+1.6 | Cornyn LOST primary. Paxton (R) vs Talarico (D) — Talarico leads |
| VA | Warner | D | D+3 | — | Mizusawa (R) won Aug 4 primary. Safe D |
| WV | Capito | R | R+30 | — | Safe R |
| WY | Open | R | R+35 | — | Lummis retired. Hageman favored (primary Aug 18). Safe R |
| OH | Open | R | R+8 | D+0.4 | Vance vacancy. Brown (D) vs Husted (R, appt) |

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

1. **Resolve pending nominations** — SC (Aug 25 R runoff: Graham vs Norman), FL (Aug 18 D
   primary), AK (Aug 18 top-4), WY (Aug 18). None of these results are in the current data;
   SC and OK polling stays held out until their nominees are known.
2. **Update analysis_notes.md** — ratings changed again after the Aug 28 drop (OH → Toss-up,
   NE → Likely R, AR and SD averages moved sharply on thin data)
3. **Model documentation** — living document detailing forecasting methodology
4. **Regional correlation** — improve correlation structure in `monte_carlo.py` with state clusters
5. **Candidate quality pipeline** — integrate FEC fundraising data to auto-update quality scores
6. **Undecided allocation** — currently assumes even split; add challenger-lean adjustment
7. **Bayesian blending** — replace linear polling ramp with Bayesian update framework
8. **Historical model validation** — back-test against 2018, 2020, 2022 Senate results
9. **Methodology page** — add `/methodology` route explaining the model in detail
10. **Mobile responsive polish** — map is functional but could use mobile-optimised layout

---

## Security notes

- Service account key (`GCP_SA_KEY`) stored only in GitHub Secrets — never committed
- Cloud Run runs as a non-root user (see `backend/Dockerfile`)
- CORS restricted to Firebase Hosting domains only
- Admin refresh endpoint requires `ADMIN_SECRET` query param
- `.gitignore` blocks all `*.json` key files and `.env` files
