# 2026 Senate Forecast

A FiveThirtyEight-style probabilistic forecast for the 2026 US Senate midterm elections, built with React + FastAPI and deployed on Google Cloud Platform.

---

## Overview

The site forecasts all 35 Senate seats in play in November 2026 (33 Class II seats + OH and FL special elections). It features:

- **Interactive US choropleth map** — states colored by projected win probability
- **Chamber control probability** — probability the Democrats or Republicans control the Senate post-election, with a full seat-distribution histogram
- **Per-race detail panel** — win probability, fundamentals lean, Cook PVI, candidate info, and polling average
- **Monte Carlo engine** — 40,000 simulations per run, with correlated national errors producing realistic wave scenarios
- **National environment model** — data-driven estimates from presidential approval, GDP growth, and consumer sentiment

Live site: [https://election-forecast-489820.web.app](https://election-forecast-489820.web.app)

---

## Current Forecast Snapshot (March 2026)

| Metric | Value |
|--------|-------|
| Expected D seats | ~48.5 / 100 |
| D Senate control probability | ~15% |
| Net national environment | D+3.54 |
| Days to election | ~601 |
| Polling weight | ~35% polls / 65% fundamentals |

### Key Battlegrounds

| Race | Rating | D Win Prob | Polling Avg |
|------|--------|-----------|-------------|
| NC (Cooper vs Whatley) | Likely D | ~76% | D+7 |
| GA (Ossoff vs TBD) | Lean D | ~70% | D+5.3 |
| NH (Pappas vs TBD) | Lean D | ~62% | — |
| MI (TBD vs Rogers) | Lean D | ~55% | R+1 |
| ME (TBD vs Collins) | Toss-up | ~55% | D+2.5 |
| AK (Peltola vs Sullivan) | Lean R | ~40% | D+2 |
| FL (Jenkins vs Moody) | Lean R | ~35% | — |
| OH Special (Brown vs Husted) | Lean R | ~34% | R+2 |

See [analysis_notes.md](backend/app/data/analysis_notes.md) for detailed race-by-race analysis and [polls.csv](backend/app/data/polls.csv) for all polling data considered.

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
| Environment | National environment shift (approval, GDP, sentiment) | `environment.json` → `environment.py` |
| Candidate | Quality score differential | Seed data (0–10 scale) |
| Seat | Open-seat volatility | Seed data flag |
| Polling | Head-to-head average (D − R) | `polling_average` field in seed data |

### National Environment (v0.2.0)

The model uses a four-component national environment estimate that replaces the earlier flat midterm penalty:

| Component | Coefficient | Current Value | Contribution |
|-----------|------------|---------------|-------------|
| Base midterm penalty | — | — | D+1.50 |
| Presidential approval | 0.12 per net approval pt | −11.0 | D+1.32 |
| GDP growth | 0.3 per pt above 2.0% trend | 2.3% | D−0.09 |
| Consumer sentiment | 0.04 per pt below 85.0 baseline | 64.7 | D+0.81 |

**Net environment: D+3.54**

Data sourced from RealClearPolitics (approval, 16-poll average), BEA (GDP), and University of Michigan (sentiment). Updated in `backend/app/data/environment.json`.

### Blending

```
blended_lean = α × polling_average + (1 − α) × fundamentals_lean

α = max(0, min(1, (365 − days_until_election) / 365))
```

At ~601 days out, `α ≈ 0.35`: the model is **65% fundamentals, 35% polling**. Polling weight ramps linearly to 100% over the final year before the election.

### Uncertainty / Sigma

```
σ_per_state = √(σ_fundamentals² + σ_polling² + σ_residual²)

σ_fundamentals = 7.0 × (1 − α)    # large early, shrinks as polls arrive
σ_polling       = 2.5 × α          # pure polling error
σ_residual      = 2.8              # state-specific floor
```

Open seats receive an additional +1.5 pp of uncertainty.

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
| `backend/app/data/environment.json` | National environment indicators (approval, GDP, sentiment) |
| `backend/app/data/polls.csv` | All polls considered, with sources, sponsors, dates, and inclusion flags |
| `backend/app/data/analysis_notes.md` | Detailed race-by-race analysis, tiered ratings, and methodology |

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
│   │   │   ├── environment.py  # National environment model
│   │   │   └── monte_carlo.py  # 40k simulation engine
│   │   └── data/
│   │       ├── races_2026.json    # Seed data for all 35 races
│   │       ├── environment.json   # National environment indicators
│   │       ├── polls.csv          # All polls considered
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

1. **Add a poll**: edit `races_2026.json`, set `"polling_average": <D_margin>` for the race. Log the poll in `polls.csv`.
2. **Update candidate info**: edit the `candidates` block and `"quality_score"` fields
3. **Update environment data**: edit `environment.json` with latest approval/GDP/sentiment figures
4. **Change fundamentals**: edit `pvi` or model constants in `backend/app/model/fundamentals.py`
5. **Tune model parameters**: adjust `SIGMA_NATIONAL`, `N_SIMS`, etc. in `backend/app/model/monte_carlo.py`

After any backend change, push to `main` to auto-deploy. The cache refreshes every 30 minutes; to force an immediate refresh:

```bash
curl -X POST "https://<CLOUD_RUN_URL>/api/forecast/refresh?secret=<ADMIN_SECRET>"
```
