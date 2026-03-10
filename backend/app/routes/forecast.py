"""
/api/forecast  — serve the cached Monte Carlo simulation output.

The simulation result is cached in-process for CACHE_TTL_SECONDS.
A manual refresh endpoint is available for admin use.
"""

from __future__ import annotations
import threading
import time
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.model import run_simulation, SimulationOutput

router = APIRouter()

# ── In-memory cache ────────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 1800   # 30 minutes

_cache_lock = threading.Lock()
_cached_result: Optional[SimulationOutput] = None
_cache_timestamp: float = 0.0


def _get_or_refresh() -> SimulationOutput:
    global _cached_result, _cache_timestamp
    with _cache_lock:
        now = time.monotonic()
        if _cached_result is None or (now - _cache_timestamp) > CACHE_TTL_SECONDS:
            _cached_result = run_simulation()
            _cache_timestamp = now
        return _cached_result


# Warm the cache at import time (best-effort, doesn't block startup)
def _warm_cache():
    try:
        _get_or_refresh()
    except Exception:
        pass

_warm_thread = threading.Thread(target=_warm_cache, daemon=True)
_warm_thread.start()


# ── Response models ────────────────────────────────────────────────────────────

class IncumbentOut(BaseModel):
    name: str
    party: str


class CandidatesOut(BaseModel):
    dem: str
    rep: str


class RaceOut(BaseModel):
    state: str
    state_code: str
    incumbent: Optional[IncumbentOut]
    candidates: CandidatesOut
    is_open: bool
    pvi: int
    blended_lean: float
    dem_win_probability: float
    rating: str
    polling_average: Optional[float]
    note: Optional[str]


class ChamberControlOut(BaseModel):
    dem_probability: float
    rep_probability: float
    expected_dem_seats: float
    seat_distribution: list[int]   # index 0-100 → count of sims


class MetaOut(BaseModel):
    as_of: str
    days_until_election: int
    polling_weight: float
    model_version: str
    run_duration_ms: float


class ForecastResponse(BaseModel):
    meta: MetaOut
    chamber_control: ChamberControlOut
    dem_seats_not_up: int
    rep_seats_not_up: int
    races: list[RaceOut]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_response(sim: SimulationOutput) -> ForecastResponse:
    races_out = []
    for r in sim.races:
        inc = IncumbentOut(name=r.incumbent_name, party=r.incumbent_party) \
              if r.incumbent_name else None
        races_out.append(RaceOut(
            state=r.state,
            state_code=r.state_code,
            incumbent=inc,
            candidates=CandidatesOut(dem=r.dem_candidate, rep=r.rep_candidate),
            is_open=r.is_open,
            pvi=r.pvi,
            blended_lean=r.blended_lean_value,
            dem_win_probability=r.dem_win_probability,
            rating=r.rating,
            polling_average=r.polling_average,
            note=r.note,
        ))

    return ForecastResponse(
        meta=MetaOut(
            as_of=sim.as_of,
            days_until_election=sim.days_until_election,
            polling_weight=sim.polling_weight_value,
            model_version="0.1.0",
            run_duration_ms=sim.run_duration_ms,
        ),
        chamber_control=ChamberControlOut(
            dem_probability=sim.dem_control_probability,
            rep_probability=round(1.0 - sim.dem_control_probability, 4),
            expected_dem_seats=sim.expected_dem_seats_total,
            seat_distribution=sim.seat_distribution,
        ),
        dem_seats_not_up=sim.dem_seats_not_up,
        rep_seats_not_up=sim.rep_seats_not_up,
        races=races_out,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/forecast", response_model=ForecastResponse, summary="Current Senate forecast")
async def get_forecast():
    """
    Returns the full 2028 Senate forecast: per-race win probabilities,
    chamber control probabilities, and seat distribution from the Monte Carlo.
    Results are cached for 30 minutes.
    """
    try:
        sim = _get_or_refresh()
        return _to_response(sim)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/forecast/refresh", summary="Force cache refresh (admin)")
async def refresh_forecast(secret: str = Query(..., description="Admin secret")):
    """
    Force a fresh Monte Carlo run, bypassing the cache.
    Requires the ADMIN_SECRET env variable to match.
    """
    import os
    expected = os.getenv("ADMIN_SECRET", "")
    if not expected or secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    global _cached_result, _cache_timestamp
    with _cache_lock:
        _cached_result = run_simulation()
        _cache_timestamp = time.monotonic()

    return {"status": "refreshed", "as_of": _cached_result.as_of}
