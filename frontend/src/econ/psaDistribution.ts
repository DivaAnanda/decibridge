import type { ParamType, PSADistribution } from './types'

export const DISTRIBUTION_LABEL: Record<PSADistribution, string> = {
  fixed: 'Tetap (tidak disampel)',
  beta: 'Beta',
  gamma: 'Gamma',
  lognormal: 'Log-normal',
  normal: 'Normal',
}

// What the two stored numbers mean for each distribution (mirrors the backend).
export const DISTRIBUTION_PARAM_NAMES: Record<PSADistribution, [string, string]> = {
  fixed: ['', ''],
  beta: ['alpha', 'beta'],
  gamma: ['shape', 'scale'],
  lognormal: ['mean', 'SE'],
  normal: ['mean', 'SD'],
}

// The parameters the PSA engine samples, in the order the screen lists them.
export const PSA_SAMPLED_KEYS = [
  'drug_cost',
  'event_probability',
  'event_cost',
  'other_cost',
  'baseline_utility',
  'event_disutility',
]

const BOUNDED_TYPES = new Set<ParamType>(['probability', 'utility', 'disutility'])

/** Beta for proportions, Gamma/Log-normal for costs; the backend refuses the rest. */
export function allowedDistributions(paramType: ParamType): PSADistribution[] {
  return BOUNDED_TYPES.has(paramType)
    ? ['fixed', 'beta', 'normal']
    : ['fixed', 'gamma', 'lognormal', 'normal']
}

export function parseNumber(text: string): number | null {
  const trimmed = text.trim().replace(',', '.')
  if (trimmed === '') return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : null
}

/**
 * Reads the uncertainty a user typed: an absolute SE/SD ("600000", "0,06") or a
 * share of the base value ("10%"). The package gives costs as "SE 10% dari
 * mean" and quotes monthly figures, while drug cost is stored per year; typing
 * the percentage avoids copying an SE in the wrong unit.
 */
export function parseUncertainty(text: string, mean: number): number | null {
  const trimmed = text.trim()
  if (trimmed.endsWith('%')) {
    const share = parseNumber(trimmed.slice(0, -1))
    return share === null ? null : (Math.abs(mean) * share) / 100
  }
  return parseNumber(trimmed)
}

// The column holds ten decimal places; longer input is rejected by the API.
export function formatParam(value: number): string {
  return value.toFixed(10).replace(/\.?0+$/, '')
}

export interface DerivedParams {
  p1: string
  p2: string
}

/**
 * Method of moments: the two stored parameters from a mean and its SE/SD.
 * Null when no such distribution exists (e.g. a beta whose SD is too wide for
 * its mean, or a gamma around zero).
 */
export function deriveParams(
  distribution: PSADistribution,
  mean: number,
  sd: number,
): DerivedParams | null {
  if (!(sd > 0)) return null

  if (distribution === 'beta') {
    if (!(mean > 0 && mean < 1)) return null
    const k = (mean * (1 - mean)) / (sd * sd) - 1
    if (!(k > 0)) return null
    return { p1: formatParam(mean * k), p2: formatParam((1 - mean) * k) }
  }
  if (distribution === 'gamma') {
    if (!(mean > 0)) return null
    return { p1: formatParam((mean / sd) ** 2), p2: formatParam((sd * sd) / mean) }
  }
  if (distribution === 'lognormal') {
    if (!(mean > 0)) return null
    return { p1: formatParam(mean), p2: formatParam(sd) }
  }
  if (distribution === 'normal') {
    return { p1: formatParam(mean), p2: formatParam(sd) }
  }
  return null
}

export function impliedMean(distribution: PSADistribution, p1: number, p2: number): number | null {
  if (distribution === 'beta') return p1 + p2 > 0 ? p1 / (p1 + p2) : null
  if (distribution === 'gamma') return p1 * p2
  if (distribution === 'lognormal' || distribution === 'normal') return p1
  return null
}

export function impliedSd(distribution: PSADistribution, p1: number, p2: number): number | null {
  if (distribution === 'beta') {
    const total = p1 + p2
    return total > 0 ? Math.sqrt((p1 * p2) / (total * total * (total + 1))) : null
  }
  if (distribution === 'gamma') return p1 > 0 ? Math.sqrt(p1) * p2 : null
  if (distribution === 'lognormal' || distribution === 'normal') return p2
  return null
}

// Small gaps are normal (a beta from 18/40 with a prior has mean 0.452, not
// 0.45). A gap this large means the base value was edited after the
// distribution was set, so PSA would sample around the old value.
const MEAN_MISMATCH_TOLERANCE = 0.05

export function meanMismatch(baseValue: number, mean: number): boolean {
  if (baseValue === 0) return Math.abs(mean) > 0
  return Math.abs(mean - baseValue) / Math.abs(baseValue) > MEAN_MISMATCH_TOLERANCE
}
