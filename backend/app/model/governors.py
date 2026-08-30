"""
Gubernatorial coattail signal.

A Senate candidate sharing a ballot with an unusually strong (or weak)
gubernatorial candidate of the same party gets a small push in that direction.
Most of the raw correlation between same-state Senate and governor margins is
just shared state partisanship, which the forecast already captures through PVI.
What this module isolates is the *residual*: how far the governor race is
running from where the state's partisan lean says it should be, and how much of
that transfers down the ballot.

Estimating the transfer coefficient
-----------------------------------
Fit on the 45 state-years since 2018 that held a Senate and a governor race
concurrently (2018 n=20, 2022 n=25; excludes CA'18 and ME'18, which had no
D-vs-R Senate matchup, and AK'22, whose ranked-choice final round was R vs R).

Within each cycle separately — which absorbs that cycle's national environment:

    1. Senate margin   ~ PVI  ->  Senate residual
    2. Governor margin ~ PVI  ->  Governor residual
    3. Senate residual ~ Governor residual  ->  beta

    beta = 0.119  (SE 0.050, t = 2.36, r = 0.34)
    bootstrap 90% CI [0.036, 0.241]; Theil-Sen slope 0.142
    trimmed variants range 0.089 - 0.153; leave-one-out range 0.090 - 0.182

For contrast, the raw Senate-vs-governor margin correlation across the same 45
races is r = 0.59 — five times the explanatory power of the residual
relationship. Nearly all of that is shared partisanship, so using the raw
correlation would double-count PVI.

We use BETA = 0.10, the conservative end of that interval. The effect is real
but modest and unstable across cycles (2018 beta = 0.25, 2022 beta = 0.02), and
the largest residuals are exactly the personality-driven cases that transfer
least — Phil Scott, Charlie Baker, Larry Hogan style governors winning blowouts
in states whose Senate seat never moved. Hence also a hard cap and a
sample-size shrink, both of which bite precisely on those cases.
"""

from __future__ import annotations
import csv
import collections
import datetime
import threading
from pathlib import Path
from typing import Optional

import numpy as np

DATA_PATH = Path(__file__).parent.parent / "data" / "governors.csv"

BETA: float = 0.10          # share of gubernatorial over-performance that transfers
CAP: float = 2.0            # max |adjustment| in points, before shrink
SHRINK_K: float = 2.0       # n/(n+K) shrink toward zero for thin polling
RECENT_DAYS: int = 120      # only polls this recent count toward the average
MIN_STATES: int = 8         # below this, don't attempt the regression

# Cook PVI (2020-2024 edition), D-positive, in Cook's half-margin units.
# Only used as the regression baseline, so the scale cancels out of the residual.
_PVI = {
    'AL': -15, 'AK': -6, 'AZ': -2, 'AR': -15, 'CA': 12, 'CO': 6, 'CT': 8,
    'DE': 8, 'FL': -5, 'GA': -1, 'HI': 13, 'ID': -18, 'IL': 6, 'IN': -9,
    'IA': -6, 'KS': -8, 'KY': -15, 'LA': -11, 'ME': 4, 'MD': 15, 'MA': 14,
    'MI': 0, 'MN': 3, 'MS': -11, 'MO': -9, 'MT': -10, 'NE': -10, 'NV': -1,
    'NH': 2, 'NJ': 4, 'NM': 4, 'NY': 8, 'NC': -1, 'ND': -18, 'OH': -5,
    'OK': -17, 'OR': 8, 'PA': -1, 'RI': 8, 'SC': -8, 'SD': -15, 'TN': -14,
    'TX': -6, 'UT': -11, 'VT': 17, 'VA': 3, 'WA': 10, 'WV': -21, 'WI': 0,
    'WY': -23,
}

_POP_RANK = {'lv': 0, 'rv': 1, 'v': 2, 'a': 3}

_cache: dict = {}
_cache_lock = threading.Lock()


