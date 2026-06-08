import { apiClient } from './client'
import type {
  AuditLogEntry,
  CaseVersionRow,
  VersionDiffResponse,
  VersionState,
} from '../versioning/types'

export async function listVersions(caseId: string): Promise<CaseVersionRow[]> {
  const { data } = await apiClient.get<CaseVersionRow[]>(
    `/cases/${caseId}/versions/`,
  )
  return data
}

export async function getVersionTimeline(
  caseId: string,
  versionId: number,
): Promise<AuditLogEntry[]> {
  const { data } = await apiClient.get<AuditLogEntry[]>(
    `/cases/${caseId}/versions/${versionId}/timeline/`,
  )
  return data
}

export async function getVersionState(
  caseId: string,
  versionId: number,
): Promise<VersionState> {
  const { data } = await apiClient.get<VersionState>(
    `/cases/${caseId}/versions/${versionId}/state/`,
  )
  return data
}

export async function getVersionDiff(
  caseId: string,
  fromId: number,
  toId: number,
): Promise<VersionDiffResponse> {
  const { data } = await apiClient.get<VersionDiffResponse>(
    `/cases/${caseId}/versions/diff/?from=${fromId}&to=${toId}`,
  )
  return data
}
