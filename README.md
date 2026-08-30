# 2026 Senate Forecast

A probabilistic forecast for the 2026 US Senate midterm elections, built with React + FastAPI and deployed on Google Cloud Platform.

---

## Overview

The site forecasts all 35 Senate seats on the November 2026 ballot: 33 Class II seats plus 2 vacancy elections (OH and FL, filling the seats vacated by J.D. Vance and Marco Rubio). It features:

- **Interactive US choropleth map** — states colored by projected win probability
- **Chamber control probability** — probability the Democrats or Republicans control the Senate post-election, with a full seat-distribution histogram
- **Per-race detail panel** — win probability, fundamentals lean, Cook PVI, candidate info, and polling average
- **Monte Carlo engine** — 40,000 simulations per run, with correlated national errors producing realistic wave scenarios
- **National environment model** — data-driven estimates from presidential approval, GDP growth, and consumer sentiment

Live site: [https://elections.eddievb.com](https://elections.eddievb.com) (also: [https://election-forecast-489820.web.app](https://election-forecast-489820.web.app))

---

## Current Forecast Snapshot (August 30, 2026)

| Metric | Value |
|--------|-------|
| Expected D seats | ~50.0 / 100 |
| D Senate control probability | ~42% |
| Net national environment | D+5.10 |
| Days to election | 65 |
| Polling weight | ~62% Senate polls / 38% everything else |

Democrats need 51 seats for control (the model does not credit a tie-breaking
vice president, since the VP is Republican this cycle). The expected seat count
sitting right at 50 while control probability sits below 50% is exactly what
that asymmetry looks like.

### Key Battlegrounds

| Race | Rating | D Win Prob | Polling Avg |
|------|--------|-----------|-------------|
| MN (Flanagan vs Tafoya) | Safe D | ~90% | D+4.6 |
| NC (Cooper vs Whatley) | Safe D | ~90% | D+7.7 |
| GA (Ossoff vs Collins) | Safe D | ~89% | D+6.6 |
| NH (Pappas vs Sununu/Brown) | Safe D | ~87% | D+6.1 |
| ME (Jackson vs Collins) | Lean D | ~69% | D+1.3 |
| MI (El-Sayed vs Rogers) | Lean D | ~57% | R+0.7 |
| AK (Peltola vs Sullivan) | Toss-up | ~50% | D+1.9 |
| OH vacancy (Brown vs Husted) | Toss-up | ~48% | D+0.4 |
| TX (Talarico vs Paxton) | Lean R | ~42% | D+1.7 |
| SC vacancy (Andrews vs D. Graham) | Lean R | ~32% | EVEN |
| IA (Turek vs Hinson) | Likely R | ~28% | R+1.4 |
| NE (Osborn I vs Ricketts) | Safe R | ~6% | R+0.7 |
| FL vacancy (Nixon vs Moody) | Safe R | ~5% | R+10.1 |

> **South Carolina is the weakest number on this page.** Its average is one
> D-sponsored poll showing a 41-41 tie in an R+11 seat. That single poll is the
> entire difference between Safe R and Lean R there. Treat SC as poorly
> measured rather than genuinely competitive until more polling lands.

> **Rating labels are looser than the analysis scale.** `prob_to_rating()` in
> `monte_carlo.py` labels anything ≥85% "Safe", while
> [analysis_notes.md](backend/app/data/analysis_notes.md) reserves "Safe" for
> >95%. That is why NC/GA/NH/MN read "Safe D" at 88–94%. The two scales are
> not yet reconciled.

See [analysis_notes.md](backend/app/data/analysis_notes.md) for detailed
race-by-race analysis and [polls.csv](backend/app/data/polls.csv) for all 408
polls considered — 257 included in averages across 24 states.

---

## Architecture

```
┌─────────────────────┐     HTTPS      ┌───────────────────────────┐
│  Firebase Hosting   │ ←────────────  │  Vite + React + TypeScript│
│  (frontend CDN)     │                │  react-simple-maps         │
└─────────────────────┘                │  recharts, Tailwind CSS    │
         │ /api/*                      └───────────────────────────┘
         ▼
┌─────────────────────┐
│  Cloud Run          │
│  FastAPI (Python)   │
│  · Monte Carlo      │
│  · 30 min cache     │
└─────────────────────┘
```

**GCP services used (cost-optimized):**

| Service | Purpose | Est. monthly cost |
|---|---|---|
| Firebase Hosting | Frontend static site | Free tier |
| Cloud Run | Backend API (scales to 0) | ~$0–2 |
| Artifact Registry | Docker image storage | ~$0.10/GB |

**Total expected cost: well under $5/month** for a low-traffic development/demo site.

---

## Model

### Inputs

| Category | Variable | Source |
|---|---|---|
| Structural | Cook PVI | `races_2026.json` |
| Structural | Incumbency advantage (+2.5 pp) | Computed |
| Environment | National environment shift (approval, GDP, sentiment) | `potus-approval.csv` + `environment.json` → `environment.py` |
| Candidate | Quality score differential | Seed data (0–10 scale) |
| Seat | Open-seat volatility | Seed data flag |
| Coattails | Gubernatorial over/under-performance | `governors.csv` → `governors.py` |
| Ballot | Ballot-structure adjustment (AK only) | `ballot_adjustment` in seed data |
| Polling | Head-to-head average (D − R) | `polls.csv` + `senate.csv` → `polling_average` in seed data |

### National Environment (v0.2.0)

The model uses a four-component national environment estimate that replaces the earlier flat midterm penalty:

| Component | Coefficient | Current Value | Contribution |
|-----------|------------|---------------|-------------|
| Base midterm penalty | — | — | D+1.50 |
| Presidential approval | 0.12 per net approval pt | −17.64 | D+2.12 |
| GDP growth | 0.3 per pt above 2.0% trend | 1.5% | D+0.15 |
| Consumer sentiment | 0.04 per pt below 85.0 baseline | 51.7 | D+1.33 |

**Net environment: D+5.10**

Presidential approval is computed live from `potus-approval.csv` — a
time-decay-weighted average (half-life 21 days, partisan-adjusted, polls older
than 540 days dropped), so the model automatically reflects the latest data
whenever the CSV is updated. The file currently holds 989 polls through 8/28/26,
896 of them inside the window. The `presidential_approval` block in
`environment.json` is a fallback only and is overridden on every run.

GDP and sentiment are **manual** entries in `backend/app/data/environment.json`,
currently the BEA Q2 2026 second estimate (+1.5% annualized, unchanged from the
advance, released 8/26/26) and University of Michigan August 2026 final (51.7,
released 8/28/26). See `DATA-REFRESH.md` for the refresh routine and release
calendar.

### Gubernatorial coattails

Where a state votes for governor on the same ballot, the Senate candidate gets a
small push from how far the governor race is running from that state's partisan
baseline.

The raw correlation between same-state Senate and gubernatorial margins is high
(r = 0.59 across the 45 concurrent races since 2018) — but nearly all of that is
shared state partisanship, which PVI already captures. Using it directly would
double-count. What is actually incremental is the *residual* relationship:

```
1. Senate margin   ~ PVI  →  Senate residual        (fit within each cycle,
2. Governor margin ~ PVI  →  Governor residual       which absorbs that cycle's
3. Senate residual ~ Governor residual → β           national environment)

β = 0.119   (SE 0.050, t = 2.36, r = 0.34)
bootstrap 90% CI [0.036, 0.241]; Theil–Sen 0.142
```

So roughly **10–15% of a governor candidate's over-performance shows up in the
Senate race** — real, but an order of magnitude smaller than the raw correlation
suggests. The model uses **β = 0.10**, the conservative end, because the estimate
is unstable across cycles (2018 β = 0.25, 2022 β = 0.02) and the largest
residuals are exactly the personality-driven cases that transfer least — the
Phil Scott / Charlie Baker / Larry Hogan pattern of a Republican winning a
governor's race in a blue state whose Senate seat never moves.

Two dampers keep it modest: a hard **±2.0 point cap**, and an `n/(n+2)` shrink
toward zero so a state with one stale gubernatorial poll cannot move its Senate
race much. In the current run the largest adjustment on a competitive race is
**NH at −0.97** (Ayotte running well ahead in the governor race), and most are
under half a point.

### Blending

```
blended_lean = α × polling_average + (1 − α) × fundamentals_lean
             + ballot_adjustment

α = 0.75 × max(0, min(1, (365 − days_until_election) / 365))
```

At 65 days out, `α ≈ 0.62`: the model is **62% Senate polling, 38% everything
else**. The ramp is capped so that **Senate polling never exceeds 75% of the
mix, even on election day.** Public state-level polling error has been large and
directionally persistent in recent cycles, so the remaining quarter stays with
inputs that carry independent information and fail in different ways —  PVI, the
national environment (approval, GDP, sentiment), incumbency, candidate quality
and the gubernatorial signal.

A thin or unrepresentative state average still moves a race hard, which is why
polls testing a nomination that has not been decided are held out rather than
averaged in, and why matchups are re-flagged the moment a primary resolves.

`ballot_adjustment` is applied at full strength rather than blended, because it
describes the ballot voters actually receive. Only Alaska uses it — see below.

### Alaska: two candidates named Dan Sullivan

The November ballot carries both **Dan Sullivan**, the Republican incumbent, and
**Daniel J. Sullivan Jr.**, a Petersburg logger listed with no party affiliation
who took 2.5% in the August top-four primary and polls 3–5%. The state tried to
keep him off the ballot as a deliberate attempt to confuse voters; the Alaska
Supreme Court allowed him on.

Alaska uses ranked-choice voting, which matters enormously here: most votes cast
for the wrong Sullivan flow back to the incumbent in later rounds. The residual
benefit to Peltola is only the share that *never returns*:

```
share × intent × non-return  =  0.030 × 0.70 × 0.45  ≈  1.0 pt
```

- **share 3.0%** — the name-alike's first-round vote (2.5% in the primary, 3–5% in polls)
- **intent 0.70** — the fraction of that meant for the incumbent rather than genuine protest votes
- **non-return 0.45** — the fraction that fails to reach Sullivan in later rounds, either exhausting or transferring elsewhere. Alaska's overall ballot exhaustion runs 5–8%, but this subgroup is far higher: a voter who misidentified the candidate has no reason to rank the *other* Sullivan second.

The model applies **+1.0 point to Peltola**, with a plausible range of +0.4 to
+2.3. The state's polling average is read as the RCV final round, which is
head-to-head, so this does not double-count.

### Uncertainty / Sigma

```
σ_per_state = √(σ_fundamentals² + σ_polling² + σ_residual²)

σ_fundamentals = 7.0 × (1 − α)    # large early, shrinks as polls arrive
σ_polling       = 2.5 × α          # pure polling error
σ_residual      = 2.8              # state-specific floor

# α caps at 0.75, so σ_fundamentals never falls below 1.75 — the model stays
# permanently uncertain about the share it does not give to Senate polling.
```

Open seats receive an additional +1.5 pp of uncertainty (added in quadrature: `σ = √(σ² + 1.5²)`).

### Simulation

```python
# Per simulation (40,000 total):
nat_error  ~ N(0, 2.5)             # national wave — all states move together
state_err  ~ N(0, σ_per_state)     # independent per state
margin_i   = blended_lean_i + nat_error + state_err_i
D_wins_i   = margin_i > 0
```

The shared national error produces the cross-state correlation essential for realistic chamber-control distributions.

### Planned Improvements

1. **Weight polling averages by depth**: every state's `polling_average` currently counts the same regardless of whether it rests on 27 polls or 1. South Carolina is the live example — a single sponsored poll carries the same 62% weight as Texas's 27. Widening σ when a state's average is thin would be the single biggest accuracy win available.
2. **Correlated state errors**: currently a single national factor. A full covariance matrix (regional clusters, open-seat correlation) would improve accuracy.
3. **Candidate quality**: currently a coarse 0–10 score. Plan to integrate FEC fundraising data and name-recognition tiers.
4. **Undecided allocation**: no model yet; assumes they split evenly. Will add a challenger-lean adjustment.
5. **Bayesian blending**: replace the linear polling ramp with a Bayesian update framework as more polls arrive.
6. **Reconcile rating labels** with the stricter scale in `analysis_notes.md`.

---

## Data Files

| File | Description |
|------|-------------|
| `backend/app/data/races_2026.json` | Seed data for all 35 races (PVI, candidates, polling averages, notes) |
| `backend/app/data/environment.json` | Economic environment indicators (GDP, consumer sentiment, unemployment) |
| `backend/app/data/potus-approval.csv` | Raw presidential approval polls (989 polls through 8/28/26); read by `environment.py` at runtime |
| `backend/app/data/senate.csv` | Raw NYT Senate polling bulk export (~3,800 rows); curated by hand into `polls.csv` |
| `backend/app/data/governors.csv` | Raw NYT gubernatorial polling bulk export; read live by `governors.py` for the coattail signal |
| `backend/app/data/polls.csv` | Curated Senate polls (408 rows, 257 included, 24 states) with sources, sponsors, dates, and inclusion flags |
| `backend/app/data/archive/` | Dated snapshots of prior `senate.csv` / `potus-approval.csv` drops, kept so each new drop can be diffed against the last |
| `backend/app/data/analysis_notes.md` | Detailed race-by-race analysis, tiered ratings, and methodology |
| `backend/app/data/races_2028.json` | Class III seed data for the next cycle (not active) |
| `DATA-REFRESH.md` | Running checklist of hand-fetched inputs that need updating |

### How a polling average is produced

There is **no averaging script** — this step is done by hand, and the details matter:

```
senate.csv          one row per candidate per question (NYT bulk export)
    ↓  curate by hand
polls.csv           one row per matchup, with included_in_average yes/no + reason
    ↓  unweighted mean of (dem_pct − rep_pct) over rows flagged "yes"
races_2026.json     polling_average
```

The average is a plain unweighted mean: no time decay, no sample-size weighting,
no pollster-rating weighting. (The *approval* average in `environment.py` is a
different pipeline and does use time decay and a partisan adjustment.)

The trap to watch for: **one survey that publishes N questions contributes N
rows and gets N× the weight.** A pollster testing three likely-voter screens of
the same matchup, or five hypothetical opponents, will quietly dominate a
state's average. The curation rules that follow from this:

- One row per distinct matchup; where a survey publishes several population
  screens of it, keep the likely-voter version and flag the rest `no`.
- Where a survey asks both a two-party and a ballot-realistic multi-way
  question, keep the one that matches the actual November ballot (MT, MS).
- Where a nomination is genuinely unresolved, keep every live matchup (NH, MA)
  — or, if the data is a single sponsored poll of an undecided field, hold the
  state out entirely (SC, OK).
- When a primary resolves, re-flag the losing candidate's matchups `no`, or the
  average keeps measuring someone who is not on the ballot (MN, SD).

After any new `senate.csv` drop, recompute every state's mean from `polls.csv`
and diff it against the stored values — they should match to 0.01 before you
start editing.

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit as needed
uvicorn app.main:app --reload --port 8080
# API docs: http://localhost:8080/api/docs
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # leave VITE_API_URL empty to use Vite proxy
npm run dev
# App: http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8080`, so you need the backend running.

---

## Deployment

### First-time GCP setup

```bash
gcloud auth login
chmod +x infrastructure/setup.sh
./infrastructure/setup.sh
```

This script:
1. Enables required GCP APIs
2. Creates an Artifact Registry Docker repository
3. Creates a `github-actions-deploy` service account with minimal permissions
4. Prints the SA JSON key — add this to GitHub Secrets as `GCP_SA_KEY`
5. Deploys a placeholder Cloud Run service

Then initialize Firebase Hosting:

```bash
cd frontend
firebase login
firebase init hosting --project election-forecast-489820
```

Add secrets to the GitHub repo (`Settings → Secrets → Actions`):

| Secret | Value |
|---|---|
| `GCP_SA_KEY` | JSON output from setup.sh |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase Admin SDK JSON (download from Firebase console → Project Settings → Service accounts) |
| `ADMIN_SECRET` | Any strong random string (used to force model refresh) |

### CI/CD (GitHub Actions)

Every push to `main` triggers `.github/workflows/deploy.yml`:

1. Build and push Docker image to Artifact Registry
2. Deploy new image to Cloud Run (zero-downtime)
3. Build React app with `VITE_API_URL` set to the Cloud Run URL
4. Deploy static build to Firebase Hosting

---

## Repository Structure

```
election-forecast/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app + CORS
│   │   ├── routes/
│   │   │   └── forecast.py     # /api/forecast endpoint + cache
│   │   ├── model/
│   │   │   ├── fundamentals.py # PVI, incumbency, environment lean
│   │   │   ├── environment.py  # National environment model + approval average
│   │   │   ├── governors.py    # Gubernatorial coattail signal
│   │   │   └── monte_carlo.py  # 40k simulation engine
│   │   └── data/
│   │       ├── races_2026.json    # Seed data for all 35 races
│   │       ├── races_2028.json    # Class III seed data (not active)
│   │       ├── environment.json   # Economic environment indicators
│   │       ├── potus-approval.csv # Presidential approval polls (live input)
│   │       ├── senate.csv         # Raw NYT Senate polling bulk export
│   │       ├── governors.csv      # Raw NYT gubernatorial polling (live input)
│   │       ├── polls.csv          # Curated polls with inclusion flags
│   │       ├── archive/           # Dated snapshots of prior data drops
│   │       └── analysis_notes.md  # Detailed race analysis
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── USMap.tsx           # Interactive choropleth map
│   │   │   ├── ChamberControl.tsx  # Seat probability bar + histogram
│   │   │   ├── RaceList.tsx        # Grouped race list with mini bars
│   │   │   ├── RaceDetail.tsx      # Selected race detail panel
│   │   │   └── Header.tsx          # Top bar with metadata + environment
│   │   ├── hooks/useForecast.ts    # TanStack Query data fetching
│   │   ├── types/index.ts          # TypeScript interfaces
│   │   └── utils/                  # Color scales, state lookup, formatters
│   ├── public/
│   │   ├── favicon.svg            # Bar chart favicon
│   │   ├── favicon.png            # PNG favicon + apple-touch-icon
│   │   ├── og-image.svg           # Open Graph share image (source)
│   │   └── og-image.png           # Open Graph share image (1200×630)
│   ├── firebase.json               # Firebase Hosting config
│   └── package.json
├── infrastructure/
│   └── setup.sh                # One-shot GCP provisioning script
└── .github/workflows/
    └── deploy.yml              # CI/CD pipeline
```

---

## Contributing / Updating the Model

1. **Add Senate polls**: drop the new NYT bulk export in as `senate.csv`, moving the previous one to `archive/senate-<date>.csv` first. Diff the two by `poll_id` to find what is actually new, curate those matchups into `polls.csv` by hand (see [How a polling average is produced](#how-a-polling-average-is-produced) — there is no script), re-flag any matchup whose candidate is no longer running, then recompute the `polling_average` fields in `races_2026.json`.
2. **Add approval polls**: drop in a new `potus-approval.csv` — the model reads it live at runtime, no other changes needed
3. **Update economic data**: edit `environment.json` with the latest GDP and consumer sentiment figures
4. **Update candidate info**: edit the `candidates` block and `"quality_score"` fields in `races_2026.json`
5. **Change fundamentals**: edit `pvi` or model constants in `backend/app/model/fundamentals.py`
6. **Tune model parameters**: adjust `SIGMA_NATIONAL`, `N_SIMS`, etc. in `backend/app/model/monte_carlo.py`

After any backend change, push to `main` to auto-deploy. The cache refreshes every 30 minutes; to force an immediate refresh:

```bash
curl -X POST "https://<CLOUD_RUN_URL>/api/forecast/refresh?secret=<ADMIN_SECRET>"
```
