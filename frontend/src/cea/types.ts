import type { AuthUser } from '../auth/types'

export type EfficacyMetric = 'qaly' | 'lyg' | 'other'

export type DataSource = 'literature' | 'local_data' | 'expert_opinion' | 'mixed'

export type Dominance =
  | 'cost_saving'
  | 'cost_effective_safe'
  | 'cost_effective_at_threshold'
  | 'cost_uncertain'
  | 'cost_ineffective'
  | 'dominated'
  | 'frontier_ambiguous'

export interface CEAInput {
  id: number
  drug_cost_per_unit: string
  comparator_cost_per_unit: string
  efficacy_metric: EfficacyMetric
  metric_label: string
  drug_efficacy_value: string
  comparator_efficacy_value: string
  patient_population_size: number
  wtop_threshold: string
  data_source: DataSource
  evidence_year: number | null
  notes: string
  created_at: string
  updated_at: string
  created_by: AuthUser
  last_edited_by: AuthUser | null
}

export interface CEAResult {
  id: number
  input_snapshot: Record<string, unknown>
  incremental_cost: string
  incremental_effect: string
  icer_value: string | null
  wtop_threshold_used: string
  dominance: Dominance
  ce_score: number
  sensitivity_low_icer: string | null
  sensitivity_high_icer: string | null
  threshold_sensitivity_flag: boolean
  interpretation_text: string
  algorithm_version: string
  computed_at: string
  computed_by: AuthUser | null
}

export interface CEAInputPayload {
  drug_cost_per_unit: string
  comparator_cost_per_unit: string
  efficacy_metric: EfficacyMetric
  metric_label?: string
  drug_efficacy_value: string
  comparator_efficacy_value: string
  patient_population_size: number
  wtop_threshold: string
  data_source: DataSource
  evidence_year?: number | null
  notes?: string
}

export const DOMINANCE_LABEL_ID: Record<Dominance, string> = {
  cost_saving: 'Cost-Saving (Dominan)',
  cost_effective_safe: 'Cost-Effective (Aman)',
  cost_effective_at_threshold: 'Cost-Effective (Di Ambang)',
  cost_uncertain: 'Tidak Pasti',
  cost_ineffective: 'Cost-Ineffective',
  dominated: 'Dominated',
  frontier_ambiguous: 'Frontier Ambigu',
}

export const DOMINANCE_COLOR: Record<Dominance, string> = {
  cost_saving: 'teal',
  cost_effective_safe: 'green',
  cost_effective_at_threshold: 'lime',
  cost_uncertain: 'yellow',
  cost_ineffective: 'red',
  dominated: 'red',
  frontier_ambiguous: 'gray',
}

export const EFFICACY_METRIC_LABEL: Record<EfficacyMetric, string> = {
  qaly: 'QALY (Quality-Adjusted Life Year)',
  lyg: 'LYG (Life Year Gained)',
  other: 'Lainnya (isi label)',
}

export const DATA_SOURCE_LABEL: Record<DataSource, string> = {
  literature: 'Literatur ilmiah',
  local_data: 'Data lokal RS',
  expert_opinion: 'Pendapat ahli',
  mixed: 'Campuran',
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
