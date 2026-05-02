"""
National environment model: converts presidential approval, GDP growth,
and consumer sentiment into a national lean adjustment.

The adjustment replaces the old flat MIDTERM_PENALTY constant with a
data-driven estimate of how much the national environment favours or
hurts the president's party in the upcoming midterm.

Coefficients are calibrated to historical midterm Senate results
(1982–2022, 11 cycles):

  • Presidential net approval (approve − disapprove) is the strongest
    single predictor of midterm swing.  Each point of net disapproval
    adds ~0.12 pts to the opposing party's margin.
  • Real GDP growth (annualized) above/below the ~2% trend shifts
    outcomes ~0.3 pts per point toward/away from the president's party.
  • Consumer sentiment (U. Michigan index) deviations from the ~85
    historical average shift outcomes ~0.04 pts per index point toward
    or away from the president's party.

All three are combined additively with a base midterm structural penalty.

Presidential approval is computed live from potus-approval.csv using
exponential time-decay (half-life 21 days) so the model always reflects
the most recent polling.
"""

from __future__ import annotations
import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

ENV_PATH = Path(__file__).parent.parent / "data" / "environment.json"
APPROVAL_CSV_PATH = Path(__file__).parent.parent / "data" / "potus-approval.csv"

# ── Approval-average constants ────────────────────────────────────────────────

APPROVAL_HALFLIFE_DAYS: int = 21        # exponential decay half-life
APPROVAL_MAX_AGE_DAYS: int = 540        # ignore polls older than 18 months
APPROVAL_PARTISAN_ADJ: float = 2.0     # pts to adjust partisan-sponsored polls

# ── Coefficients (calibrated to 1982–2022 midterm Senate results) ────────────

BASE_MIDTERM_PENALTY: float = 1.5          # structural anti-president-party pts
APPROVAL_COEFFICIENT: float = 0.12         # pts per point of net disapproval
GDP_TREND: float = 2.0                     # baseline GDP growth (%)
GDP_COEFFICIENT: float = 0.3              # pts per GDP point above/below trend
SENTIMENT_BASELINE: float = 85.0           # long-run avg consumer sentiment
SENTIMENT_COEFFICIENT: float = 0.04        # pts per sentiment point below baseline


