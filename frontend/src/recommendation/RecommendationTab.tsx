import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Group,
  SegmentedControl,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconCalculator } from '@tabler/icons-react'

import { computeRecommendation, listRecommendations } from '../api/recommendation'
import { useAuth } from '../auth/useAuth'
import { WeightsCard } from './WeightsCard'
import { CBACard } from './CBACard'
import { RecommendationCard } from './RecommendationCard'
import { TRAFFIC_LIGHT_COLOR, TRAFFIC_LIGHT_LABEL_ID } from './types'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

export function RecommendationTab({ caseId, caseIsLocked }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canCompute =
    !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris', 'ketua_kft')

  const [method, setMethod] = useState<'mean' | 'median'>('mean')
  const queryClient = useQueryClient()

  const resultsQuery = useQuery({
    queryKey: ['recommendation', caseId, 'results'],
    queryFn: () => listRecommendations(caseId),
  })

  const computeMutation = useMutation({
    mutationFn: () => computeRecommendation(caseId, method),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['recommendation', caseId, 'results'] })
      notifications.show({ color: 'teal', message: 'Rekomendasi berhasil dihitung.' })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      notifications.show({
        color: 'red',
        title: 'Komputasi gagal',
        message: err.response?.data?.detail ?? 'Terjadi kesalahan.',
      })
    },
  })

  const latest = resultsQuery.data?.[0]

  return (
    <Stack gap="lg">
      {latest && <RecommendationCard result={latest} />}

      {!latest && (
        <Alert color="blue" variant="light">
          Belum ada rekomendasi untuk kasus ini. Lengkapi bobot domain (jika Anda anggota KFT),
          definisikan kriteria CBA (jika berlaku), lalu klik "Hitung Rekomendasi" di bawah.
        </Alert>
      )}

      <Card withBorder padding="md" radius="md">
        <Group justify="space-between">
          <Stack gap={2}>
            <Title order={5}>Hitung Rekomendasi</Title>
            <Text size="xs" c="dimmed">
              Engine memakai bobot tetap dari brief: 40% bukti · 30% CEA · 20% BIA · 10% CBA.
              Aggregasi bobot domain (mean/median) hanya untuk informasi.
            </Text>
          </Stack>
          <Group>
            <SegmentedControl
              value={method}
              onChange={(v) => setMethod(v as 'mean' | 'median')}
              size="xs"
              data={[
                { value: 'mean', label: 'Mean' },
                { value: 'median', label: 'Median' },
              ]}
            />
            <Button
              leftSection={<IconCalculator size={16} />}
              onClick={() => computeMutation.mutate()}
              loading={computeMutation.isPending}
              disabled={!canCompute}
              color="teal"
            >
              Hitung Rekomendasi
            </Button>
          </Group>
        </Group>
        {!canCompute && (
          <Text size="xs" c="dimmed" mt="xs">
            {caseIsLocked
              ? 'Kasus terkunci — rekomendasi tidak dapat dihitung ulang.'
              : 'Anda tidak memiliki izin untuk menjalankan komputasi.'}
          </Text>
        )}
      </Card>

      <WeightsCard caseId={caseId} caseIsLocked={caseIsLocked} />
      <CBACard caseId={caseId} caseIsLocked={caseIsLocked} />

      {resultsQuery.data && resultsQuery.data.length > 1 && (
        <Card withBorder padding="lg" radius="md">
          <Title order={5} mb="sm">
            Riwayat komputasi
          </Title>
          <Stack gap="xs">
            {resultsQuery.data.slice(1).map((r) => (
              <Group key={r.id} justify="space-between">
                <Text size="sm" c="dimmed">
                  {new Date(r.computed_at).toLocaleString('id-ID')}
                </Text>
                <Group gap="xs">
                  <Text size="sm" ff="monospace">
                    {Number(r.composite_score).toFixed(2)}
                  </Text>
                  <Text
                    size="sm"
                    c={TRAFFIC_LIGHT_COLOR[r.traffic_light]}
                    fw={600}
                  >
                    {TRAFFIC_LIGHT_LABEL_ID[r.traffic_light]}
                  </Text>
                </Group>
              </Group>
            ))}
          </Stack>
        </Card>
      )}
    </Stack>
  )
}
