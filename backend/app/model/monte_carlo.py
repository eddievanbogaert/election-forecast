"""
Monte Carlo simulation engine for the 2026 Senate forecast.

Architecture
------------
For each of N_SIMS iterations:
  1. Draw a national error  ε_nat  ~ N(0, σ_nat)   — shifts every state equally
  2. Draw a state error      ε_i   ~ N(0, σ_state)  — per-state independent error
  3. Effective D margin  =  μ_i  +  ε_nat  +  ε_i
  4. D wins state i  iff effective margin > 0

Then aggregate across all iterations:
  • Per-race D win probability
  • Full distribution of total D seats
  • Chamber control probability (≥51 D seats, or ≥50 if D holds White House)

The shared national error produces realistic cross-state correlation —
a national wave lifts (or sinks) all races together.
"""

from __future__ import annotations
import json
import math
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import numpy as np

from .fundamentals import (
    blended_lean,
    days_until_election,
    polling_weight,
    total_sigma,
)
from .environment import (
    load_environment,
    national_environment_shift,
    environment_summary,
)

# ── Constants ──────────────────────────────────────────────────────────────────

N_SIMS: int = 40_000
SIGMA_NATIONAL: float = 2.5   # national wave error (all states move together)
DATA_PATH = Path(__file__).parent.parent / "data" / "races_2026.json"

RATING_THRESHOLDS = [
    (0.85, "Safe D"),
    (0.70, "Likely D"),
    (0.55, "Lean D"),
    (0.45, "Toss-up"),
    (0.30, "Lean R"),
    (0.15, "Likely R"),
    (0.00, "Safe R"),
]


def prob_to_rating(p: float) -> str:
    for threshold, label in RATING_THRESHOLDS:
        if p >= threshold:
            return label
    return "Safe R"


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class RaceResult:
    state: str
    state_code: str
    incumbent_name: Optional[str]
    incumbent_party: Optional[str]
    dem_candidate: str
    rep_candidate: str
    is_open: bool
    outgoing_senator: Optional[str]
    pvi: int
    blended_lean_value: float
    dem_win_probability: float
    rating: str
    polling_average: Optional[float]
    note: Optional[str]


@dataclass
class SimulationOutput:
    races: list[RaceResult]
    dem_seats_not_up: int
    rep_seats_not_up: int
    dem_control_probability: float  # P(D ≥ 51 seats total)
    expected_dem_seats_total: float
    seat_distribution: list[int]    # index = total D seats; value = sim count
    days_until_election: int
    polling_weight_value: float
    national_environment: dict        # environment summary
    run_duration_ms: float
    as_of: str                       # ISO date string


# ── Simulation ─────────────────────────────────────────────────────────────────

def load_data() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


def run_simulation(
    as_of: Optional[date] = None,
    n_sims: int = N_SIMS,
    rng_seed: Optional[int] = None,
) -> SimulationOutput:
    """
    Load race data, compute blended leans, and run the Monte Carlo.
    """
    t0 = time.perf_counter()
    # Use US Eastern time so the date matches what US users expect
    eastern = timezone(timedelta(hours=-5))
    ref = as_of or datetime.now(eastern).date()
    rng = np.random.default_rng(rng_seed)

    data = load_data()
    president_party: str = data["current_president_party"]
    dem_not_up: int = data["dem_seats_not_up"]
    rep_not_up: int = data["rep_seats_not_up"]
    races_raw: list[dict] = data["races"]

    # Load national environment once
    env = load_environment()
    env_shift = national_environment_shift(env)
    env_summary = environment_summary(env)

    n_races = len(races_raw)

    # ── Per-race fundamentals ─────────────────────────────────────────────────
    mu = np.array([blended_lean(r, president_party, ref, env_shift) for r in races_raw])
    sigma_per_race = np.array([total_sigma(r, ref) for r in races_raw])

    # ── Monte Carlo draws ─────────────────────────────────────────────────────
    # National error — same for every state in a given sim
    nat_errors = rng.standard_normal(n_sims) * SIGMA_NATIONAL   # (n_sims,)

    # State-specific errors — broadcast σ per race
    state_errors = rng.standard_normal((n_sims, n_races)) * sigma_per_race   # (n_sims, n_races)

    # Effective margin for each state in each sim
    effective_margins = mu[np.newaxis, :] + nat_errors[:, np.newaxis] + state_errors

    # D wins where margin > 0
    dem_wins = effective_margins > 0   # (n_sims, n_races)

    # Per-race D win probability (empirical)
    win_probs: np.ndarray = dem_wins.mean(axis=0)   # (n_races,)

    # Total D seats per sim (add non-contested seats)
    dem_seats_contested = dem_wins.sum(axis=1)   # (n_sims,)
    dem_total = dem_not_up + dem_seats_contested  # (n_sims,)

    # Chamber control (majority = 51, or 50 with a D VP – we use 51 for now)
    dem_control_prob: float = float((dem_total >= 51).mean())
    expected_dem_seats_total: float = float(dem_total.mean())

    # Seat distribution histogram (0 … 100)
    seat_dist = np.bincount(dem_total.astype(int), minlength=101).tolist()

    # ── Build race results ────────────────────────────────────────────────────
    results: list[RaceResult] = []
    for i, r in enumerate(races_raw):
        inc = r.get("incumbent")
        results.append(RaceResult(
            state=r["state"],
            state_code=r["state_code"],
            incumbent_name=inc["name"] if inc else None,
            incumbent_party=inc["party"] if inc else None,
            dem_candidate=r["candidates"].get("dem", {}).get("name", "TBD"),
            rep_candidate=r["candidates"].get("rep", {}).get("name", "TBD"),
            is_open=r.get("is_open", False),
            outgoing_senator=r.get("outgoing_senator"),
            pvi=r["pvi"],
            blended_lean_value=round(float(mu[i]), 2),
            dem_win_probability=round(float(win_probs[i]), 4),
            rating=prob_to_rating(float(win_probs[i])),
            polling_average=r.get("polling_average"),
            note=r.get("note"),
        ))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return SimulationOutput(
        races=results,
        dem_seats_not_up=dem_not_up,
        rep_seats_not_up=rep_not_up,
        dem_control_probability=round(dem_control_prob, 4),
        expected_dem_seats_total=round(expected_dem_seats_total, 2),
        seat_distribution=seat_dist,
        days_until_election=days_until_election(ref),
        polling_weight_value=round(polling_weight(ref), 4),
        national_environment=env_summary,
        run_duration_ms=round(elapsed_ms, 1),
        as_of=ref.isoformat(),
    )
