import type { AuthUser } from '../auth/types'

export type Judgement = 0 | 25 | 50 | 75 | 100
export type Certainty = 'high' | 'moderate' | 'low' | 'very_low'
export type ReferenceType =
  | 'journal_article'
  | 'clinical_guideline'
  | 'institutional_protocol'
  | 'expert_opinion'
  | 'pharmacoeconomic_model'

export type DomainSlug =
  | 'problem'
  | 'desirable_effects'
  | 'undesirable_effects'
  | 'certainty_of_evidence'
  | 'values_preferences'
  | 'resource_use'
  | 'equity'
  | 'feasibility'
  | 'acceptability'

export interface EtDDomain {
  id: number
  slug: DomainSlug
  display_name_id: string
  display_name_en: string
  description: string
  prompt_text_id: string
  order: number
}

export interface ReferenceCitation {
  id: number
  reference_type: ReferenceType
  citation_text: string
  authors: string
  publication_year: number | null
  title: string
  journal_name: string
  doi_pmid: string
  url: string
  evidence_summary: string
  created_at: string
  created_by: AuthUser
}

export interface ReferenceCitationPayload {
  reference_type: ReferenceType
  citation_text: string
  authors?: string
  publication_year?: number | null
  title?: string
  journal_name?: string
  doi_pmid?: string
  url?: string
  evidence_summary?: string
}

export interface EtDAppraisal {
  id: number
  case: number
  domain: number
  domain_slug: DomainSlug
  member: AuthUser
  judgement: Judgement
  judgement_label: string
  certainty: Certainty
  certainty_label: string
  narrative: string
  references: ReferenceCitation[]
  created_at: string
  updated_at: string
}

export interface AppraisalPayload {
  domain_slug: DomainSlug
  judgement: Judgement
  certainty: Certainty
  narrative?: string
  reference_ids?: number[]
}

export interface DomainAggregate {
  domain_slug: DomainSlug
  appraisal_count: number
  mean_judgement: string | null
  median_judgement: string | null
  dominant_certainty: Certainty | null
  certainty_score: string | null
  combined_domain_score: string | null
}

export interface OverallScore {
  domains_completed: number
  domains_total: number
  evidence_strength_score: string | null
  average_certainty: Certainty | null
}

export interface EtDSummary {
  per_domain: DomainAggregate[]
  overall: OverallScore
}

export const JUDGEMENT_OPTIONS: { value: Judgement; label: string }[] = [
  { value: 0, label: 'Tidak' },
  { value: 25, label: 'Mungkin tidak' },
  { value: 50, label: 'Tidak pasti' },
  { value: 75, label: 'Mungkin ya' },
  { value: 100, label: 'Ya' },
]

export const CERTAINTY_OPTIONS: { value: Certainty; label: string }[] = [
  { value: 'high', label: 'Tinggi' },
  { value: 'moderate', label: 'Sedang' },
  { value: 'low', label: 'Rendah' },
  { value: 'very_low', label: 'Sangat rendah' },
]

export const CERTAINTY_COLOR: Record<Certainty, string> = {
  high: 'teal',
  moderate: 'yellow',
  low: 'orange',
  very_low: 'red',
}

export const REFERENCE_TYPE_LABEL: Record<ReferenceType, string> = {
  journal_article: 'Artikel jurnal',
  clinical_guideline: 'Pedoman klinis',
  institutional_protocol: 'Protokol institusi',
  expert_opinion: 'Pendapat ahli',
  pharmacoeconomic_model: 'Model farmakoekonomi',
}
