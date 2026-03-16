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
**Live site**: https://election-forecast-489820.web.app

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
  app/data/polls.csv             — All polls considered (78 entries, 12 states), with tracking metadata
  app/data/senate.csv            — NYT bulk export of all published Senate polls (~1400 rows)
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

### Current state (March 2026, ~233 days to election)

The model blends **structural fundamentals** with **polling data** using a time-weighted
ramp. At ~233 days out, polling weight `α ≈ 0.36`: the model is roughly
**64% fundamentals / 36% polling**.

### National environment: D+3.54

A four-component data-driven estimate (replaces earlier flat midterm penalty):

| Component | Coefficient | Current Value | Contribution |
|-----------|-------------|---------------|-------------|
| Base midterm penalty | — | — | D+1.50 |
| Presidential approval | 0.12 per net approval pt | −11.0 | D+1.32 |
| GDP growth | 0.3 per pt above 2.0% trend | 2.3% | D−0.09 |
| Consumer sentiment | 0.04 per pt below 85.0 baseline | 64.7 | D+0.81 |

Data sources: RealClearPolitics (approval, 16-poll average), BEA (GDP), U. Michigan (sentiment).
Stored in `backend/app/data/environment.json`.

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
σ_total         = √(σ_f² + σ_p² + σ_r²)  +  1.5 if open seat
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

## Current forecast snapshot (as of March 2026)

| Metric | Value |
|--------|-------|
| Expected D seats | ~48.4 / 100 |
| D Senate control probability | ~14.4% |
| Net national environment | D+3.54 |
| Polling weight | ~36% polls / 64% fundamentals |
| D seats not up | 34 |
| R seats not up | 31 |

### Race ratings

| Rating | Races |
|--------|-------|
| **Likely D** | NC |
| **Lean D** | GA, NH, MN |
| **Toss-up / Lean D** | ME, MI |
| **Lean R** | AK |
| **Likely R** | OH-Special, FL, IA |
| **Safe R** | TX, NE, AL, KY, MT, OK, and 12 others |
| **Safe D** | IL, NM, and 10 others |

### Key battlegrounds

| Race | PVI | Polling Avg | D Win Prob | Rating |
|------|-----|-------------|-----------|--------|
| NC (Cooper vs Whatley) | R+3 | D+7 | ~76% | Likely D |
| GA (Ossoff vs TBD) | R+4 | D+5.3 | ~70% | Lean D |
| NH (Pappas vs Sununu/Brown) | D+1 | D+3.7 | ~76% | Lean D |
| ME (Platner vs Collins) | D+3 | D+3.3 | ~67% | Lean D |
| MI (TBD vs Rogers) | R+1 | R+1 | ~55% | Toss-up |
| MN (Flanagan/Craig vs Tafoya) | D+3 | D+6.5 | ~89% | Safe D |
| AK (Peltola vs Sullivan) | R+9 | D+1.5 | ~24% | Likely R |
| OH Special (Brown vs Husted) | R+8 | R+2 | ~34% | Lean R |
| FL Special (TBD vs Moody) | R+5 | R+8.7 | ~13% | Safe R |
| TX (Talarico vs Cornyn/Paxton) | R+10 | R+1 | ~15% | Safe R |

### Polling data coverage

12 states have polling data incorporated: AK, FL, GA, IA, KY, ME, MI, MN, NC, NE, NH, OH, TX.
Additional polling exists for SC (Graham weakness) but the state is not competitive (R+11 PVI).

All polls tracked in `polls.csv` (78 entries). Bulk NYT export in `senate.csv` (~1400 rows).

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
| AL | Open | R | R+27 | — | Tuberville → Gov race. Safe R |
| AK | Sullivan | R | R+9 | D+1.5 | Peltola challenging. RCV state |
| AR | Cotton | R | R+24 | — | Safe R |
| CO | Hickenlooper | D | D+4 | — | Safe D |
| DE | Coons | D | D+8 | — | Safe D |
| FL | Moody (appt) | R | R+5 | R+8.7 | Special. Moody leads all D candidates |
| GA | Ossoff | D | R+4 | D+5.3 | Top R target; Ossoff leading |
| ID | Risch | R | R+32 | — | Safe R |
| IL | Open | D | D+17 | — | Durbin retiring. Safe D |
| IA | Open | R | R+10 | R+3 | Ernst retiring. Hinson (R) leads |
| KS | Marshall | R | R+20 | — | Safe R |
| KY | Open | R | R+26 | — | McConnell retiring. Booker (D) vs TBD |
| LA | Cassidy | R | R+20 | — | Safe R |
| ME | Collins | R | D+3 | D+3.3 | Platner (D) competitive. Collins moderate |
| MA | Markey | D | D+30 | — | Safe D |
| MI | Open | D | R+1 | R+1 | Peters retiring. D primary: McMorrow/Stevens/El-Sayed vs Rogers |
| MN | Open | D | D+3 | D+6.5 | Smith retiring. Flanagan/Craig vs Tafoya |
| MS | Hyde-Smith | R | R+18 | — | Safe R |
| MT | Open | R | R+18 | — | Daines withdrew. Safe R |
| NE | Ricketts (appt) | R | R+22 | R+1 | Osborn (I) challenging. Modeled on D side |
| NH | Open | D | D+1 | D+3.7 | Shaheen retiring. Pappas vs Sununu/Brown |
| NJ | Booker | D | D+14 | — | Safe D |
| NM | Luján | D | D+4 | — | R candidate disqualified. Unopposed |
| NC | Open | R | R+3 | D+7 | Tillis retiring. Cooper vs Whatley. Top D pickup |
| OK | Open | R | R+26 | — | Mullin → DHS. Safe R |
| OR | Merkley | D | D+8 | — | Safe D |
| RI | Reed | D | D+18 | — | Safe D |
| SC | Graham | R | R+11 | — | Graham polling weak but PVI saves him |
| SD | Rounds | R | R+27 | — | Safe R |
| TN | Hagerty | R | R+26 | — | Safe R |
| TX | Cornyn | R | R+10 | R+1 | Talarico competitive. R primary runoff |
| VA | Warner | D | D+3 | — | Safe D |
| WV | Capito | R | R+30 | — | Safe R |
| WY | Lummis | R | R+35 | — | Safe R |
| OH | Open (Special) | R | R+8 | R+2 | Vance vacancy. Brown vs Husted |

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

1. **Update analysis_notes.md** — ratings changed after NYT data integration (NH, FL, IA, MN)
2. **Model documentation** — living document detailing forecasting methodology
3. **Regional correlation** — improve correlation structure in `monte_carlo.py` with state clusters
4. **Candidate quality pipeline** — integrate FEC fundraising data to auto-update quality scores
5. **Undecided allocation** — currently assumes even split; add challenger-lean adjustment
6. **Bayesian blending** — replace linear polling ramp with Bayesian update framework
7. **Historical model validation** — back-test against 2018, 2020, 2022 Senate results
8. **Methodology page** — add `/methodology` route explaining the model in detail
9. **Mobile responsive polish** — map is functional but could use mobile-optimised layout

---

## Security notes

- Service account key (`GCP_SA_KEY`) stored only in GitHub Secrets — never committed
- Cloud Run runs as a non-root user (see `backend/Dockerfile`)
- CORS restricted to Firebase Hosting domains only
- Admin refresh endpoint requires `ADMIN_SECRET` query param
- `.gitignore` blocks all `*.json` key files and `.env` files
