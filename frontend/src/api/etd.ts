import { apiClient } from './client'
import type {
  AppraisalPayload,
  EtDAppraisal,
  EtDDomain,
  EtDSummary,
  ReferenceCitation,
  ReferenceCitationPayload,
} from '../etd/types'

export async function listDomains(): Promise<EtDDomain[]> {
  const { data } = await apiClient.get<EtDDomain[]>('/etd/domains/')
  return data
}

export async function listReferences(caseId: string): Promise<ReferenceCitation[]> {
  const { data } = await apiClient.get<ReferenceCitation[]>(`/cases/${caseId}/references/`)
  return data
}

export async function createReference(
  caseId: string,
  payload: ReferenceCitationPayload,
): Promise<ReferenceCitation> {
  const { data } = await apiClient.post<ReferenceCitation>(`/cases/${caseId}/references/`, payload)
  return data
}

export async function updateReference(
  caseId: string,
  id: number,
  payload: ReferenceCitationPayload,
): Promise<ReferenceCitation> {
  const { data } = await apiClient.patch<ReferenceCitation>(
    `/cases/${caseId}/references/${id}/`,
    payload,
  )
  return data
}

export async function deleteReference(caseId: string, id: number): Promise<void> {
  await apiClient.delete(`/cases/${caseId}/references/${id}/`)
}

export async function listAppraisals(caseId: string): Promise<EtDAppraisal[]> {
  const { data } = await apiClient.get<EtDAppraisal[]>(`/cases/${caseId}/etd/appraisals/`)
  return data
}

export async function upsertAppraisal(
  caseId: string,
  payload: AppraisalPayload,
): Promise<EtDAppraisal> {
  const { data } = await apiClient.post<EtDAppraisal>(
    `/cases/${caseId}/etd/appraisals/`,
    payload,
  )
  return data
}

export async function deleteOwnAppraisal(caseId: string, domainSlug: string): Promise<void> {
  await apiClient.delete(`/cases/${caseId}/etd/appraisals/${domainSlug}/`)
}

export async function getSummary(caseId: string): Promise<EtDSummary> {
  const { data } = await apiClient.get<EtDSummary>(`/cases/${caseId}/etd/summary/`)
  return data
}
