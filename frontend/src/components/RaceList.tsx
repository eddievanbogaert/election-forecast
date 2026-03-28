import type { Race, Rating } from '../types'
import { RATING_COLORS } from '../utils/colors'
import { formatProb } from '../utils/stateUtils'

const RATING_GROUPS: Rating[] = [
  'Safe D', 'Likely D', 'Lean D', 'Toss-up', 'Lean R', 'Likely R', 'Safe R',
]

interface Props {
  races: Race[]
  selectedCode: string | null
  onSelect: (code: string) => void
}

export function RaceList({ races, selectedCode, onSelect }: Props) {
  // Group races by rating
  const grouped = RATING_GROUPS.map(rating => ({
    rating,
    races: races
      .filter(r => r.rating === rating)
      .sort((a, b) => {
        // Spectrum: safest D at top, toss-ups in middle, safest R at bottom
        // D groups: highest D probability first; R groups & toss-ups: lowest D probability first
        const isD = rating.includes('D')
        return isD
          ? b.dem_win_probability - a.dem_win_probability
          : a.dem_win_probability - b.dem_win_probability
      }),
  })).filter(g => g.races.length > 0)

  return (
    <div className="flex flex-col gap-3 overflow-y-auto pr-1">
      {grouped.map(({ rating, races: groupRaces }) => (
        <div key={rating}>
          <div
            className="flex items-center gap-2 mb-1 px-1"
          >
            <div
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
              style={{ backgroundColor: RATING_COLORS[rating] }}
            />
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              {rating}
            </span>
            <span className="text-xs text-gray-600">({groupRaces.length})</span>
          </div>

          <div className="flex flex-col gap-0.5">
            {groupRaces.map(race => (
              <button
                key={race.state_code}
                onClick={() => onSelect(race.state_code)}
                className={`
                  w-full text-left px-3 py-2 rounded-lg transition-colors
                  ${selectedCode === race.state_code
                    ? 'bg-gray-700 ring-1 ring-gray-500'
                    : 'bg-gray-800/60 hover:bg-gray-800'}
                `}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-bold text-gray-300 w-7 flex-shrink-0">
                      {race.state_code}
                    </span>
                    <span className="text-xs text-gray-400 truncate">
                      {race.incumbent
                        ? `${race.incumbent.name} (${race.incumbent.party})`
                        : `Open seat${race.outgoing_senator ? ` (${race.outgoing_senator})` : ''}`}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {/* Win probability bar */}
                    <div className="w-16 h-1.5 rounded-full bg-gray-700 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${(race.dem_win_probability >= 0.5
                            ? race.dem_win_probability
                            : 1 - race.dem_win_probability) * 100}%`,
                          backgroundColor: RATING_COLORS[rating],
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-300 w-9 text-right font-medium tabular-nums">
                      {race.dem_win_probability >= 0.5
                        ? `D ${formatProb(race.dem_win_probability)}`
                        : `R ${formatProb(1 - race.dem_win_probability)}`}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
