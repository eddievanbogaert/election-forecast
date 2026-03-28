import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ReferenceLine,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { ChamberControl as ChamberControlType } from '../types'
import { formatProb } from '../utils/stateUtils'

interface Props {
  chamberControl: ChamberControlType
  demSeatsNotUp: number
  repSeatsNotUp: number
}

export function ChamberControl({ chamberControl, demSeatsNotUp, repSeatsNotUp }: Props) {
  const { dem_probability, rep_probability, expected_dem_seats, seat_distribution } = chamberControl

  // Build chart data — only show plausible range (e.g., 30–70 seats)
  const chartData = seat_distribution
    .map((count, seats) => ({ seats, count }))
    .filter(d => d.seats >= 35 && d.seats <= 75)

  const totalSims = seat_distribution.reduce((a, b) => a + b, 0)

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      {/* Control probability bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Democrats control Senate</span>
          <span>Republicans control Senate</span>
        </div>
        <div className="flex h-8 rounded-lg overflow-hidden text-sm font-semibold">
          <div
            className="flex items-center justify-center text-white transition-all duration-500"
            style={{ width: `${dem_probability * 100}%`, backgroundColor: '#1565C0' }}
          >
            {dem_probability >= 0.12 && formatProb(dem_probability)}
          </div>
          <div
            className="flex items-center justify-center text-white transition-all duration-500"
            style={{ width: `${rep_probability * 100}%`, backgroundColor: '#B71C1C' }}
          >
            {rep_probability >= 0.12 && formatProb(rep_probability)}
          </div>
        </div>

        <div className="grid grid-cols-3 mt-2 text-xs text-gray-500">
          <span className="text-left">
            D holding{' '}
            <span className="text-blue-400 font-medium">{demSeatsNotUp}</span>
            {' '}seats not up
          </span>
          <span className="text-center">
            Expected:{' '}
            <span className="text-gray-200 font-medium">
              {expected_dem_seats.toFixed(1)} D seats
            </span>
          </span>
          <span className="text-right">
            R holding{' '}
            <span className="text-red-400 font-medium">{repSeatsNotUp}</span>
            {' '}seats not up
          </span>
        </div>
      </div>

      {/* Seat distribution histogram */}
      <div className="mt-2">
        <p className="text-xs text-gray-500 mb-2">
          Distribution of Democratic seats after 2026 ({(totalSims / 1000).toFixed(0)}k simulations)
        </p>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: -28, bottom: 0 }}>
            <XAxis
              dataKey="seats"
              tick={{ fill: '#6B7280', fontSize: 10 }}
              tickLine={false}
              interval={4}
            />
            <YAxis hide />
            <ReferenceLine
              x={51}
              stroke="#F9FAFB"
              strokeWidth={1.5}
              strokeDasharray="4 2"
              label={{ value: '51', position: 'top', fill: '#9CA3AF', fontSize: 10 }}
            />
            <Tooltip
              cursor={false}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const d = payload[0].payload as { seats: number; count: number }
                const pct = ((d.count / totalSims) * 100).toFixed(1)
                return (
                  <div className="bg-gray-800 text-xs text-gray-200 rounded px-2 py-1 shadow">
                    {d.seats} D seats — {pct}%
                  </div>
                )
              }}
            />
            <Bar dataKey="count" radius={[2, 2, 0, 0]} isAnimationActive={false}>
              {chartData.map(d => (
                <Cell
                  key={d.seats}
                  fill={d.seats >= 51 ? '#1E88E5' : '#B71C1C'}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