def _parse_date(s: str) -> Optional[datetime.date]:
    try:
        m, d, y = s.split('/')
        return datetime.date(2000 + int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def _read_polls(as_of: datetime.date) -> dict[str, dict]:
    """State -> {'avg': mean D-R margin, 'n': poll count} over recent polls."""
    if not DATA_PATH.exists():
        return {}

    cutoff = as_of - datetime.timedelta(days=RECENT_DAYS)
    by_question: dict[str, list[dict]] = collections.defaultdict(list)

    with open(DATA_PATH, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r.get('cycle') != '2026' or r.get('stage') != 'general':
                continue
            by_question[r['question_id']].append(r)

    # one D-vs-R record per question
    records = []
    for rows in by_question.values():
        r0 = rows[0]
        dem = [x for x in rows if x['party'] == 'DEM']
        rep = [x for x in rows if x['party'] == 'REP']
        if not dem or not rep:
            continue
        end = _parse_date(r0['end_date'])
        if end is None or end < cutoff or end > as_of:
            continue
        try:
            d = max(dem, key=lambda x: float(x['pct'] or 0))
            rp = max(rep, key=lambda x: float(x['pct'] or 0))
            margin = float(d['pct']) - float(rp['pct'])
        except ValueError:
            continue
        records.append({
            'state': r0['state'], 'poll_id': r0['poll_id'],
            'pop': (r0['population'] or '').lower(),
            'n': int(r0['sample_size'] or 0),
            'ncand': len([x for x in rows if x['party'] != 'NONE']),
            'margin': margin,
        })

    # Collapse alternate question forms: one question per poll. Prefer the
    # likely-voter screen, then the larger sample, then the head-to-head form —
    # the same rule the Senate polling average uses, and for the same reason
    # (a survey publishing several forms would otherwise get several votes).
    by_poll: dict[str, list[dict]] = collections.defaultdict(list)
    for rec in records:
        by_poll[rec['poll_id']].append(rec)

    by_state: dict[str, list[float]] = collections.defaultdict(list)
    for polls in by_poll.values():
        polls.sort(key=lambda q: (_POP_RANK.get(q['pop'], 9), -q['n'], q['ncand']))
        best = polls[0]
        by_state[best['state']].append(best['margin'])

    return {st: {'avg': sum(ms) / len(ms), 'n': len(ms)}
            for st, ms in by_state.items() if ms}


def load_governor_residuals(as_of: Optional[datetime.date] = None) -> dict[str, dict]:
    """
    State -> {'residual', 'adjustment', 'n', 'gov_margin'}.

    `residual` is the gubernatorial polling margin minus what this cycle's own
    margin-vs-PVI fit predicts for that state; `adjustment` is the points to add
    to the Senate D margin.
    """
    ref = as_of or datetime.date.today()
    with _cache_lock:
        if _cache.get('as_of') == ref:
            return _cache['data']

    polls = _read_polls(ref)
    states = [s for s in sorted(polls) if s in _PVI]

    if len(states) < MIN_STATES:
        result: dict[str, dict] = {}
    else:
        x = np.array([_PVI[s] for s in states], dtype=float)
        y = np.array([polls[s]['avg'] for s in states], dtype=float)
        A = np.vstack([np.ones_like(x), x]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        resid = y - A @ coef

        result = {}
        for st, rr in zip(states, resid):
            n = polls[st]['n']
            shrink = n / (n + SHRINK_K)       # thin polling pulls toward zero
            adj = BETA * float(rr) * shrink
            adj = max(-CAP, min(CAP, adj))
            result[st] = {
                'residual': round(float(rr), 2),
                'adjustment': round(adj, 3),
                'n': n,
                'gov_margin': round(polls[st]['avg'], 2),
            }

    with _cache_lock:
        _cache['as_of'] = ref
        _cache['data'] = result
    return result


def governor_adjustment(state_code: str,
                        as_of: Optional[datetime.date] = None) -> float:
    """Points to add to a state's Senate D margin. 0.0 when there is no signal."""
    entry = load_governor_residuals(as_of).get(state_code)
    return entry['adjustment'] if entry else 0.0
