import { apiClient } from './client'
import type {
  CBACriterion,
  CBACriterionPayload,
  DomainWeightVote,
  Recommendation,
  WeightsSummary,
} from '../recommendation/types'

// ── Weights ─────────────────────────────────────────────────────────────

export async function listWeights(caseId: string): Promise<DomainWeightVote[]> {
  const { data } = await apiClient.get<DomainWeightVote[]>(`/cases/${caseId}/weights/`)
  return data
}

export async function upsertWeights(
  caseId: string,
  weights: Record<string, number>,
): Promise<DomainWeightVote[]> {
  const { data } = await apiClient.post<DomainWeightVote[]>(`/cases/${caseId}/weights/`, { weights })
  return data
}

export async function getWeightsSummary(
  caseId: string,
  method: 'mean' | 'median' = 'mean',
): Promise<WeightsSummary> {
  const { data } = await apiClient.get<WeightsSummary>(
    `/cases/${caseId}/weights/summary/`,
    { params: { method } },
  )
  return data
}

// ── CBA ─────────────────────────────────────────────────────────────────

export async function listCBA(caseId: string): Promise<CBACriterion[]> {
  const { data } = await apiClient.get<CBACriterion[]>(`/cases/${caseId}/cba/`)
  return data
}

export async function createCBA(
  caseId: string,
  payload: CBACriterionPayload,
): Promise<CBACriterion> {
  const { data } = await apiClient.post<CBACriterion>(`/cases/${caseId}/cba/`, payload)
  return data
}

export async function updateCBA(
  caseId: string,
  id: number,
  payload: Partial<CBACriterionPayload>,
): Promise<CBACriterion> {
  const { data } = await apiClient.patch<CBACriterion>(`/cases/${caseId}/cba/${id}/`, payload)
  return data
}

export async function deleteCBA(caseId: string, id: number): Promise<void> {
  await apiClient.delete(`/cases/${caseId}/cba/${id}/`)
}

// ── Recommendation ──────────────────────────────────────────────────────

export async function computeRecommendation(
  caseId: string,
  method: 'mean' | 'median' = 'mean',
): Promise<Recommendation> {
  const { data } = await apiClient.post<Recommendation>(
    `/cases/${caseId}/recommendation/compute/`,
    { weight_aggregation_method: method },
  )
  return data
}

export async function listRecommendations(caseId: string): Promise<Recommendation[]> {
  const { data } = await apiClient.get<Recommendation[]>(`/cases/${caseId}/recommendation/results/`)
  return data
}

export async function getLatestRecommendation(caseId: string): Promise<Recommendation | null> {
  const response = await apiClient.get<Recommendation | null>(
    `/cases/${caseId}/recommendation/results/latest/`,
    { validateStatus: (s) => s === 200 || s === 204 },
  )
  return response.status === 204 ? null : response.data
}
