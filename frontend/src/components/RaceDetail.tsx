import type { Race } from '../types'
import { RATING_COLORS } from '../utils/colors'
import { formatProb, formatLean, formatPvi } from '../utils/stateUtils'

interface Props {
  race: Race
  onClose: () => void
}

function ProbBar({ prob }: { prob: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-blue-400 w-10 text-right tabular-nums font-medium">
        {formatProb(prob)}
      </span>
      <div className="flex-1 h-3 rounded-full bg-gray-700 overflow-hidden flex">
        <div
          className="h-full rounded-l-full transition-all duration-500"
          style={{ width: `${prob * 100}%`, backgroundColor: '#1E88E5' }}
        />
        <div
          className="h-full rounded-r-full transition-all duration-500"
          style={{ width: `${(1 - prob) * 100}%`, backgroundColor: '#E53935' }}
        />
      </div>
      <span className="text-xs text-red-400 w-10 tabular-nums font-medium">
        {formatProb(1 - prob)}
      </span>
    </div>
  )
}

function StatRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-gray-800 last:border-0">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-xs text-gray-200 font-medium">{value}</span>
    </div>
  )
}

export function RaceDetail({ race, onClose }: Props) {
  const color = RATING_COLORS[race.rating]
  const demProb = race.dem_win_probability
  const repProb = 1 - demProb

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-bold text-white">{race.state}</h2>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded"
              style={{ backgroundColor: color + '33', color }}
            >
              {race.rating}
            </span>
            {race.is_open && (
              <span className="text-xs text-amber-400 font-medium">Open seat</span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-300 text-lg leading-none p-1 -mr-1"
          aria-label="Close"
        >
          ×
        </button>
      </div>

      {/* Win probability */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>D win chance</span>
          <span>R win chance</span>
        </div>
        <ProbBar prob={demProb} />
      </div>

      {/* Candidates */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-blue-950/40 rounded-lg p-2.5 border border-blue-900/30">
          <div className="text-xs text-blue-400 font-semibold mb-1">DEMOCRAT</div>
          <div className="text-sm text-white font-medium truncate">{race.candidates.dem}</div>
          {race.incumbent?.party === 'D' && (
            <div className="text-xs text-blue-300 mt-0.5">Incumbent</div>
          )}
          <div className="text-xs text-blue-300 mt-1 font-semibold">
            {formatProb(demProb)}
          </div>
        </div>
        <div className="bg-red-950/40 rounded-lg p-2.5 border border-red-900/30">
          <div className="text-xs text-red-400 font-semibold mb-1">REPUBLICAN</div>
          <div className="text-sm text-white font-medium truncate">{race.candidates.rep}</div>
          {race.incumbent?.party === 'R' && (
            <div className="text-xs text-red-300 mt-0.5">Incumbent</div>
          )}
          <div className="text-xs text-red-300 mt-1 font-semibold">
            {formatProb(repProb)}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-gray-800/50 rounded-lg p-3">
        <StatRow label="Cook PVI" value={formatPvi(race.pvi)} />
        <StatRow
          label="Fundamentals lean"
          value={
            <span style={{ color: race.blended_lean >= 0 ? '#60A5FA' : '#F87171' }}>
              {formatLean(race.blended_lean)}
            </span>
          }
        />
        <StatRow
          label="Polling average"
          value={
            race.polling_average !== null
              ? formatLean(race.polling_average)
              : <span className="text-gray-600">No polls yet</span>
          }
        />
        {race.incumbent && (
          <StatRow
            label="Incumbent"
            value={`${race.incumbent.name} (${race.incumbent.party})`}
          />
        )}
      </div>

      {/* Note */}
      {race.note && (
        <p className="text-xs text-amber-300/80 bg-amber-950/30 border border-amber-900/30 rounded-lg p-2.5 leading-relaxed">
          ℹ {race.note}
        </p>
      )}
    </div>
  )
}
