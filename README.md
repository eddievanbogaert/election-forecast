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

## Current Forecast Snapshot (August 28, 2026)

| Metric | Value |
|--------|-------|
| Expected D seats | ~50.2 / 100 |
| D Senate control probability | ~45% |
| Net national environment | D+5.02 |
| Days to election | 67 |
| Polling weight | ~82% polls / 18% fundamentals |

Democrats need 51 seats for control (the model does not credit a tie-breaking
vice president, since the VP is Republican this cycle). The expected seat count
sitting just above 50 while control probability sits below 50% is exactly what
that asymmetry looks like.

### Key Battlegrounds

| Race | Rating | D Win Prob | Polling Avg |
|------|--------|-----------|-------------|
| NC (Cooper vs Whatley) | Safe D | ~94% | D+7.7 |
| GA (Ossoff vs Collins) | Safe D | ~92% | D+6.6 |
| NH (Pappas vs Sununu/Brown) | Safe D | ~91% | D+6.5 |
| MN (Flanagan vs Tafoya) | Safe D | ~88% | D+4.6 |
| ME (Jackson vs Collins) | Lean D | ~66% | D+1.3 |
| AK (Peltola vs Sullivan) | Toss-up | ~55% | D+1.9 |
| TX (Talarico vs Paxton) | Toss-up | ~53% | D+1.6 |
| OH vacancy (Brown vs Husted) | Toss-up | ~51% | D+0.4 |
| MI (El-Sayed vs Rogers) | Toss-up | ~50% | R+0.7 |
| IA (Turek vs Hinson) | Lean R | ~32% | R+1.4 |
| NE (Osborn I vs Ricketts) | Likely R | ~19% | R+0.7 |
| FL vacancy (TBD vs Moody) | Safe R | ~8% | R+6.8 |

> **Rating labels are looser than the analysis scale.** `prob_to_rating()` in
> `monte_carlo.py` labels anything ≥85% "Safe", while
> [analysis_notes.md](backend/app/data/analysis_notes.md) reserves "Safe" for
> >95%. That is why NC/GA/NH/MN read "Safe D" at 88–94%. The two scales are
> not yet reconciled.

See [analysis_notes.md](backend/app/data/analysis_notes.md) for detailed
race-by-race analysis and [polls.csv](backend/app/data/polls.csv) for all 408
polls considered — 274 included in averages across 22 states.

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
| Polling | Head-to-head average (D − R) | `polls.csv` + `senate.csv` → `polling_average` in seed data |

### National Environment (v0.2.0)

The model uses a four-component national environment estimate that replaces the earlier flat midterm penalty:

| Component | Coefficient | Current Value | Contribution |
|-----------|------------|---------------|-------------|
| Base midterm penalty | — | — | D+1.50 |
| Presidential approval | 0.12 per net approval pt | −18.16 | D+2.18 |
| GDP growth | 0.3 per pt above 2.0% trend | 1.5% | D+0.15 |
| Consumer sentiment | 0.04 per pt below 85.0 baseline | 55.2 | D+1.19 |

**Net environment: D+5.02**

Presidential approval is computed live from `potus-approval.csv` — a
time-decay-weighted average of 953 polls (half-life 21 days, partisan-adjusted,
polls older than 540 days dropped), so the model automatically reflects the
latest data whenever the CSV is updated. The `presidential_approval` block in
`environment.json` is a fallback only and is overridden on every run.

GDP and sentiment are **manual** entries in `backend/app/data/environment.json`,
currently BEA Q2 2026 advance estimate (+1.5% annualized, released 7/30/26) and
University of Michigan July 2026 final (55.2, released 7/31/26).

### Blending

```
blended_lean = α × polling_average + (1 − α) × fundamentals_lean

α = max(0, min(1, (365 − days_until_election) / 365))
```

At 67 days out, `α ≈ 0.82`: the model is **18% fundamentals, 82% polling**. Polling weight ramps linearly to 100% over the final year before the election.

Because polling now dominates, a thin or unrepresentative state average moves a race hard. That is why hypothetical matchups — polls testing a nomination that has not been decided — are held out of the averages rather than averaged in (see SC and OK).

### Uncertainty / Sigma

```
σ_per_state = √(σ_fundamentals² + σ_polling² + σ_residual²)

σ_fundamentals = 7.0 × (1 − α)    # large early, shrinks as polls arrive
σ_polling       = 2.5 × α          # pure polling error
σ_residual      = 2.8              # state-specific floor
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

1. **Correlated state errors**: currently a single national factor. A full covariance matrix (regional clusters, open-seat correlation) would improve accuracy.
2. **Candidate quality**: currently a coarse 0–10 score. Plan to integrate FEC fundraising data and name-recognition tiers.
3. **Undecided allocation**: no model yet; assumes they split evenly. Will add a challenger-lean adjustment.
4. **Bayesian blending**: replace the linear polling ramp with a Bayesian update framework as more polls arrive.

---

## Data Files

| File | Description |
|------|-------------|
| `backend/app/data/races_2026.json` | Seed data for all 35 races (PVI, candidates, polling averages, notes) |
| `backend/app/data/environment.json` | Economic environment indicators (GDP, consumer sentiment, unemployment) |
| `backend/app/data/potus-approval.csv` | Raw presidential approval polls (953 polls); read by `environment.py` at runtime |
| `backend/app/data/senate.csv` | Raw NYT Senate polling bulk export (~3,800 rows); curated by hand into `polls.csv` |
| `backend/app/data/polls.csv` | Curated Senate polls (408 rows, 274 included, 22 states) with sources, sponsors, dates, and inclusion flags |
| `backend/app/data/archive/` | Dated snapshots of prior `senate.csv` / `potus-approval.csv` drops, kept so each new drop can be diffed against the last |
| `backend/app/data/analysis_notes.md` | Detailed race-by-race analysis, tiered ratings, and methodology |
| `backend/app/data/races_2028.json` | Class III seed data for the next cycle (not active) |

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
│   │   │   └── monte_carlo.py  # 40k simulation engine
│   │   └── data/
│   │       ├── races_2026.json    # Seed data for all 35 races
│   │       ├── races_2028.json    # Class III seed data (not active)
│   │       ├── environment.json   # Economic environment indicators
│   │       ├── potus-approval.csv # Presidential approval polls (live input)
│   │       ├── senate.csv         # Raw NYT Senate polling bulk export
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
