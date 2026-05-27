import { apiClient } from './client'
import type { BIAInput, BIAInputPayload, BIAResult } from '../bia/types'

export async function getBIAInput(caseId: string): Promise<BIAInput | null> {
  const response = await apiClient.get<BIAInput | null>(`/cases/${caseId}/bia/input/`, {
    validateStatus: (s) => s === 200 || s === 204,
  })
  return response.status === 204 ? null : response.data
}

export async function saveBIAInput(caseId: string, payload: BIAInputPayload): Promise<BIAInput> {
  const { data } = await apiClient.put<BIAInput>(`/cases/${caseId}/bia/input/`, payload)
  return data
}

export async function computeBIA(caseId: string): Promise<BIAResult> {
  const { data } = await apiClient.post<BIAResult>(`/cases/${caseId}/bia/compute/`)
  return data
}

export async function listBIAResults(caseId: string): Promise<BIAResult[]> {
  const { data } = await apiClient.get<BIAResult[]>(`/cases/${caseId}/bia/results/`)
  return data
}
