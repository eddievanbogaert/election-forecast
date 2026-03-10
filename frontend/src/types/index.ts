export type Party = 'D' | 'R' | 'I'

export type Rating =
  | 'Safe D'
  | 'Likely D'
  | 'Lean D'
  | 'Toss-up'
  | 'Lean R'
  | 'Likely R'
  | 'Safe R'

export interface Incumbent {
  name: string
  party: Party
}

export interface Candidates {
  dem: string
  rep: string
}

export interface Race {
  state: string
  state_code: string
  incumbent: Incumbent | null
  candidates: Candidates
  is_open: boolean
  pvi: number
  blended_lean: number
  dem_win_probability: number
  rating: Rating
  polling_average: number | null
  note: string | null
}

export interface ChamberControl {
  dem_probability: number
  rep_probability: number
  expected_dem_seats: number
  seat_distribution: number[]  // index 0–100 → simulation count
}

export interface ForecastMeta {
  as_of: string
  days_until_election: number
  polling_weight: number
  model_version: string
  run_duration_ms: number
}

export interface ForecastResponse {
  meta: ForecastMeta
  chamber_control: ChamberControl
  dem_seats_not_up: number
  rep_seats_not_up: number
  races: Race[]
}
