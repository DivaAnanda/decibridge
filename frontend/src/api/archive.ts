import { apiClient } from './client'
import type { ArchiveRecordDto } from '../archive/types'

export async function getArchiveRecord(
  caseId: string,
): Promise<ArchiveRecordDto | null> {
  try {
    const { data } = await apiClient.get<ArchiveRecordDto>(
      `/cases/${caseId}/archive/`,
    )
    return data
  } catch (err) {
    const status = (err as { response?: { status?: number } }).response?.status
    if (status === 404) return null
    throw err
  }
}

export async function downloadArchiveManifest(
  caseId: string,
  filename: string,
): Promise<void> {
  const response = await apiClient.get<Blob>(
    `/cases/${caseId}/archive/manifest/`,
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
