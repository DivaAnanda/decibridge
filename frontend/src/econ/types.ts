export type Alternative = 'intervention' | 'comparator' | 'shared'
export type ParamType = 'cost' | 'probability' | 'utility' | 'disutility' | 'rate' | 'count'
export type DataStatus = 'observed' | 'proxy' | 'assumption'

export const ALTERNATIVE_LABEL: Record<Alternative, string> = {
  intervention: 'Intervensi',
  comparator: 'Komparator',
  shared: 'Bersama',
}

export const PARAM_TYPE_LABEL: Record<ParamType, string> = {
  cost: 'Biaya',
  probability: 'Probabilitas',
  utility: 'Utility',
  disutility: 'Disutility',
  rate: 'Rasio/tingkat',
  count: 'Jumlah',
}

export const DATA_STATUS_LABEL: Record<DataStatus, string> = {
  observed: 'Observed',
  proxy: 'Proxy',
  assumption: 'Assumption',
}

export const DATA_STATUS_COLOR: Record<DataStatus, string> = {
  observed: 'teal',
  proxy: 'yellow',
  assumption: 'gray',
}

// Canonical parameter keys the engine understands (mirrors backend ParamKey).
export const PARAM_KEY_LABEL: Record<string, string> = {
  drug_cost: 'Biaya obat per pasien per tahun',
  event_probability: 'Probabilitas kejadian / rehospitalisasi',
  event_cost: 'Biaya per kejadian / rawat inap',
  other_cost: 'Biaya tambahan lain',
  baseline_utility: 'Utility dasar',
  event_disutility: 'Disutility kejadian',
  eligible_population: 'Jumlah populasi eligible',
  uptake: 'Uptake',
  market_share: 'Market share',
}

export const PARAM_KEY_DEFAULT_TYPE: Record<string, ParamType> = {
  drug_cost: 'cost',
  event_probability: 'probability',
  event_cost: 'cost',
  other_cost: 'cost',
  baseline_utility: 'utility',
  event_disutility: 'disutility',
  eligible_population: 'count',
  uptake: 'rate',
  market_share: 'rate',
}

interface AuditUser {
  id: number
  full_name: string
  email: string
}

export interface EconModel {
  id: number
  horizon_years: number
  cost_discount_rate: string
  outcome_discount_rate: string
  wtp_threshold: string
  annual_budget_baseline: string | null
  notes: string
  created_at: string
  updated_at: string
  created_by: AuditUser | null
  last_edited_by: AuditUser | null
}

export interface EconModelPayload {
  horizon_years: number
  cost_discount_rate: string
  outcome_discount_rate: string
  wtp_threshold: string
  annual_budget_baseline?: string | null
  notes?: string
}

export interface EconParameter {
  id: number
  key: string
  label: string
  display_label: string
  alternative: Alternative
  year_index: number | null
  value: string
  unit: string
  param_type: ParamType
  data_status: DataStatus
  source_reference: string
  source_year: number | null
  notes: string
  version: number
}

export interface EconParameterPayload {
  key: string
  alternative: Alternative
  year_index?: number | null
  value: string
  unit?: string
  param_type: ParamType
  data_status: DataStatus
  source_reference?: string
  source_year?: number | null
  notes?: string
  label?: string
}

export interface YearRow {
  year: number
  annual_cost: string
  discounted_cost: string
  annual_qaly: string
  discounted_qaly: string
}

export interface CostBreakdown {
  drug: string
  event: string
  other: string
}

export interface EconResult {
  id: number
  total_cost_intervention: string
  total_cost_comparator: string
  total_qaly_intervention: string
  total_qaly_comparator: string
  incremental_cost: string
  incremental_qaly: string
  icer: string | null
  nmb_intervention: string
  nmb_comparator: string
  inb: string
  wtp_threshold_used: string
  decision_code: string
  is_cost_effective: boolean
  is_dominant: boolean
  is_dominated: boolean
  per_year: { intervention: YearRow[]; comparator: YearRow[] }
  cost_breakdown: { intervention: CostBreakdown; comparator: CostBreakdown }
  interpretation_text: string
  algorithm_version: string
  computed_at: string
}

export const DECISION_LABEL: Record<string, string> = {
  dominant: 'DOMINAN',
  dominated: 'DOMINATED',
  cost_effective: 'COST-EFFECTIVE',
  not_cost_effective: 'TIDAK COST-EFFECTIVE',
}

export const DECISION_COLOR: Record<string, string> = {
  dominant: 'teal',
  dominated: 'red',
  cost_effective: 'teal',
  not_cost_effective: 'red',
}

export interface BIAYearRow {
  year: number
  eligible_population: string
  uptake: string
  market_share: string
  patients_intervention: string
  patients_comparator: string
  incremental_drug_cost: string
  event_cost_offset: string
  incremental_other: string
  net_budget_impact: string
  cumulative_net_impact: string
  pct_of_annual_baseline: string
}

export interface EconBIAResult {
  id: number
  cumulative_net_impact: string
  pct_of_total_baseline: string
  annual_budget_baseline: string
  severity: string
  budget_score: number
  per_year: BIAYearRow[]
  interpretation_text: string
  algorithm_version: string
  computed_at: string
}

export const BIA_SEVERITY_LABEL: Record<string, string> = {
  cost_saving: 'Penghematan bersih',
  manageable: 'Dapat dikelola',
  significant: 'Signifikan',
  prohibitive: 'Prohibitif',
}

export const BIA_SEVERITY_COLOR: Record<string, string> = {
  cost_saving: 'teal',
  manageable: 'green',
  significant: 'yellow',
  prohibitive: 'red',
}

export interface CEACPoint {
  wtp: number
  prob: number
}

export interface EconPSAResult {
  id: number
  n_simulations: number
  random_seed: number
  wtp_base: string
  prob_cost_effective_base: string
  mean_incremental_cost: string
  mean_incremental_qaly: string
  ceac: CEACPoint[]
  scatter: number[][]
  base_case_incremental_cost: string
  base_case_incremental_qaly: string
  interpretation_text: string
  algorithm_version: string
  computed_at: string
}

export interface PSAConfig {
  n_simulations: number
  seed: number
}
