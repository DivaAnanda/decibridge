export interface ArchiveRecordDto {
  id: number
  case_id: string
  archived_at: string
  archived_by_name: string
  archived_by_email: string
  manifest_path: string
  manifest_url: string
  manifest_sha256: string
  manifest_size_bytes: number
  retention_until: string
  notes: string
  artifact_counts: Record<string, number>
}
