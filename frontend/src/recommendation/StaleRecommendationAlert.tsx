import { useQuery } from '@tanstack/react-query'
import { Alert, List, Text } from '@mantine/core'

import { getLatestRecommendation } from '../api/recommendation'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

/**
 * Says when an input changed after the latest recommendation was computed.
 *
 * The backend has reported this since round 3, but no screen read it, so after
 * a revised price the old verdict stayed on display and could be signed off.
 */
export function StaleRecommendationAlert({ caseId, caseIsLocked }: Props): JSX.Element | null {
  const { data } = useQuery({
    queryKey: ['recommendation', caseId, 'latest'],
    queryFn: () => getLatestRecommendation(caseId),
    // Inputs change on other tabs, which do not know to invalidate this query.
    staleTime: 0,
  })

  if (!data?.is_stale) return null

  return (
    <Alert color="orange" title="Rekomendasi ini tidak lagi sesuai input">
      <List size="sm">
        {(data.stale_reasons ?? []).map((reason) => (
          <List.Item key={reason}>{reason}</List.Item>
        ))}
      </List>
      <Text size="xs" c="dimmed" mt="xs">
        {caseIsLocked
          ? 'Kasus sudah terkunci, sehingga rekomendasi tidak dapat dihitung ulang. Catatan ini menandai bahwa keputusan ditandatangani atas rekomendasi yang dihitung sebelum input terakhir berubah.'
          : 'Sign-off dan penguncian ditolak sampai rekomendasi dihitung ulang di tab Rekomendasi.'}
      </Text>
    </Alert>
  )
}
