import { apiClient } from './client'
import type { Approval, SignPayload } from '../approval/types'

export async function listApprovals(caseId: string): Promise<Approval[]> {
  const { data } = await apiClient.get<Approval[]>(`/cases/${caseId}/approvals/`)
  return data
}

export async function signApproval(caseId: string, payload: SignPayload): Promise<Approval> {
  const { data } = await apiClient.post<Approval>(`/cases/${caseId}/approvals/sign/`, payload)
  return data
}
