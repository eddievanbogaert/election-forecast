import type { Rating } from '../types'

// Map each rating to a hex fill color (matches tailwind config)
export const RATING_COLORS: Record<Rating, string> = {
  'Safe D':   '#1565C0',
  'Likely D': '#1E88E5',
  'Lean D':   '#64B5F6',
  'Toss-up':  '#9E9E9E',
  'Lean R':   '#EF9A9A',
  'Likely R': '#E53935',
  'Safe R':   '#B71C1C',
}

export const RATING_TEXT_COLORS: Record<Rating, string> = {
  'Safe D':   'text-blue-900',
  'Likely D': 'text-blue-700',
  'Lean D':   'text-blue-500',
  'Toss-up':  'text-gray-500',
  'Lean R':   'text-red-300',
  'Likely R': 'text-red-600',
  'Safe R':   'text-red-900',
}

export const RATING_BG: Record<Rating, string> = {
  'Safe D':   'bg-blue-900',
  'Likely D': 'bg-blue-600',
  'Lean D':   'bg-blue-300',
  'Toss-up':  'bg-gray-400',
  'Lean R':   'bg-red-200',
  'Likely R': 'bg-red-500',
  'Safe R':   'bg-red-900',
}

/** Continuous color based on D win probability 0→1 */
export function probToColor(p: number): string {
  if (p >= 0.85) return '#1565C0'
  if (p >= 0.70) return '#1E88E5'
  if (p >= 0.55) return '#64B5F6'
  if (p >= 0.45) return '#9E9E9E'
  if (p >= 0.30) return '#EF9A9A'
  if (p >= 0.15) return '#E53935'
  return '#B71C1C'
}

export const NO_RACE_COLOR = '#D1D5DB'   // Tailwind gray-300 — no 2026 race
export const HOVER_STROKE  = '#F9FAFB'   // Tailwind gray-50

export function ratingOrder(rating: Rating): number {
  const order: Rating[] = [
    'Safe D', 'Likely D', 'Lean D', 'Toss-up', 'Lean R', 'Likely R', 'Safe R',
  ]
  return order.indexOf(rating)
}
