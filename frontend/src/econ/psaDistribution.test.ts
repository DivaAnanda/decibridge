import { describe, expect, it } from 'vitest'

import {
  allowedDistributions,
  deriveParams,
  impliedMean,
  impliedSd,
  meanMismatch,
  parseNumber,
  parseUncertainty,
} from './psaDistribution'

// 05_PSA of DeciBridge_Demo_Training_Package.xlsx. Costs are annualised (x12).
describe('deriveParams reproduces the training package', () => {
  it('gamma from a cost with SE 10% of the mean', () => {
    expect(deriveParams('gamma', 14_400_000, 1_440_000)).toEqual({ p1: '100', p2: '144000' })
    expect(deriveParams('gamma', 6_000_000, 600_000)).toEqual({ p1: '100', p2: '60000' })
    expect(deriveParams('gamma', 300_000, 30_000)).toEqual({ p1: '100', p2: '3000' })
  })

  it('beta from a utility mean and SD, to the stored ten decimals', () => {
    expect(deriveParams('beta', 0.78, 0.06)).toEqual({ p1: '36.4', p2: '10.2666666667' })
    expect(deriveParams('beta', 0.74, 0.06)).toEqual({
      p1: '38.8088888889',
      p2: '13.6355555556',
    })
    expect(deriveParams('beta', 0.1, 0.03)).toEqual({ p1: '9.9', p2: '89.1' })
  })

  it('lognormal and normal keep the mean and SE as given', () => {
    expect(deriveParams('lognormal', 6_000_000, 600_000)).toEqual({ p1: '6000000', p2: '600000' })
    expect(deriveParams('normal', 0.78, 0.06)).toEqual({ p1: '0.78', p2: '0.06' })
  })
})

describe('deriveParams refuses what cannot exist', () => {
  it('a beta whose SD is too wide for its mean', () => {
    expect(deriveParams('beta', 0.1, 0.4)).toBeNull()
  })

  it('a beta or gamma around a base value of zero', () => {
    expect(deriveParams('beta', 0, 0.05)).toBeNull()
    expect(deriveParams('gamma', 0, 100)).toBeNull()
  })

  it('zero or negative uncertainty', () => {
    expect(deriveParams('gamma', 1000, 0)).toBeNull()
    expect(deriveParams('normal', 1000, -5)).toBeNull()
  })

  it('a fixed parameter', () => {
    expect(deriveParams('fixed', 1000, 100)).toBeNull()
  })
})

describe('implied mean and SD', () => {
  it('read back what the package entered as shape parameters', () => {
    expect(impliedMean('beta', 60, 140)).toBeCloseTo(0.3, 12)
    expect(impliedMean('beta', 90, 110)).toBeCloseTo(0.45, 12)
    expect(impliedMean('gamma', 100, 144_000)).toBe(14_400_000)
    expect(impliedSd('gamma', 100, 144_000)).toBe(1_440_000)
    expect(impliedSd('beta', 36.4, 10.2666666667)).toBeCloseTo(0.06, 9)
  })

  it('are the stored numbers themselves for lognormal and normal', () => {
    expect(impliedMean('lognormal', 6_000_000, 600_000)).toBe(6_000_000)
    expect(impliedSd('normal', 0.78, 0.06)).toBe(0.06)
  })

  it('are undefined for a fixed parameter', () => {
    expect(impliedMean('fixed', 1, 1)).toBeNull()
    expect(impliedSd('fixed', 1, 1)).toBeNull()
  })
})

describe('parseUncertainty', () => {
  it('reads a percentage as a share of the base value', () => {
    expect(parseUncertainty('10%', 14_400_000)).toBe(1_440_000)
    expect(parseUncertainty(' 10 % ', 6_000_000)).toBe(600_000)
  })

  it('reads an absolute value with a decimal comma or point', () => {
    expect(parseUncertainty('0,06', 0.78)).toBe(0.06)
    expect(parseUncertainty('0.03', 0.1)).toBe(0.03)
  })

  it('returns null for blank or unreadable input', () => {
    expect(parseUncertainty('', 1)).toBeNull()
    expect(parseUncertainty('abc', 1)).toBeNull()
    expect(parseUncertainty('%', 1)).toBeNull()
    expect(parseNumber('1.440.000')).toBeNull()
  })
})

describe('meanMismatch', () => {
  it('tolerates a beta posterior that is slightly off the point estimate', () => {
    expect(meanMismatch(0.45, 19 / 42)).toBe(false)
  })

  it('flags a base value edited after the distribution was set', () => {
    expect(meanMismatch(13_200_000, 14_400_000)).toBe(true)
  })

  it('flags any spread around a zero base value', () => {
    expect(meanMismatch(0, 100)).toBe(true)
    expect(meanMismatch(0, 0)).toBe(false)
  })
})

describe('allowedDistributions', () => {
  it('offers beta but not gamma for proportions', () => {
    expect(allowedDistributions('utility')).toEqual(['fixed', 'beta', 'normal'])
    expect(allowedDistributions('probability')).not.toContain('gamma')
  })

  it('offers gamma and lognormal but not beta for costs', () => {
    expect(allowedDistributions('cost')).toEqual(['fixed', 'gamma', 'lognormal', 'normal'])
  })
})
