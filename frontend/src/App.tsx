import { useState } from 'react'
import { useForecast } from './hooks/useForecast'
import { Header } from './components/Header'
import { USMap } from './components/USMap'
import { ChamberControl } from './components/ChamberControl'
import { RaceList } from './components/RaceList'
import { RaceDetail } from './components/RaceDetail'

export default function App() {
  const { data, isLoading, isError, error } = useForecast()
  const [selectedCode, setSelectedCode] = useState<string | null>(null)

  const selectedRace = data?.races.find(r => r.state_code === selectedCode) ?? null

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-400 text-sm animate-pulse">Loading forecast…</div>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="bg-gray-900 border border-red-900/40 rounded-xl p-6 max-w-md text-center">
            <div className="text-red-400 font-semibold mb-2">Failed to load forecast</div>
            <div className="text-gray-500 text-sm">
              {error?.message ?? 'Could not connect to the API. Make sure the backend is running.'}
            </div>
            <button
              className="mt-4 text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <Header meta={data.meta} />

      <main className="flex-1 max-w-screen-xl mx-auto w-full px-3 py-4 grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
        {/* Left column: map + chamber control */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          {/* Chamber control */}
          <ChamberControl
            chamberControl={data.chamber_control}
            demSeatsNotUp={data.dem_seats_not_up}
            repSeatsNotUp={data.rep_seats_not_up}
          />

          {/* Map */}
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
            <h2 className="text-sm font-semibold text-gray-300 mb-3">
              2028 Senate Map — Class III Seats
            </h2>
            <USMap
              races={data.races}
              selectedCode={selectedCode}
              onSelect={setSelectedCode}
            />
          </div>

          {/* Selected race detail (large screens: below map) */}
          {selectedRace && (
            <div className="lg:hidden">
              <RaceDetail
                race={selectedRace}
                onClose={() => setSelectedCode(null)}
              />
            </div>
          )}
        </div>

        {/* Right column: race detail (top) + race list */}
        <div className="flex flex-col gap-4 lg:max-h-[calc(100vh-80px)] lg:sticky lg:top-4">
          {selectedRace ? (
            <RaceDetail
              race={selectedRace}
              onClose={() => setSelectedCode(null)}
            />
          ) : (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 text-xs text-gray-500 text-center">
              Click a state on the map to see race details
            </div>
          )}

          <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 flex flex-col min-h-0 lg:overflow-hidden">
            <h2 className="text-sm font-semibold text-gray-300 mb-3 flex-shrink-0">
              All Races ({data.races.length})
            </h2>
            <div className="lg:overflow-y-auto lg:flex-1">
              <RaceList
                races={data.races}
                selectedCode={selectedCode}
                onSelect={setSelectedCode}
              />
            </div>
          </div>
        </div>
      </main>

      <footer className="text-center text-xs text-gray-700 py-3 px-4">
        Probabilistic model — not a guarantee of outcome. Data is preliminary;
        candidates not yet announced.{' '}
        <span className="text-gray-600">
          Model ran in {data.meta.run_duration_ms.toFixed(0)} ms · v{data.meta.model_version}
        </span>
      </footer>
    </div>
  )
}
