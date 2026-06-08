import { apiClient } from './client'
import type { PolicyBriefDocument } from '../policy_brief/types'

export async function listPolicyBriefs(caseId: string): Promise<PolicyBriefDocument[]> {
  const { data } = await apiClient.get<PolicyBriefDocument[]>(
    `/cases/${caseId}/policy-briefs/`,
  )
  return data
}

export async function generatePolicyBrief(caseId: string): Promise<PolicyBriefDocument> {
  const { data } = await apiClient.post<PolicyBriefDocument>(
    `/cases/${caseId}/policy-briefs/`,
  )
  return data
}

/** Download the artifact through the authenticated client and trigger a save. */
export async function downloadPolicyBrief(
  caseId: string,
  briefId: number,
  fmt: 'docx' | 'pdf',
  filename: string,
): Promise<void> {
  const response = await apiClient.get<Blob>(
    `/cases/${caseId}/policy-briefs/${briefId}/download/${fmt}/`,
    { responseType: 'blob' },
  )
  const blob = response.data
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(objectUrl)
}
