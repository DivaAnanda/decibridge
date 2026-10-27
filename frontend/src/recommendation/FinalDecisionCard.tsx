import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Divider,
  Group,
  Loader,
  Select,
  Stack,
  Text,
  Textarea,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconGavel } from '@tabler/icons-react'

import { listFinalDecisions, recordFinalDecision } from '../api/recommendation'
import { useAuth } from '../auth/useAuth'
import {
  FINAL_DECISION_COLOR,
  FINAL_DECISION_OPTIONS,
  TRAFFIC_LIGHT_LABEL_ID,
  type FinalDecision,
  type FinalDecisionPayload,
  type FinalDecisionType,
} from './types'

interface Props {
  caseId: string
  caseIsEditable: boolean
  hasRecommendation: boolean
}

type ApiError = { response?: { data?: Record<string, unknown> } }

function errorMessage(err: ApiError): string {
  const data = err.response?.data
  if (!data || typeof data !== 'object') return 'Keputusan gagal disimpan.'
  if (typeof data.detail === 'string') return data.detail
  const fields = Object.values(data).flat().filter((v) => typeof v === 'string')
  return fields.join(' ') || 'Keputusan gagal disimpan.'
}

function fmt(value: string): string {
  return new Date(value).toLocaleString('id-ID')
}

function DecisionSummary({ decision }: { decision: FinalDecision }): JSX.Element {
  return (
    <Stack gap={6}>
      <Group gap="xs">
        <Badge
          color={FINAL_DECISION_COLOR[decision.decision]}
          variant="filled"
          size="lg"
          tt="none"
          h="auto"
          py={4}
          style={{ whiteSpace: 'normal' }}
        >
          {decision.decision_label}
        </Badge>
      </Group>
      <Text size="sm">{decision.reason}</Text>
      <Text size="xs" c="dimmed">
        {decision.decided_by_name}, {fmt(decision.decided_at)} - atas rekomendasi sistem{' '}
        {TRAFFIC_LIGHT_LABEL_ID[decision.recommendation_traffic_light]} (skor{' '}
        {Number(decision.recommendation_composite_score).toFixed(2)})
      </Text>
    </Stack>
  )
}

/**
 * Round 5 item 3: "hasil warna/skor sistem tetap ada, tetapi tambahkan kolom Keputusan
 * Final KFT + alasan yang diisi manusia." The colour above is the system's; this is
 * the committee's decision, kept as an append-only history.
 */
export function FinalDecisionCard({
  caseId,
  caseIsEditable,
  hasRecommendation,
}: Props): JSX.Element {
  const { hasRole } = useAuth()
  const isKft = hasRole('kft_member', 'ketua_kft')
  const canRecord = isKft && caseIsEditable && hasRecommendation
  const queryClient = useQueryClient()

  const [decision, setDecision] = useState<FinalDecisionType | null>(null)
  const [reason, setReason] = useState('')

  const decisionsQuery = useQuery({
    queryKey: ['final-decisions', caseId],
    queryFn: () => listFinalDecisions(caseId),
  })

  const recordMutation = useMutation({
    mutationFn: (payload: FinalDecisionPayload) => recordFinalDecision(caseId, payload),
    onSuccess: () => {
      setDecision(null)
      setReason('')
      void queryClient.invalidateQueries({ queryKey: ['final-decisions', caseId] })
      void queryClient.invalidateQueries({ queryKey: ['case', caseId] })
      notifications.show({ color: 'teal', message: 'Keputusan Final KFT tersimpan.' })
    },
    onError: (err: ApiError) => {
      notifications.show({ color: 'red', title: 'Gagal menyimpan', message: errorMessage(err) })
    },
  })

  const current = decisionsQuery.data?.[0]
  const earlier = decisionsQuery.data?.slice(1) ?? []

  const blockedReason = !isKft
    ? 'Diisi oleh Anggota KFT atau Ketua KFT.'
    : !hasRecommendation
      ? 'Hitung rekomendasi sistem terlebih dahulu; keputusan final dicatat atas rekomendasi itu.'
      : !caseIsEditable
        ? 'Keputusan final hanya dapat dicatat selama kasus berstatus Draft atau Dalam ' +
          'Tinjauan. Pada kasus yang sudah disetujui, Ketua KFT memilih Minta Revisi lebih dulu.'
        : null

  return (
    <Card withBorder padding="lg" radius="md">
      <Group gap="xs" mb={4}>
        <IconGavel size={18} />
        <Title order={4}>Keputusan Final KFT</Title>
      </Group>
      <Text size="xs" c="dimmed" mb="md">
        Warna dan skor di atas adalah hasil hitungan sistem. Keputusan di sini adalah keputusan
        KFT, wajib disertai alasan, dan diperlukan sebelum sign-off. Setiap perubahan disimpan
        sebagai riwayat.
      </Text>

      {decisionsQuery.isLoading && <Loader size="sm" />}
      {decisionsQuery.isError && (
        <Text size="sm" c="red">
          Keputusan final gagal dimuat.
        </Text>
      )}
      {decisionsQuery.isSuccess &&
        (current ? (
          <DecisionSummary decision={current} />
        ) : (
          <Text size="sm" c="dimmed">
            Belum ada keputusan final.
          </Text>
        ))}

      {current && !current.is_current && (
        <Alert color="orange" variant="light" mt="md">
          {current.matches_latest_recommendation
            ? 'Keputusan ini dicatat untuk versi sebelumnya. Catat ulang keputusan untuk versi ' +
              'yang sedang direvisi sebelum sign-off.'
            : 'Rekomendasi sistem dihitung ulang setelah keputusan ini dicatat. Catat ulang ' +
              'keputusan atas rekomendasi terbaru sebelum sign-off.'}
        </Alert>
      )}

      <Divider my="md" />

      {canRecord ? (
        <Stack gap="sm">
          <Select
            label="Keputusan"
            placeholder="Pilih keputusan"
            data={FINAL_DECISION_OPTIONS}
            value={decision}
            onChange={(v) => setDecision(v as FinalDecisionType | null)}
            allowDeselect={false}
            withAsterisk
          />
          <Textarea
            label="Alasan"
            withAsterisk
            description="Wajib. Jelaskan dasar keputusan, termasuk bila berbeda dari warna sistem."
            value={reason}
            onChange={(e) => setReason(e.currentTarget.value)}
            minRows={3}
            autosize
          />
          <Group justify="flex-end">
            <Button
              leftSection={<IconGavel size={16} />}
              onClick={() => decision && recordMutation.mutate({ decision, reason: reason.trim() })}
              loading={recordMutation.isPending}
              disabled={!decision || reason.trim().length === 0}
            >
              {current ? 'Catat Keputusan Baru' : 'Simpan Keputusan Final'}
            </Button>
          </Group>
        </Stack>
      ) : (
        <Text size="xs" c="dimmed">
          {blockedReason}
        </Text>
      )}

      {earlier.length > 0 && (
        <>
          <Divider my="md" label="Riwayat keputusan" labelPosition="left" />
          <Stack gap="md">
            {earlier.map((d) => (
              <DecisionSummary key={d.id} decision={d} />
            ))}
          </Stack>
        </>
      )}
    </Card>
  )
}
