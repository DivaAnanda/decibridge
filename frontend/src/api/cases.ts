import { apiClient } from './client'
import type {
  CaseCreateInput,
  CaseDetail,
  CaseListItem,
  CaseStatus,
  DecisionQuestion,
} from '../cases/types'

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function listCases(params?: {
  status?: CaseStatus
  search?: string
  page?: number
}): Promise<Paginated<CaseListItem>> {
  const { data } = await apiClient.get<Paginated<CaseListItem>>('/cases/', { params })
  return data
}

export async function getCase(caseId: string): Promise<CaseDetail> {
  const { data } = await apiClient.get<CaseDetail>(`/cases/${caseId}/`)
  return data
}

export async function createCase(payload: CaseCreateInput): Promise<CaseDetail> {
  const { data } = await apiClient.post<CaseDetail>('/cases/', payload)
  return data
}

export async function updateCase(
  caseId: string,
  payload: Partial<CaseCreateInput>,
): Promise<CaseDetail> {
  const { data } = await apiClient.patch<CaseDetail>(`/cases/${caseId}/`, payload)
  return data
}

export async function transitionCase(
  caseId: string,
  action: string,
  reason?: string,
): Promise<CaseDetail> {
  const { data } = await apiClient.post<CaseDetail>(`/cases/${caseId}/transition/`, {
    action,
    reason: reason ?? '',
  })
  return data
}

export async function addDecisionQuestion(
  caseId: string,
  payload: Omit<DecisionQuestion, 'id' | 'order' | 'created_at'>,
): Promise<DecisionQuestion> {
  const { data } = await apiClient.post<DecisionQuestion>(`/cases/${caseId}/questions/`, payload)
  return data
}
