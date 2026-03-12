"""
Fundamentals model: converts seed race data into blended lean estimates.

The model computes a Democratic vote margin estimate for each race based on:
  1. State partisan lean (Cook PVI)
  2. National environment (presidential approval, GDP, consumer sentiment)
  3. Incumbency advantage / disadvantage
  4. Candidate quality adjustment
  5. Open-seat volatility penalty

Polling weight ramps from 0 → 1 linearly over the final 365 days before
the election.  More than a year out, the estimate is fundamentals-only.
"""

from datetime import date
from typing import Optional
import math

from .environment import national_environment_shift, load_environment


# ── Constants ──────────────────────────────────────────────────────────────────

INCUMBENCY_ADVANTAGE: float = 2.5   # percentage points boost for incumbents
QUALITY_WEIGHT: float = 0.8         # pts per quality-score point differential
OPEN_SEAT_PENALTY: float = 1.5      # extra uncertainty (not mean shift) for open seats

ELECTION_DATE = date(2026, 11, 3)


# ── Helpers ────────────────────────────────────────────────────────────────────

def days_until_election(as_of: Optional[date] = None) -> int:
    ref = as_of or date.today()
    return max(0, (ELECTION_DATE - ref).days)


def polling_weight(as_of: Optional[date] = None) -> float:
    """
    Weight given to polling vs. fundamentals.
    Ramps linearly from 0 (≥365 days out) to 1 (election day).
    """
    days = days_until_election(as_of)
    return max(0.0, min(1.0, (365 - days) / 365))


def fundamentals_lean(
    race: dict,
    president_party: str = "R",
    env_shift: Optional[float] = None,
) -> float:
    """
    Compute the fundamentals-based Democratic vote margin (percentage points).
    Positive = D favoured, negative = R favoured.

    Parameters
    ----------
    race : dict
        Single race entry from races_2026.json.
    president_party : str
        Party of the sitting president ("D" or "R").
    env_shift : float, optional
        Pre-computed national environment shift (D advantage in pts).
        If None, loaded from environment.json.

    Returns
    -------
    float
        Expected D margin in percentage points under a purely
        fundamentals-based model.
    """
    # 1. Baseline from Cook PVI (positive PVI = R-leaning state)
    pvi: float = race["pvi"]
    lean: float = -pvi  # D perspective: negative PVI → positive lean

    # 2. National environment (replaces flat midterm penalty)
    if env_shift is None:
        env_shift = national_environment_shift()
    if president_party == "R":
        lean += env_shift     # D benefits from anti-R environment
    else:
        lean -= env_shift     # R benefits from anti-D environment

    # 3. Incumbency
    incumbent = race.get("incumbent")
    if incumbent:
        if incumbent["party"] == "D":
            lean += INCUMBENCY_ADVANTAGE
        elif incumbent["party"] == "R":
            lean -= INCUMBENCY_ADVANTAGE
    # open seats: no incumbency adjustment (handled by wider σ in monte_carlo)

    # 4. Candidate quality differential (D quality - R quality)
    dem_quality = race["candidates"].get("dem", {}).get("quality_score", 5)
    rep_quality = race["candidates"].get("rep", {}).get("quality_score", 5)
    lean += (dem_quality - rep_quality) * QUALITY_WEIGHT

    return lean


def blended_lean(
    race: dict,
    president_party: str = "R",
    as_of: Optional[date] = None,
    env_shift: Optional[float] = None,
) -> float:
    """
    Blend fundamentals lean with polling average (if available).
    """
    f_lean = fundamentals_lean(race, president_party, env_shift)
    poll_avg = race.get("polling_average")  # D - R margin from polls, or None

    if poll_avg is None:
        return f_lean

    pw = polling_weight(as_of)
    return pw * poll_avg + (1.0 - pw) * f_lean


def total_sigma(
    race: dict,
    as_of: Optional[date] = None,
) -> float:
    """
    Per-race standard deviation (excluding the shared national error).
    Larger far from the election; shrinks as polls accumulate.
    Wider for open seats.
    """
    pw = polling_weight(as_of)

    # Fundamentals uncertainty decays with polling weight
    sigma_fundamentals = 7.0 * (1.0 - pw)
    # Polling error floor
    sigma_polling = 2.5 * pw
    # State-specific residual
    sigma_residual = 2.8

    sigma = math.sqrt(sigma_fundamentals**2 + sigma_polling**2 + sigma_residual**2)

    # Open seats are more volatile
    if race.get("is_open", False):
        sigma = math.sqrt(sigma**2 + OPEN_SEAT_PENALTY**2)

    return sigma
