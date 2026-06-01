import type { AuthUser } from '../auth/types'

export type ApprovalDecision = 'approved' | 'rejected' | 'revision_requested'

export interface Approval {
  id: number
  case: number
  recommendation: number
  approver: AuthUser
  decision: ApprovalDecision
  decision_label: string
  confirmation_acknowledged: boolean
  password_verified_at: string
  reason: string
  signed_at: string
  ip_address: string | null
  user_agent: string
}

export interface SignPayload {
  recommendation_id: number
  decision: ApprovalDecision
  confirmation_acknowledged: boolean
  password: string
  reason?: string
}

export const DECISION_LABEL_ID: Record<ApprovalDecision, string> = {
  approved: 'Disetujui',
  rejected: 'Ditolak',
  revision_requested: 'Minta Revisi',
}

export const DECISION_COLOR: Record<ApprovalDecision, string> = {
  approved: 'green',
  rejected: 'red',
  revision_requested: 'orange',
}
