import type { AuthUser } from '../auth/types'

export type CaseStatus = 'draft' | 'in_review' | 'approved' | 'locked' | 'archived'

export type CasePerspective = 'hospital' | 'payer_bpjs' | 'societal'

export interface DecisionQuestion {
  id: number
  order: number
  question_text: string
  pico_population: string
  pico_intervention: string
  pico_comparator: string
  pico_outcome: string
  created_at: string
}

export interface CaseVersion {
  id: number
  version_number: string
  status: 'draft' | 'locked' | 'archived'
  locked_at: string | null
  locked_by: AuthUser | null
  lock_reason: string
  diff: Record<string, unknown> | null
  created_at: string
  created_by: AuthUser
}

export interface AllowedTransition {
  name: string
  target: CaseStatus
  requires_reason: boolean
}

export interface CaseListItem {
  id: number
  case_id: string
  case_title: string
  technology: string
  comparator: string
  indication: string
  status: CaseStatus
  perspective: CasePerspective
  created_by_email: string
  created_at: string
  updated_at: string
}

export interface CaseDetail {
  id: number
  case_id: string
  case_title: string
  technology: string
  comparator: string
  indication: string
  population: string
  setting: string
  perspective: CasePerspective
  status: CaseStatus
  is_editable: boolean
  is_locked: boolean
  decision_questions: DecisionQuestion[]
  versions: CaseVersion[]
  created_by: AuthUser
  created_at: string
  updated_at: string
  allowed_transitions: AllowedTransition[]
}

export interface CaseCreateInput {
  case_id: string
  case_title: string
  technology: string
  comparator: string
  indication: string
  population?: string
  setting?: string
  perspective?: CasePerspective
  decision_question?: {
    question_text: string
    pico_population: string
    pico_intervention: string
    pico_comparator: string
    pico_outcome: string
  }
}

export const STATUS_LABEL_ID: Record<CaseStatus, string> = {
  draft: 'Draft',
  in_review: 'Dalam tinjauan',
  approved: 'Disetujui',
  locked: 'Terkunci',
  archived: 'Diarsipkan',
}

export const STATUS_COLOR: Record<CaseStatus, string> = {
  draft: 'gray',
  in_review: 'yellow',
  approved: 'teal',
  locked: 'blue',
  archived: 'dark',
}

export const TRANSITION_LABEL_ID: Record<string, string> = {
  submit: 'Ajukan untuk Tinjauan',
  send_back: 'Kembalikan ke Draft',
  approve: 'Setujui',
  request_revision: 'Minta Revisi',
  lock: 'Kunci Keputusan',
  archive: 'Arsipkan',
}
