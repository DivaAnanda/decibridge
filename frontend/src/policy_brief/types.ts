export type PolicyBriefStatus = 'generating' | 'completed' | 'failed'

export interface PolicyBriefDocument {
  id: number
  case_id: string
  version: number
  status: PolicyBriefStatus
  docx_path: string
  pdf_path: string
  docx_url: string | null
  pdf_url: string | null
  docx_sha256: string
  pdf_sha256: string
  docx_size_bytes: number
  pdf_size_bytes: number
  error_message: string
  generated_by_email: string
  generated_by_name: string
  generated_at: string
  completed_at: string | null
  source_recommendation_id: number | null
}

export const STATUS_LABEL_ID: Record<PolicyBriefStatus, string> = {
  generating: 'Sedang diproses',
  completed: 'Selesai',
  failed: 'Gagal',
}

export const STATUS_COLOR: Record<PolicyBriefStatus, string> = {
  generating: 'blue',
  completed: 'teal',
  failed: 'red',
}
