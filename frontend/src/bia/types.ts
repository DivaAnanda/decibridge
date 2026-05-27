import type { AuthUser } from '../auth/types'

export type ProjectionHorizon = 1 | 3
export type Severity = 'cost_saving' | 'manageable' | 'significant' | 'prohibitive'
export type Direction = 'savings' | 'mixed' | 'cost_increase'

export interface BIAInput {
  id: number
  eligible_population: number
  patient_uptake_year1: string
  patient_uptake_year3: string
  market_share_year1: string
  market_share_year3: string
  unit_cost_drug: string
  unit_cost_comparator: string
  budget_baseline: string
  projection_horizon: ProjectionHorizon
  notes: string
  created_at: string
  updated_at: string
  created_by: AuthUser
  last_edited_by: AuthUser | null
}

export interface BIAResult {
  id: number
  input_snapshot: Record<string, unknown>
  year1_drug_cost: string
  year1_comparator_cost_displaced: string
  year1_net_impact: string
  year2_net_impact_interpolated: string | null
  year3_drug_cost: string | null
  year3_comparator_cost_displaced: string | null
  year3_net_impact: string | null
  cumulative_impact: string
  pct_of_annual_budget: string
  severity: Severity
  direction: Direction
  budget_score: number
  interpretation_text: string
  algorithm_version: string
  computed_at: string
  computed_by: AuthUser | null
}

export interface BIAInputPayload {
  eligible_population: number
  patient_uptake_year1: string
  patient_uptake_year3: string
  market_share_year1: string
  market_share_year3: string
  unit_cost_drug: string
  unit_cost_comparator: string
  budget_baseline: string
  projection_horizon: ProjectionHorizon
  notes?: string
}

export const SEVERITY_LABEL_ID: Record<Severity, string> = {
  cost_saving: 'Cost-Saving (Penghematan)',
  manageable: 'Manageable (≤10% anggaran)',
  significant: 'Significant (10–50% anggaran)',
  prohibitive: 'Prohibitive (>50% anggaran)',
}

export const SEVERITY_COLOR: Record<Severity, string> = {
  cost_saving: 'teal',
  manageable: 'green',
  significant: 'yellow',
  prohibitive: 'red',
}

export const DIRECTION_LABEL_ID: Record<Direction, string> = {
  savings: 'Penghematan bersih',
  mixed: 'Campuran',
  cost_increase: 'Beban biaya tambahan',
}

export function formatIDR(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  const n = typeof value === 'string' ? Number(value) : value
  if (!Number.isFinite(n)) return '—'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(n)
}
