import { useState, type ReactNode } from 'react'
import { useParams, Link as RouterLink } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Divider,
  Grid,
  Group,
  Loader,
  Menu,
  Modal,
  Stack,
  Table,
  Tabs,
  Text,
  Textarea,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import {
  IconArrowLeft,
  IconCalculator,
  IconChevronDown,
  IconCoin,
  IconFileText,
  IconHistory,
  IconScale,
} from '@tabler/icons-react'

import { getCase, transitionCase } from '../api/cases'
import {
  STATUS_COLOR,
  STATUS_LABEL_ID,
  TRANSITION_LABEL_ID,
  type AllowedTransition,
  type CaseDetail,
} from '../cases/types'
import { CEATab } from '../cea/CEATab'
import { BIATab } from '../bia/BIATab'
import { EtDTab } from '../etd/EtDTab'

interface SummaryFieldProps {
  label: string
  children: ReactNode
}

function SummaryField({ label, children }: SummaryFieldProps): JSX.Element {
  return (
    <Stack gap={2}>
      <Text size="xs" c="dimmed">
        {label}
      </Text>
      <Text>{children}</Text>
    </Stack>
  )
}

interface PanelProps {
  data: CaseDetail
}

function OverviewPanel({ data }: PanelProps): JSX.Element {
  return (
    <Stack gap="md">
      <Card withBorder padding="lg" radius="md">
        <Group justify="space-between" mb="sm">
          <Stack gap={2}>
            <Text size="xs" c="dimmed" ff="monospace">
              {data.case_id}
            </Text>
            <Title order={3}>{data.case_title}</Title>
          </Stack>
          <Badge color={STATUS_COLOR[data.status]} variant="filled" size="lg">
            {STATUS_LABEL_ID[data.status]}
          </Badge>
        </Group>

        <Grid mt="md">
          <Grid.Col span={6}>
            <SummaryField label="Intervensi">{data.technology}</SummaryField>
          </Grid.Col>
          <Grid.Col span={6}>
            <SummaryField label="Komparator">{data.comparator}</SummaryField>
          </Grid.Col>
          <Grid.Col span={12}>
            <SummaryField label="Indikasi">{data.indication}</SummaryField>
          </Grid.Col>
          {data.population && (
            <Grid.Col span={12}>
              <SummaryField label="Populasi">{data.population}</SummaryField>
            </Grid.Col>
          )}
          {data.setting && (
            <Grid.Col span={6}>
              <SummaryField label="Setting">{data.setting}</SummaryField>
            </Grid.Col>
          )}
          <Grid.Col span={6}>
            <SummaryField label="Perspektif">{data.perspective}</SummaryField>
          </Grid.Col>
          <Grid.Col span={6}>
            <SummaryField label="Dibuat oleh">{data.created_by.full_name}</SummaryField>
          </Grid.Col>
          <Grid.Col span={6}>
            <SummaryField label="Dibuat pada">
              {new Date(data.created_at).toLocaleString('id-ID')}
            </SummaryField>
          </Grid.Col>
        </Grid>
      </Card>

      <Card withBorder padding="lg" radius="md">
        <Title order={4} mb="sm">
          Pertanyaan Keputusan (PICO)
        </Title>
        {data.decision_questions.length === 0 ? (
          <Text c="dimmed" size="sm">
            Belum ada pertanyaan keputusan.
          </Text>
        ) : (
          <Stack gap="md">
            {data.decision_questions.map((q) => (
              <Card key={q.id} withBorder padding="md" radius="sm">
                <Text fw={500}>
                  Q{q.order}: {q.question_text}
                </Text>
                <Divider my="xs" />
                <Grid>
                  <Grid.Col span={6}>
                    <SummaryField label="Populasi (P)">{q.pico_population || '—'}</SummaryField>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <SummaryField label="Intervensi (I)">{q.pico_intervention || '—'}</SummaryField>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <SummaryField label="Komparator (C)">{q.pico_comparator || '—'}</SummaryField>
                  </Grid.Col>
                  <Grid.Col span={6}>
                    <SummaryField label="Outcome (O)">{q.pico_outcome || '—'}</SummaryField>
                  </Grid.Col>
                </Grid>
              </Card>
            ))}
          </Stack>
        )}
      </Card>
    </Stack>
  )
}

