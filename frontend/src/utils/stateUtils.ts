// Map full state names (as in us-atlas TopoJSON) → 2-letter code
export const STATE_NAME_TO_CODE: Record<string, string> = {
  Alabama: 'AL', Alaska: 'AK', Arizona: 'AZ', Arkansas: 'AR',
  California: 'CA', Colorado: 'CO', Connecticut: 'CT', Delaware: 'DE',
  Florida: 'FL', Georgia: 'GA', Hawaii: 'HI', Idaho: 'ID',
  Illinois: 'IL', Indiana: 'IN', Iowa: 'IA', Kansas: 'KS',
  Kentucky: 'KY', Louisiana: 'LA', Maine: 'ME', Maryland: 'MD',
  Massachusetts: 'MA', Michigan: 'MI', Minnesota: 'MN', Mississippi: 'MS',
  Missouri: 'MO', Montana: 'MT', Nebraska: 'NE', Nevada: 'NV',
  'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
  'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND',
  Ohio: 'OH', Oklahoma: 'OK', Oregon: 'OR', Pennsylvania: 'PA',
  'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
  Tennessee: 'TN', Texas: 'TX', Utah: 'UT', Vermont: 'VT',
  Virginia: 'VA', Washington: 'WA', 'West Virginia': 'WV',
  Wisconsin: 'WI', Wyoming: 'WY',
}

export function formatProb(p: number): string {
  if (p >= 0.995) return '>99%'
  if (p <= 0.005) return '<1%'
  return `${Math.round(p * 100)}%`
}

export function formatLean(lean: number): string {
  if (Math.abs(lean) < 0.5) return 'Even'
  const party = lean > 0 ? 'D' : 'R'
  return `${party}+${Math.abs(lean).toFixed(1)}`
}

export function formatPvi(pvi: number): string {
  if (pvi === 0) return 'Even'
  const party = pvi < 0 ? 'D' : 'R'
  return `${party}+${Math.abs(pvi)}`
}

export function daysToElection(asOf: string): number {
  const election = new Date('2026-11-03')
  const ref = new Date(asOf)
  const diff = election.getTime() - ref.getTime()
  return Math.max(0, Math.round(diff / (1000 * 60 * 60 * 24)))
}
