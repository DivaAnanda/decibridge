export type VersionTrigger = 'created' | 'locked' | 'revision_requested'
export type VersionStatus = 'draft' | 'locked' | 'archived'

export interface CaseVersionRow {
  id: number
  version_number: string
  status: VersionStatus
  status_label: string
  trigger: VersionTrigger
  trigger_label: string
  locked_at: string | null
  locked_by_name: string | null
  locked_by_email: string
  lock_reason: string
  created_at: string
  created_by_name: string
  cea_result_id: number | null
  bia_result_id: number | null
  recommendation_id: number | null
  approval_id: number | null
  policy_brief_document_id: number | null
}

export interface AuditLogEntry {
  id: number
  created_at: string
  action: string
  action_label: string
  actor_name: string
  actor_email: string
  target_label: string
  target_object_id: string
  diff: Record<string, unknown> | null
  metadata: Record<string, unknown> | null
  ip_address: string | null
}

export interface VersionState {
  version_number: string
  status: VersionStatus
  trigger: VersionTrigger
  locked_at: string | null
  locked_by: string | null
  lock_reason: string
  cea: Record<string, unknown> | null
  bia: Record<string, unknown> | null
  recommendation: Record<string, unknown> | null
  approval: Record<string, unknown> | null
  policy_brief: Record<string, unknown> | null
}

export interface VersionDiffResponse {
  from_version: string
  to_version: string
  from_id: number
  to_id: number
  diff: Record<string, Record<string, { from: unknown; to: unknown }>>
}

export const TRIGGER_COLOR: Record<VersionTrigger, string> = {
  created: 'gray',
  locked: 'teal',
  revision_requested: 'orange',
}

export const STATUS_COLOR: Record<VersionStatus, string> = {
  draft: 'gray',
  locked: 'teal',
  archived: 'blue',
}
