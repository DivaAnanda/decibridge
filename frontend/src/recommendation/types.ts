import type { AuthUser } from '../auth/types'
import type { DomainSlug } from '../etd/types'

export type TrafficLight = 'green' | 'yellow' | 'red'

export type CBAOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'in_list'
  | 'is_present'

export interface DomainWeightVote {
  id: number
  case: number
  domain: number
  domain_slug: DomainSlug
  member: AuthUser
  weight: number
  created_at: string
  updated_at: string
}

export interface WeightAggregate {
  domain_slug: DomainSlug
  vote_count: number
  mean_weight: string | null
  median_weight: string | null
  chosen_weight: string | null
  normalized_weight: string | null
}

export interface WeightsSummary {
  method: 'mean' | 'median'
  aggregates: WeightAggregate[]
}

export interface CBACriterion {
  id: number
  order: number
  criterion_name: string
  field_reference: string
  operator: CBAOperator
  expected_value: string
  description: string
  is_satisfied: boolean
  created_by: AuthUser
  last_edited_by: AuthUser | null
  created_at: string
  updated_at: string
}

export interface CBACriterionPayload {
  criterion_name: string
  field_reference?: string
  operator: CBAOperator
  expected_value?: string
  description?: string
  is_satisfied?: boolean
}

export interface Recommendation {
  id: number
  input_snapshot: Record<string, unknown>
  evidence_strength_score: string | null
  ce_score: string | null
  budget_score: string | null
  cba_score: string | null
  composite_score: string
  traffic_light: TrafficLight
  traffic_light_label: string
  justification_text: string
  cba_criteria_count: number
  cba_satisfied_count: number
  algorithm_version: string
  weight_aggregation_method: string
  computed_at: string
  computed_by: AuthUser | null
}

export const TRAFFIC_LIGHT_LABEL_ID: Record<TrafficLight, string> = {
  green: 'HIJAU — Adopsi Tanpa Syarat',
  yellow: 'KUNING — Adopsi Bersyarat (CBA)',
  red: 'MERAH — Tidak Direkomendasikan',
}

export const TRAFFIC_LIGHT_COLOR: Record<TrafficLight, string> = {
  green: 'green',
  yellow: 'yellow',
  red: 'red',
}

export const CBA_OPERATOR_LABEL: Record<CBAOperator, string> = {
  equals: 'Sama dengan',
  not_equals: 'Tidak sama dengan',
  greater_than: 'Lebih besar dari',
  less_than: 'Lebih kecil dari',
  in_list: 'Dalam daftar',
  is_present: 'Ada / Terdapat',
}
