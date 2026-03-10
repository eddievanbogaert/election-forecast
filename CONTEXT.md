# Project Context — Quick Re-Orientation Guide

Use this file to get up to speed quickly after a context reset or weekly limit.

---

## What we're building

A FiveThirtyEight-style election forecasting site for the **2028 US Senate midterms**
(34 Class III seats). The site shows a coloured US map, per-race win probabilities,
and overall chamber control odds derived from a Monte Carlo simulation.

**GitHub repo**: `eddievanbogaert/election-forecast` (private)
**Local clone**: `/Users/eddievb/Development/election-forecast`
**GCP project**: `election-forecast-489820` (owner: eddie@eddievb.com)

---

## Technology stack

| Layer | Stack |
|---|---|
| Frontend | React 18 + TypeScript + Vite; `react-simple-maps` (map); `recharts` (histogram); Tailwind CSS |
| Backend | Python 3.12 + FastAPI + NumPy (Monte Carlo); served by uvicorn |
| Hosting | Firebase Hosting (frontend) + Cloud Run (backend) |
| CI/CD | GitHub Actions → Artifact Registry → Cloud Run + Firebase Hosting |
| Secrets | GitHub repo secrets: `GCP_SA_KEY`, `FIREBASE_SERVICE_ACCOUNT`, `ADMIN_SECRET` |

---

## Repository layout (key files)

```
backend/
  app/main.py                — FastAPI app; CORS configured via CORS_ORIGINS env var
  app/routes/forecast.py     — GET /api/forecast (30 min in-memory cache)
  app/model/monte_carlo.py   — 40k-iteration simulation; returns SimulationOutput
  app/model/fundamentals.py  — PVI + incumbency + midterm lean; blending formula
  app/data/races_2028.json   — Seed data: 34 Class III races, PVI, incumbency, quality

frontend/
  src/App.tsx                — Layout; top-level state (selectedCode)
  src/components/USMap.tsx   — react-simple-maps choropleth; hover tooltip; click → select
  src/components/ChamberControl.tsx — Probability bar + recharts histogram
  src/components/RaceList.tsx       — Races grouped by rating; mini probability bars
  src/components/RaceDetail.tsx     — Selected race: prob bar, candidates, stats, notes
  src/hooks/useForecast.ts   — TanStack Query; fetches /api/forecast
  src/types/index.ts         — TypeScript interfaces (Race, ForecastResponse, etc.)
  src/utils/colors.ts        — Color scale (Safe D → Safe R), probToColor
  src/utils/stateUtils.ts    — STATE_NAME_TO_CODE lookup, formatProb/formatLean/formatPvi

infrastructure/setup.sh      — One-shot GCP provisioning (run once)
.github/workflows/deploy.yml — CI/CD: backend (Cloud Run) then frontend (Firebase)
```

---

## Model summary

**Current state (March 2026, ~972 days to election)**
Polling weight `α = 0` — entirely fundamentals-driven.

**Blended lean formula:**
```
dem_margin = -PVI + midterm_bonus(+3) + incumbency(±2.5) + quality_diff × 0.8
σ_per_state ≈ √(7² + 2.8²) ≈ 7.5 pp
```

**Monte Carlo:**
```
nat_error  ~ N(0, 2.5)     # shared across all states (national wave)
state_err  ~ N(0, σ)       # independent per state
margin_i   = lean_i + nat_error + state_err_i
```

Win probabilities are empirical means across 40,000 simulations.
Chamber control: count sims where D total seats ≥ 51.

**Estimated seat composition going into 2028:**
- D holds 34 non-contested seats (post-2026 estimate)
- R holds 32 non-contested seats
- 34 Class III seats contested: D defends 15, R defends 19

---

## Races (34 Class III seats)

| State | Inc. | Party | PVI | Key notes |
|---|---|---|---|---|
| AL | K. Britt | R | R+27 | Safe R |
| AK | L. Murkowski | R | R+9 | Likely R (moderate) |
| AZ | M. Kelly | D | R+2 | Toss-up |
| AR | J. Boozman | R | R+24 | Safe R |
| CA | A. Padilla | D | D+29 | Safe D |
| CO | M. Bennet | D | D+4 | Likely D |
| CT | R. Blumenthal | D | D+10 | Safe D |
| FL | Open | — | R+5 | Rubio → Sec. State; Likely R |
| GA | R. Warnock | D | R+4 | Toss-up |
| HI | B. Schatz | D | D+30 | Safe D |
| ID | M. Crapo | R | R+32 | Safe R |
| IL | T. Duckworth | D | D+17 | Safe D |
| IN | T. Young | R | R+18 | Safe R |
| IA | C. Grassley | R | R+10 | Likely R; retirement risk (age 95) |
| KS | J. Moran | R | R+20 | Safe R |
| KY | R. Paul | R | R+26 | Safe R |
| LA | J. Kennedy | R | R+20 | Safe R |
| MD | C. Van Hollen | D | D+24 | Safe D |
| MO | E. Schmitt | R | R+18 | Safe R |
| NV | C. Cortez Masto | D | D+1 | Lean D |
| NH | M. Hassan | D | D+1 | Lean D |
| NY | C. Schumer | D | D+23 | Safe D |
| NC | T. Budd | R | R+3 | Likely R |
| ND | J. Hoeven | R | R+35 | Safe R |
| OH | Open | — | R+8 | Vance → VP; Toss-up |
| OK | J. Lankford | R | R+26 | Safe R |
| OR | J. Merkley | D | D+14 | Likely D |
| PA | J. Fetterman | D | R+1 | Lean D |
| SC | T. Scott | R | R+11 | Likely R |
| SD | J. Thune | R | R+27 | Safe R |
| UT | M. Lee | R | R+20 | Safe R |
| VT | P. Welch | D | D+35 | Safe D |
| WA | P. Murray | D | D+14 | Safe D |
| WI | R. Johnson | R | R+1 | Toss-up |

---

## GCP / deployment checklist

- [ ] Run `infrastructure/setup.sh` (one-time)
- [ ] Add `GCP_SA_KEY` to GitHub Secrets
- [ ] `firebase init hosting` in `frontend/`
- [ ] Add `FIREBASE_SERVICE_ACCOUNT` to GitHub Secrets
- [ ] Add `ADMIN_SECRET` to GitHub Secrets
- [ ] Push to `main` → CI/CD auto-deploys

**Local dev:**
```bash
# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8080

# Frontend (separate terminal)
cd frontend && npm run dev
```

---

## Next development priorities

1. **Wire up real polling data** — add `polling_average` values to `races_2028.json` as polls are released; the blending formula handles the rest automatically once α > 0
2. **Economic environment variables** — add presidential approval, GDP, CPI inputs to `fundamentals.py`
3. **Regional correlation** — improve the correlation structure in `monte_carlo.py` with state clusters (South, Midwest, etc.)
4. **Candidate quality pipeline** — integrate FEC fundraising API to auto-update quality scores
5. **Mobile responsive polish** — the map is functional but could use a mobile-optimised layout
6. **Historical model validation** — back-test against 2018, 2020, 2022 Senate results
7. **Methodology page** — add `/methodology` route explaining the model in detail

---

## Security notes

- Service account key (`GCP_SA_KEY`) is stored only in GitHub Secrets — never committed
- Cloud Run runs as a non-root user (see `backend/Dockerfile`)
- CORS is restricted to the Firebase Hosting domain only
- Admin refresh endpoint requires `ADMIN_SECRET` query param
- `.gitignore` blocks all `*.json` key files and `.env` files
