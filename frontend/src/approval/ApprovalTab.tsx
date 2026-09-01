import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconCheck, IconEdit, IconShieldCheck, IconX } from '@tabler/icons-react'

import { listApprovals, signApproval } from '../api/approval'
import { getLatestRecommendation } from '../api/recommendation'
import { useAuth } from '../auth/useAuth'
import { ApprovalDossierCard } from './ApprovalDossierCard'
import { ReadinessChecklistCard } from './ReadinessChecklistCard'
import { SignatureModal } from './SignatureModal'
import {
  DECISION_COLOR,
  DECISION_LABEL_ID,
  type ApprovalDecision,
} from './types'

interface Props {
  caseId: string
  caseStatus: string
}

export function ApprovalTab({ caseId, caseStatus }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const isKetua = hasRole('ketua_kft')
  const canSign = isKetua && caseStatus === 'in_review'

  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [decision, setDecision] = useState<ApprovalDecision>('approved')

  const recoQuery = useQuery({
    queryKey: ['recommendation', caseId, 'latest'],
    queryFn: () => getLatestRecommendation(caseId),
  })

  const approvalsQuery = useQuery({
    queryKey: ['approvals', caseId],
    queryFn: () => listApprovals(caseId),
  })

  const signMutation = useMutation({
    mutationFn: signApproval.bind(null, caseId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['approvals', caseId] })
      void queryClient.invalidateQueries({ queryKey: ['case', caseId] })
      void queryClient.invalidateQueries({ queryKey: ['cases'] })
      notifications.show({ color: 'teal', message: 'Tanda tangan tercatat.' })
      setModalOpen(false)
    },
    onError: (err: { response?: { data?: { detail?: string } | Record<string, string[]> } }) => {
      const d = err.response?.data ?? {}
      const message =
        typeof d === 'object' && 'detail' in d && typeof d.detail === 'string'
          ? d.detail
          : Object.entries(d as Record<string, string[]>)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
              .join('\n') || 'Tanda tangan gagal.'
      notifications.show({ color: 'red', title: 'Sign-off gagal', message })
    },
  })

  const openModal = (d: ApprovalDecision): void => {
    setDecision(d)
    setModalOpen(true)
  }

  return (
    <Stack gap="lg">
      <ReadinessChecklistCard caseId={caseId} />
      <ApprovalDossierCard caseId={caseId} />

      {isKetua && (
        <Card withBorder padding="lg" radius="md">
          <Group justify="space-between" mb="sm">
            <Stack gap={2}>
              <Title order={4}>Tanda Tangan Ketua KFT</Title>
              <Text size="xs" c="dimmed">
                Status kasus saat ini:{' '}
                <Badge variant="light" size="sm">
                  {caseStatus}
                </Badge>{' '}
                {!canSign && '— sign-off hanya tersedia saat status "in_review".'}
              </Text>
            </Stack>
          </Group>

          {canSign && (
            <Group>
              <Button
                color="teal"
                leftSection={<IconShieldCheck size={16} />}
                onClick={() => openModal('approved')}
                disabled={!recoQuery.data}
              >
                Setujui dengan Sign-Off
              </Button>
              <Button
                color="orange"
                variant="default"
                leftSection={<IconEdit size={16} />}
                onClick={() => openModal('revision_requested')}
              >
                Minta Revisi
              </Button>
              <Button
                color="red"
                variant="default"
                leftSection={<IconX size={16} />}
                onClick={() => openModal('rejected')}
              >
                Tolak
              </Button>
            </Group>
          )}

          {canSign && !recoQuery.data && (
            <Alert color="yellow" variant="light" mt="sm">
              Rekomendasi belum dihitung. Buka tab Rekomendasi dan klik "Hitung Rekomendasi"
              terlebih dahulu.
            </Alert>
          )}
        </Card>
      )}

      <Card withBorder padding="lg" radius="md">
        <Title order={4} mb="sm">
          Riwayat Tanda Tangan
        </Title>
        {(!approvalsQuery.data || approvalsQuery.data.length === 0) && (
          <Text size="sm" c="dimmed">
            Belum ada sign-off untuk kasus ini.
          </Text>
        )}
        {approvalsQuery.data && approvalsQuery.data.length > 0 && (
          <Table verticalSpacing="xs" striped>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Waktu</Table.Th>
                <Table.Th>Keputusan</Table.Th>
                <Table.Th>Penandatangan</Table.Th>
                <Table.Th>Alasan</Table.Th>
                <Table.Th>IP</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {approvalsQuery.data.map((a) => (
                <Table.Tr key={a.id}>
                  <Table.Td>{new Date(a.signed_at).toLocaleString('id-ID')}</Table.Td>
                  <Table.Td>
                    <Badge color={DECISION_COLOR[a.decision]} variant="filled" size="sm">
                      {DECISION_LABEL_ID[a.decision]}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group gap={4}>
                      <IconCheck size={12} color="green" />
                      <Text size="sm">{a.approver.full_name}</Text>
                    </Group>
                    <Text size="xs" c="dimmed">
                      {a.approver.email}
                    </Text>
                  </Table.Td>
                  <Table.Td>{a.reason || '—'}</Table.Td>
                  <Table.Td ff="monospace" fz="xs">
                    {a.ip_address || '—'}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Card>

      <SignatureModal
        opened={modalOpen}
        decision={decision}
        recommendationId={recoQuery.data?.id ?? null}
        onClose={() => setModalOpen(false)}
        onSubmit={(payload) => signMutation.mutate(payload)}
        isSubmitting={signMutation.isPending}
      />
    </Stack>
  )
}
