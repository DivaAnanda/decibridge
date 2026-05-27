import { apiClient } from './client'
import type { CEAInput, CEAInputPayload, CEAResult } from '../cea/types'

export async function getCEAInput(caseId: string): Promise<CEAInput | null> {
  const response = await apiClient.get<CEAInput | null>(`/cases/${caseId}/cea/input/`, {
    validateStatus: (s) => s === 200 || s === 204,
  })
  return response.status === 204 ? null : response.data
}

export async function saveCEAInput(caseId: string, payload: CEAInputPayload): Promise<CEAInput> {
  const { data } = await apiClient.put<CEAInput>(`/cases/${caseId}/cea/input/`, payload)
  return data
}

export async function computeCEA(caseId: string): Promise<CEAResult> {
  const { data } = await apiClient.post<CEAResult>(`/cases/${caseId}/cea/compute/`)
  return data
}

export async function listCEAResults(caseId: string): Promise<CEAResult[]> {
  const { data } = await apiClient.get<CEAResult[]>(`/cases/${caseId}/cea/results/`)
  return data
}

export async function getLatestCEAResult(caseId: string): Promise<CEAResult | null> {
  const response = await apiClient.get<CEAResult | null>(
    `/cases/${caseId}/cea/results/latest/`,
    { validateStatus: (s) => s === 200 || s === 204 },
  )
  return response.status === 204 ? null : response.data
}
