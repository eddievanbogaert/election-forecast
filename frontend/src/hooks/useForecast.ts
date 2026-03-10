import { useQuery } from '@tanstack/react-query'
import type { ForecastResponse } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function fetchForecast(): Promise<ForecastResponse> {
  const res = await fetch(`${API_BASE}/api/forecast`)
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`)
  }
  return res.json() as Promise<ForecastResponse>
}

export function useForecast() {
  return useQuery<ForecastResponse, Error>({
    queryKey: ['forecast'],
    queryFn: fetchForecast,
    staleTime: 1000 * 60 * 15,    // consider fresh for 15 min
    gcTime: 1000 * 60 * 30,       // keep in cache 30 min
    retry: 2,
  })
}