function VersionsPanel({ data }: PanelProps): JSX.Element {
  if (data.versions.length === 0) {
    return (
      <Card withBorder padding="lg" radius="md">
        <Text c="dimmed" size="sm">
          Belum ada versi.
        </Text>
      </Card>
    )
  }
  return (
    <Card withBorder padding="lg" radius="md">
      <Title order={4} mb="sm">
        Riwayat Versi
      </Title>
      <Table verticalSpacing="xs">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Versi</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Dibuat</Table.Th>
            <Table.Th>Dikunci oleh</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {data.versions.map((v) => (
            <Table.Tr key={v.id}>
              <Table.Td ff="monospace">v{v.version_number}</Table.Td>
              <Table.Td>
                <Badge variant="light" size="sm">
                  {v.status}
                </Badge>
              </Table.Td>
              <Table.Td>{new Date(v.created_at).toLocaleString('id-ID')}</Table.Td>
              <Table.Td>{v.locked_by ? v.locked_by.full_name : '—'}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Card>
  )
}

export function CaseDetailPage(): JSX.Element {
  const { caseId = '' } = useParams<{ caseId: string }>()
  const queryClient = useQueryClient()

  const [pendingTransition, setPendingTransition] = useState<AllowedTransition | null>(null)
  const [reason, setReason] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => getCase(caseId),
    enabled: caseId.length > 0,
  })

  const transitionMutation = useMutation({
    mutationFn: (input: { action: string; reason: string }) =>
      transitionCase(caseId, input.action, input.reason),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['case', caseId] })
      void queryClient.invalidateQueries({ queryKey: ['cases'] })
      notifications.show({ color: 'teal', message: 'Status kasus diperbarui.' })
      setPendingTransition(null)
      setReason('')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      notifications.show({
        color: 'red',
        title: 'Gagal mengubah status',
        message: err.response?.data?.detail ?? 'Terjadi kesalahan.',
      })
    },
  })

  if (isLoading) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    )
  }

  if (isError || !data) {
    return (
      <Stack gap="md">
        <Anchor component={RouterLink} to="/cases">
          ← Kembali ke daftar kasus
        </Anchor>
        <Text c="red">Kasus tidak ditemukan atau gagal dimuat.</Text>
      </Stack>
    )
  }

  const handleTransition = (t: AllowedTransition): void => {
    if (t.requires_reason) {
      setPendingTransition(t)
    } else {
      transitionMutation.mutate({ action: t.name, reason: '' })
    }
  }

  const confirmTransitionWithReason = (): void => {
    if (!pendingTransition) return
    if (reason.trim().length === 0) {
      notifications.show({ color: 'red', message: 'Alasan wajib diisi.' })
      return
    }
    transitionMutation.mutate({ action: pendingTransition.name, reason })
  }

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Anchor component={RouterLink} to="/cases" size="sm">
          <Group gap={4}>
            <IconArrowLeft size={14} />
            Kembali ke daftar kasus
          </Group>
        </Anchor>
        {data.allowed_transitions.length > 0 && (
          <Menu position="bottom-end" withinPortal>
            <Menu.Target>
              <Button rightSection={<IconChevronDown size={14} />}>Tindakan</Button>
            </Menu.Target>
            <Menu.Dropdown>
              {data.allowed_transitions.map((t) => (
                <Menu.Item key={t.name} onClick={() => handleTransition(t)}>
                  {TRANSITION_LABEL_ID[t.name] ?? t.name}
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>
        )}
      </Group>

      <Tabs defaultValue="overview" keepMounted={false}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconFileText size={14} />}>
            Ringkasan
          </Tabs.Tab>
          <Tabs.Tab value="cea" leftSection={<IconCalculator size={14} />}>
            CEA Quick
          </Tabs.Tab>
          <Tabs.Tab value="bia" leftSection={<IconCoin size={14} />}>
            BIA
          </Tabs.Tab>
          <Tabs.Tab value="etd" leftSection={<IconScale size={14} />}>
            EtD (9 domain)
          </Tabs.Tab>
          <Tabs.Tab value="versions" leftSection={<IconHistory size={14} />}>
            Versi
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="md">
          <OverviewPanel data={data} />
        </Tabs.Panel>
        <Tabs.Panel value="cea" pt="md">
          <CEATab caseId={data.case_id} caseIsLocked={data.is_locked} />
        </Tabs.Panel>
        <Tabs.Panel value="bia" pt="md">
          <BIATab caseId={data.case_id} caseIsLocked={data.is_locked} />
        </Tabs.Panel>
        <Tabs.Panel value="etd" pt="md">
          <EtDTab caseId={data.case_id} caseIsLocked={data.is_locked} />
        </Tabs.Panel>
        <Tabs.Panel value="versions" pt="md">
          <VersionsPanel data={data} />
        </Tabs.Panel>
      </Tabs>

      <Modal
        opened={pendingTransition !== null}
        onClose={() => {
          setPendingTransition(null)
          setReason('')
        }}
        title={pendingTransition ? TRANSITION_LABEL_ID[pendingTransition.name] : ''}
        centered
      >
        <Stack>
          <Text size="sm">Tindakan ini memerlukan alasan. Mohon jelaskan secara singkat.</Text>
          <Textarea
            value={reason}
            onChange={(e) => setReason(e.currentTarget.value)}
            placeholder="Alasan..."
            minRows={3}
            autosize
            required
          />
          <Group justify="flex-end">
            <Button
              variant="default"
              onClick={() => {
                setPendingTransition(null)
                setReason('')
              }}
            >
              Batal
            </Button>
            <Button onClick={confirmTransitionWithReason} loading={transitionMutation.isPending}>
              Lanjutkan
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
