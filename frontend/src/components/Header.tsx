import type { ForecastMeta } from '../types'

interface Props {
  meta?: ForecastMeta
}

export function Header({ meta }: Props) {
  return (
    <header className="bg-gray-950 border-b border-gray-800 px-4 py-3">
      <div className="max-w-screen-xl mx-auto flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="text-2xl font-bold text-white tracking-tight">
            <span className="text-blue-400">2026</span>{' '}
            <span className="text-gray-100">Senate Forecast</span>
          </div>
          <span className="hidden sm:block text-xs font-medium bg-gray-800 text-gray-400 rounded px-2 py-0.5">
            MIDTERMS
          </span>
        </div>

        {meta && (
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span>
              Model updated{' '}
              <span className="text-gray-200 font-medium">
                {new Date(meta.as_of).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </span>
            </span>
            <span className="hidden md:block">
              {meta.days_until_election.toLocaleString()} days to election
            </span>
            <span className="hidden md:block text-gray-600">
              {meta.polling_weight === 0
                ? 'Fundamentals only'
                : `${Math.round(meta.polling_weight * 100)}% polls / ${Math.round((1 - meta.polling_weight) * 100)}% fundamentals`}
            </span>
            {meta.national_environment && (
              <span className="hidden lg:block text-gray-600">
                WH Approval {meta.national_environment.presidential_approval}% · Env D+{meta.national_environment.national_environment_shift.toFixed(1)}
              </span>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