def _parse_date(s: str) -> Optional[date]:
    for fmt in ("%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


# Population rank: prefer likely voters > registered voters > adults
_POP_RANK: dict[str, int] = {"lv": 0, "rv": 1, "a": 2}


def compute_approval_average(ref: Optional[date] = None) -> dict:
    """
    Read potus-approval.csv and return a time-decay-weighted approval average.

    Each unique poll contributes one data point (best available population
    type: lv > rv > a).  Partisan-sponsored polls are adjusted by
    ±APPROVAL_PARTISAN_ADJ points before averaging.  Weights follow an
    exponential decay with half-life APPROVAL_HALFLIFE_DAYS so that recent
    polls dominate.

    Returns
    -------
    dict with keys: approve, disapprove, net, n_polls, as_of
    """
    ref = ref or date.today()

    rows: list[dict] = []
    with open(APPROVAL_CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("yes") and row.get("no"):
                rows.append(row)

    # One row per poll_id: pick the row with the best population type
    by_poll: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_poll[row["poll_id"]].append(row)

    total_w = total_app = total_dis = 0.0
    n_polls = 0

    for poll_rows in by_poll.values():
        poll_rows.sort(
            key=lambda r: _POP_RANK.get(r.get("population_full") or r.get("population", ""), 3)
        )
        best = poll_rows[0]
        end_date = _parse_date(best["end_date"])
        if end_date is None:
            continue
        age = (ref - end_date).days
        if age < 0 or age > APPROVAL_MAX_AGE_DAYS:
            continue

        partisan = best.get("partisan", "").upper()
        approve = float(best["yes"])
        disapprove = float(best["no"])

        # Adjust partisan-sponsored polls toward the center
        if partisan == "REP":
            approve -= APPROVAL_PARTISAN_ADJ
            disapprove += APPROVAL_PARTISAN_ADJ
        elif partisan == "DEM":
            approve += APPROVAL_PARTISAN_ADJ
            disapprove -= APPROVAL_PARTISAN_ADJ

        w = math.exp(-age * math.log(2) / APPROVAL_HALFLIFE_DAYS)
        total_w += w
        total_app += w * approve
        total_dis += w * disapprove
        n_polls += 1

    if total_w == 0:
        return {}

    avg_approve = round(total_app / total_w, 2)
    avg_disapprove = round(total_dis / total_w, 2)
    return {
        "approve": avg_approve,
        "disapprove": avg_disapprove,
        "net": round(avg_approve - avg_disapprove, 2),
        "n_polls": n_polls,
        "source": f"potus-approval.csv weighted average ({n_polls} polls, half-life {APPROVAL_HALFLIFE_DAYS}d)",
        "as_of": ref.isoformat(),
    }


def load_environment(ref: Optional[date] = None) -> dict:
    with open(ENV_PATH) as f:
        env = json.load(f)
    # Replace any hardcoded approval with the live CSV-computed average
    if APPROVAL_CSV_PATH.exists():
        env["presidential_approval"] = compute_approval_average(ref)
    return env


def national_environment_shift(env: Optional[dict] = None) -> float:
    """
    Compute the net D advantage (positive) or R advantage (negative)
    arising from the national political/economic environment.

    When the president is R (as in 2026), a negative environment for
    the president means D benefits, so the shift is positive.

    Returns
    -------
    float
        Points of D advantage from national environment.
        This replaces the old flat MIDTERM_PENALTY.
    """
    if env is None:
        env = load_environment()

    # ── Presidential approval ────────────────────────────────────────────────
    approval = env.get("presidential_approval", {})
    net_approval = approval.get("net", 0.0)  # approve - disapprove

    # Net disapproval hurts the president's party.
    # net_approval = -11 → net_disapproval = 11 → 11 * 0.12 = 1.32 pts
    approval_effect = -net_approval * APPROVAL_COEFFICIENT

    # ── GDP growth ───────────────────────────────────────────────────────────
    economy = env.get("economy", {})
    gdp = economy.get("gdp_growth_annualized")
    gdp_effect = 0.0
    if gdp is not None:
        # Above-trend growth helps the president's party (reduces D advantage)
        gdp_effect = -(gdp - GDP_TREND) * GDP_COEFFICIENT

    # ── Consumer sentiment ───────────────────────────────────────────────────
    sentiment = economy.get("consumer_sentiment")
    sentiment_effect = 0.0
    if sentiment is not None:
        # Below-baseline sentiment hurts the president's party
        sentiment_effect = -(sentiment - SENTIMENT_BASELINE) * SENTIMENT_COEFFICIENT

    # ── Combine ──────────────────────────────────────────────────────────────
    # All effects are from the D perspective (positive = D advantage).
    # The base midterm penalty always hurts the president's party.
    total = BASE_MIDTERM_PENALTY + approval_effect + gdp_effect + sentiment_effect

    return round(total, 2)


def environment_summary(env: Optional[dict] = None) -> dict:
    """Return a human-readable summary for the API response."""
    if env is None:
        env = load_environment()

    approval = env.get("presidential_approval", {})
    economy = env.get("economy", {})
    shift = national_environment_shift(env)

    return {
        "as_of": env.get("as_of"),
        "presidential_approval": approval.get("approve"),
        "presidential_disapproval": approval.get("disapprove"),
        "net_approval": approval.get("net"),
        "gdp_growth": economy.get("gdp_growth_annualized"),
        "consumer_sentiment": economy.get("consumer_sentiment"),
        "unemployment_rate": economy.get("unemployment_rate"),
        "national_environment_shift": shift,
        "components": {
            "base_midterm_penalty": BASE_MIDTERM_PENALTY,
            "approval_effect": round(-approval.get("net", 0) * APPROVAL_COEFFICIENT, 2),
            "gdp_effect": round(-(economy.get("gdp_growth_annualized", GDP_TREND) - GDP_TREND) * GDP_COEFFICIENT, 2),
            "sentiment_effect": round(-(economy.get("consumer_sentiment", SENTIMENT_BASELINE) - SENTIMENT_BASELINE) * SENTIMENT_COEFFICIENT, 2),
        },
    }
