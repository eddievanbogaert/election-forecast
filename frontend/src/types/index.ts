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

export interface EnvironmentComponents {
  base_midterm_penalty: number
  approval_effect: number
  gdp_effect: number
  sentiment_effect: number
}

export interface NationalEnvironment {
  as_of: string | null
  presidential_approval: number | null
  presidential_disapproval: number | null
  net_approval: number | null
  gdp_growth: number | null
  consumer_sentiment: number | null
  unemployment_rate: number | null
  national_environment_shift: number
  components: EnvironmentComponents
}

export interface ForecastMeta {
  as_of: string
  days_until_election: number
  polling_weight: number
  national_environment: NationalEnvironment
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
