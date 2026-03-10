# 2028 Senate Forecast

A FiveThirtyEight-style probabilistic forecast for the 2028 US Senate midterm elections, built with React + FastAPI and deployed on Google Cloud Platform.

---

## Overview

The site forecasts all 34 Class III Senate seats up for election in November 2028. It features:

- **Interactive US choropleth map** — states coloured by projected win probability
- **Chamber control probability** — probability the Democrats or Republicans control the Senate post-election, with a full seat-distribution histogram
- **Per-race detail panel** — win probability, fundamentals lean, Cook PVI, candidate info, and polling average (once available)
- **Monte Carlo engine** — 40,000 simulations per run, with correlated national errors producing realistic wave scenarios

Live site: [https://election-forecast-489820.web.app](https://election-forecast-489820.web.app)

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

**GCP services used (cost-optimised):**

| Service | Purpose | Est. monthly cost |
|---|---|---|
| Firebase Hosting | Frontend static site | Free tier |
| Cloud Run | Backend API (scales to 0) | ~$0–2 |
| Artifact Registry | Docker image storage | ~$0.10/GB |

**Total expected cost: well under $5/month** for a low-traffic development/demo site.

---

## Model

### Inputs (current — fundamentals only; polls integrated as they become available)

| Category | Variable | Source |
|---|---|---|
| Structural | Cook PVI | Stored in `races_2028.json` |
| Structural | Incumbency advantage (+2.5 pp) | Computed |
| Structural | Midterm penalty for president's party (−3 pp) | Computed |
| Candidate | Quality score differential | Seed data (0–10 scale) |
| Seat | Open-seat volatility | Seed data flag |
| Polling | Head-to-head average (D − R) | `polling_average` field in seed data |

### Blending

```
blended_lean = α × polling_average + (1 − α) × fundamentals_lean

α = max(0, min(1, (365 − days_until_election) / 365))
```

At the current date (~972 days out), `α ≈ 0`: the model is **fundamentals-only**. Polling weight ramps linearly to 1 over the final year.

### Uncertainty / sigma

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

### Key judgment calls & planned improvements

1. **Fundamentals vs. polls**: currently a linear ramp. Could be replaced with a Bayesian update or a decaying exponential once polls start flowing.
2. **Correlated state errors**: currently a single national factor. A full covariance matrix (regional clusters, open-seat correlation) would improve accuracy.
3. **Candidate quality**: currently a coarse 0–10 score. Plan to integrate FEC fundraising data and name-recognition tiers.
4. **Economic environment**: presidential approval, GDP, consumer sentiment not yet wired in. Planned for the next model version.
5. **Undecided allocation**: no model yet; assume they split evenly. Will add a challenger-lean adjustment.

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

Then initialise Firebase Hosting:

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
│   │   │   ├── fundamentals.py # PVI, incumbency, midterm lean
│   │   │   └── monte_carlo.py  # 40k simulation engine
│   │   └── data/
│   │       └── races_2028.json # Seed data for all 34 Class III races
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── USMap.tsx           # Interactive choropleth map
│   │   │   ├── ChamberControl.tsx  # Seat probability bar + histogram
│   │   │   ├── RaceList.tsx        # Grouped race list with mini bars
│   │   │   ├── RaceDetail.tsx      # Selected race detail panel
│   │   │   └── Header.tsx          # Top bar with metadata
│   │   ├── hooks/useForecast.ts    # TanStack Query data fetching
│   │   ├── types/index.ts          # TypeScript interfaces
│   │   └── utils/                  # Color scales, state lookup, formatters
│   ├── firebase.json               # Firebase Hosting config
│   └── package.json
├── infrastructure/
│   └── setup.sh                # One-shot GCP provisioning script
└── .github/workflows/
    └── deploy.yml              # CI/CD pipeline
```

---

## Data Notes

All race data in `races_2028.json` is **preliminary** as of early 2026:

- Candidate fields marked `"TBD"` will be updated as races develop
- Open seats in Florida (Rubio → Sec. State) and Ohio (Vance → VP) are flagged with notes
- Cook PVI values are approximate; will be updated after 2026 results
- Chuck Grassley (IA, age 95 in 2028) is flagged as a potential retirement

---

## Contributing / Updating the Model

1. **Add a poll**: edit `races_2028.json`, set `"polling_average": <D_margin>` for the race
2. **Update candidate info**: edit the `candidates` block and `"quality_score"` fields
3. **Change fundamentals**: edit `pvi` or model constants in `backend/app/model/fundamentals.py`
4. **Tune model parameters**: adjust `SIGMA_NATIONAL`, `N_SIMS`, etc. in `backend/app/model/monte_carlo.py`

After any backend change, push to `main` to auto-deploy. The cache refreshes every 30 minutes; to force an immediate refresh:

```bash
curl -X POST "https://<CLOUD_RUN_URL>/api/forecast/refresh?secret=<ADMIN_SECRET>"
```
