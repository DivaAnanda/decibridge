import type { AuthUser } from '../auth/types'
import type { FinalDecision } from '../recommendation/types'

export type ApprovalDecision = 'approved' | 'rejected' | 'revision_requested'

export interface Approval {
  id: number
  case: number
  recommendation: number
  final_decision: FinalDecision | null
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
  /** The KFT decision on screen; the server refuses if a newer one exists. */
  final_decision_id?: number | null
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
