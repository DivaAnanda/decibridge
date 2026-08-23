import { apiClient } from './client'
import type {
  EconBIAResult,
  EconModel,
  EconModelPayload,
  EconParameter,
  EconParameterPayload,
  EconPSAResult,
  EconResult,
  PSAConfig,
  ValidationReport,
} from '../econ/types'

export async function getEconModel(caseId: string): Promise<EconModel | null> {
  const response = await apiClient.get<EconModel | null>(`/cases/${caseId}/econ/model/`, {
    validateStatus: (s) => s === 200 || s === 204,
  })
  return response.status === 204 ? null : response.data
}

export async function saveEconModel(caseId: string, payload: EconModelPayload): Promise<EconModel> {
  const { data } = await apiClient.put<EconModel>(`/cases/${caseId}/econ/model/`, payload)
  return data
}

export async function getEconParameters(caseId: string): Promise<EconParameter[]> {
  const { data } = await apiClient.get<EconParameter[]>(`/cases/${caseId}/econ/parameters/`)
  return data
}

export async function saveEconParameters(
  caseId: string,
  payload: EconParameterPayload[],
): Promise<EconParameter[]> {
  const { data } = await apiClient.put<EconParameter[]>(`/cases/${caseId}/econ/parameters/`, payload)
  return data
}

export async function computeEcon(caseId: string): Promise<EconResult> {
  const { data } = await apiClient.post<EconResult>(`/cases/${caseId}/econ/compute/`)
  return data
}

export async function listEconResults(caseId: string): Promise<EconResult[]> {
  const { data } = await apiClient.get<EconResult[]>(`/cases/${caseId}/econ/results/`)
  return data
}

export async function getLatestEconResult(caseId: string): Promise<EconResult | null> {
  const response = await apiClient.get<EconResult | null>(`/cases/${caseId}/econ/results/latest/`, {
    validateStatus: (s) => s === 200 || s === 204,
  })
  return response.status === 204 ? null : response.data
}

export async function computeEconBIA(caseId: string): Promise<EconBIAResult> {
  const { data } = await apiClient.post<EconBIAResult>(`/cases/${caseId}/econ/bia/compute/`)
  return data
}

export async function getLatestEconBIA(caseId: string): Promise<EconBIAResult | null> {
  const response = await apiClient.get<EconBIAResult | null>(
    `/cases/${caseId}/econ/bia/results/latest/`,
    { validateStatus: (s) => s === 200 || s === 204 },
  )
  return response.status === 204 ? null : response.data
}

export async function computeEconPSA(caseId: string, config: PSAConfig): Promise<EconPSAResult> {
  const { data } = await apiClient.post<EconPSAResult>(`/cases/${caseId}/econ/psa/compute/`, config)
  return data
}

export async function getLatestEconPSA(caseId: string): Promise<EconPSAResult | null> {
  const response = await apiClient.get<EconPSAResult | null>(
    `/cases/${caseId}/econ/psa/results/latest/`,
    { validateStatus: (s) => s === 200 || s === 204 },
  )
  return response.status === 204 ? null : response.data
}

export async function validateWorkbook(caseId: string, file: File): Promise<ValidationReport> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<ValidationReport>(`/cases/${caseId}/econ/validate/`, form)
  return data
}

export async function downloadValidationTemplate(caseId: string): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/cases/${caseId}/econ/validate/template/`, {
    responseType: 'blob',
  })
  return data
}
