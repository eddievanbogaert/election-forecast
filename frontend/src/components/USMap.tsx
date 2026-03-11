import { useState } from 'react'
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from 'react-simple-maps'
import type { Race } from '../types'
import { probToColor, NO_RACE_COLOR, RATING_COLORS } from '../utils/colors'
import { STATE_NAME_TO_CODE } from '../utils/stateUtils'
import { formatProb } from '../utils/stateUtils'

// Public CDN — us-atlas 10m resolution
const GEO_URL = 'https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json'

interface Tooltip {
  x: number
  y: number
  state: string
  race: Race | null
}

interface Props {
  races: Race[]
  selectedCode: string | null
  onSelect: (code: string | null) => void
}

export function USMap({ races, selectedCode, onSelect }: Props) {
  const [tooltip, setTooltip] = useState<Tooltip | null>(null)

  const raceByCode = new Map(races.map(r => [r.state_code, r]))

  function getFill(_stateName: string, stateCode: string): string {
    if (selectedCode === stateCode) return '#F59E0B'  // amber highlight
    const race = raceByCode.get(stateCode)
    if (!race) return NO_RACE_COLOR
    return probToColor(race.dem_win_probability)
  }

  function getStroke(stateCode: string): string {
    return selectedCode === stateCode ? '#FCD34D' : '#1F2937'
  }

  return (
    <div className="relative w-full">
      <ComposableMap
        projection="geoAlbersUsa"
        projectionConfig={{ scale: 1000 }}
        className="w-full h-auto"
        style={{ outline: 'none' }}
      >
        <ZoomableGroup zoom={1} center={[0, 0]} minZoom={1} maxZoom={6}>
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map(geo => {
                const stateName: string = geo.properties.name
                const stateCode = STATE_NAME_TO_CODE[stateName] ?? ''
                const race = raceByCode.get(stateCode) ?? null

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill={getFill(stateName, stateCode)}
                    stroke={getStroke(stateCode)}
                    strokeWidth={0.5}
                    style={{
                      default: { outline: 'none', cursor: race ? 'pointer' : 'default' },
                      hover:   { outline: 'none', opacity: 0.85, cursor: race ? 'pointer' : 'default' },
                      pressed: { outline: 'none' },
                    }}
                    onClick={() => {
                      if (!stateCode) return
                      onSelect(selectedCode === stateCode ? null : stateCode)
                    }}
                    onMouseEnter={e => {
                      setTooltip({
                        x: e.clientX,
                        y: e.clientY,
                        state: stateName,
                        race,
                      })
                    }}
                    onMouseMove={e => {
                      setTooltip(prev =>
                        prev ? { ...prev, x: e.clientX, y: e.clientY } : null
                      )
                    }}
                    onMouseLeave={() => setTooltip(null)}
                  />
                )
              })
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>

      {/* Floating tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 shadow-xl text-sm"
          style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
        >
          <div className="font-semibold text-white">{tooltip.state}</div>
          {tooltip.race ? (
            <>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div
                  className="w-2 h-2 rounded-sm"
                  style={{ backgroundColor: RATING_COLORS[tooltip.race.rating] }}
                />
                <span className="text-gray-300 text-xs">{tooltip.race.rating}</span>
              </div>
              <div className="text-xs text-gray-400 mt-0.5">
                D {formatProb(tooltip.race.dem_win_probability)} ·{' '}
                R {formatProb(1 - tooltip.race.dem_win_probability)}
              </div>
            </>
          ) : (
            <div className="text-xs text-gray-500 mt-0.5">No Senate race in 2026</div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 px-1">
        {(
          [
            ['Safe D', '#1565C0'],
            ['Likely D', '#1E88E5'],
            ['Lean D', '#64B5F6'],
            ['Toss-up', '#9E9E9E'],
            ['Lean R', '#EF9A9A'],
            ['Likely R', '#E53935'],
            ['Safe R', '#B71C1C'],
          ] as const
        ).map(([label, color]) => (
          <div key={label} className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-xs text-gray-400">{label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: NO_RACE_COLOR }} />
          <span className="text-xs text-gray-400">No race</span>
        </div>
      </div>
    </div>
  )
}
