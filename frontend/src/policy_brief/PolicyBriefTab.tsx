import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Code,
  Group,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import {
  IconAlertTriangle,
  IconDownload,
  IconFileTypeDocx,
  IconFileTypePdf,
  IconReportAnalytics,
} from '@tabler/icons-react'

import {
  downloadPolicyBrief,
  generatePolicyBrief,
  listPolicyBriefs,
} from '../api/policyBrief'
import { useAuth } from '../auth/useAuth'
import {
  STATUS_COLOR,
  STATUS_LABEL_ID,
  type PolicyBriefDocument,
} from './types'

interface Props {
  caseId: string
  caseStatus: string
}

const GATEABLE_STATUSES = new Set(['approved', 'locked'])

export function PolicyBriefTab({ caseId, caseStatus }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canGenerate =
    hasRole('hta_analyst', 'farmasi_sekretaris', 'ketua_kft') &&
    GATEABLE_STATUSES.has(caseStatus)

  const queryClient = useQueryClient()

  const briefsQuery = useQuery({
    queryKey: ['policy-briefs', caseId],
    queryFn: () => listPolicyBriefs(caseId),
  })

  const generateMutation = useMutation({
    mutationFn: () => generatePolicyBrief(caseId),
    onSuccess: (doc) => {
      void queryClient.invalidateQueries({ queryKey: ['policy-briefs', caseId] })
      notifications.show({
        color: 'teal',
        title: 'Dokumen tersedia',
        message: `Ringkasan kebijakan v${doc.version} berhasil dihasilkan.`,
      })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      notifications.show({
        color: 'red',
        title: 'Gagal membuat dokumen',
        message:
          err.response?.data?.detail ??
          'Terjadi kesalahan saat membuat ringkasan kebijakan.',
      })
    },
  })

  const handleDownload = async (
    brief: PolicyBriefDocument,
    fmt: 'docx' | 'pdf',
  ): Promise<void> => {
    const filename = `${caseId}_policy_brief_v${brief.version}.${fmt}`
    try {
      await downloadPolicyBrief(caseId, brief.id, fmt, filename)
    } catch {
      notifications.show({
        color: 'red',
        title: 'Gagal mengunduh',
        message: 'Terjadi kesalahan saat mengunduh dokumen.',
      })
    }
  }

  const latest = briefsQuery.data?.[0]
  const reasonGenerateDisabled = !GATEABLE_STATUSES.has(caseStatus)
    ? 'Kasus harus berstatus "Disetujui" atau "Terkunci" sebelum ringkasan dapat diterbitkan.'
    : !hasRole('hta_analyst', 'farmasi_sekretaris', 'ketua_kft')
      ? 'Anda tidak memiliki izin untuk menerbitkan ringkasan kebijakan.'
      : null

  return (
    <Stack gap="lg">
      <Card withBorder padding="lg" radius="md">
        <Group justify="space-between" mb="md">
          <Stack gap={2}>
            <Title order={4}>Ringkasan Kebijakan (Policy Brief)</Title>
            <Text size="xs" c="dimmed">
              Dokumen DOCX & PDF yang merangkum keputusan KFT. Dapat diunduh,
              dicetak, atau dilampirkan ke korespondensi.
            </Text>
          </Stack>
          <Tooltip
            label={reasonGenerateDisabled ?? ''}
            disabled={!reasonGenerateDisabled}
            multiline
            w={260}
          >
            <Button
              color="teal"
              leftSection={<IconReportAnalytics size={16} />}
              onClick={() => generateMutation.mutate()}
              loading={generateMutation.isPending}
              disabled={!canGenerate || generateMutation.isPending}
            >
              {latest ? 'Buat Versi Baru' : 'Terbitkan Ringkasan'}
            </Button>
          </Tooltip>
        </Group>

        {!latest && !briefsQuery.isLoading && (
          <Alert color="blue" variant="light">
            Belum ada ringkasan kebijakan untuk kasus ini. Setelah kasus disetujui
            oleh Ketua KFT, terbitkan dokumen di sini.
          </Alert>
        )}

        {latest && latest.status === 'failed' && (
          <Alert
            color="red"
            variant="light"
            icon={<IconAlertTriangle size={16} />}
            mt="sm"
          >
            Versi terakhir gagal dibuat: {latest.error_message || 'Kesalahan tidak diketahui.'}
            <br />
            <Text size="xs" c="dimmed" mt={4}>
              Pastikan Microsoft Word ter-install dan tidak sedang membuka dokumen lain.
            </Text>
          </Alert>
        )}
      </Card>

      <Card withBorder padding="lg" radius="md">
        <Title order={5} mb="sm">
          Riwayat Versi
        </Title>
        {briefsQuery.isLoading && (
          <Text size="sm" c="dimmed">
            Memuat...
          </Text>
        )}
        {briefsQuery.data && briefsQuery.data.length === 0 && (
          <Text size="sm" c="dimmed">
            Belum ada versi yang diterbitkan.
          </Text>
        )}
        {briefsQuery.data && briefsQuery.data.length > 0 && (
          <Table verticalSpacing="sm" striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Versi</Table.Th>
                <Table.Th>Diterbitkan</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Penerbit</Table.Th>
                <Table.Th>SHA-256 DOCX</Table.Th>
                <Table.Th>Unduh</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {briefsQuery.data.map((brief) => (
                <Table.Tr key={brief.id}>
                  <Table.Td ff="monospace">v{brief.version}</Table.Td>
                  <Table.Td>
                    {new Date(brief.generated_at).toLocaleString('id-ID')}
                  </Table.Td>
                  <Table.Td>
                    <Badge color={STATUS_COLOR[brief.status]} variant="light" size="sm">
                      {STATUS_LABEL_ID[brief.status]}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Stack gap={0}>
                      <Text size="sm">{brief.generated_by_name}</Text>
                      <Text size="xs" c="dimmed">
                        {brief.generated_by_email}
                      </Text>
                    </Stack>
                  </Table.Td>
                  <Table.Td>
                    <Code fz="xs">{brief.docx_sha256.slice(0, 12) || '—'}</Code>
                  </Table.Td>
                  <Table.Td>
                    {brief.status === 'completed' ? (
                      <Group gap="xs">
                        <Button
                          variant="default"
                          size="xs"
                          leftSection={<IconFileTypeDocx size={14} />}
                          onClick={() => void handleDownload(brief, 'docx')}
                        >
                          DOCX
                        </Button>
                        <Button
                          variant="default"
                          size="xs"
                          leftSection={<IconFileTypePdf size={14} />}
                          onClick={() => void handleDownload(brief, 'pdf')}
                        >
                          PDF
                        </Button>
                      </Group>
                    ) : brief.status === 'generating' ? (
                      <Group gap={4}>
                        <IconDownload size={14} opacity={0.4} />
                        <Text size="xs" c="dimmed">
                          memproses...
                        </Text>
                      </Group>
                    ) : (
                      <Text size="xs" c="red">
                        gagal
                      </Text>
                    )}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Card>
    </Stack>
  )
}
