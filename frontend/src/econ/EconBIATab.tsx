import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Grid,
  Group,
  List,
  Loader,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconCalculator } from '@tabler/icons-react'

import { computeEconBIA, getLatestEconBIA } from '../api/econ'
import { useAuth } from '../auth/useAuth'
import { BIA_SEVERITY_COLOR, BIA_SEVERITY_LABEL, type EconBIAResult } from './types'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

function idr(value: string, dp = 0): string {
  const n = Number(value)
  return Number.isNaN(n) ? value : n.toLocaleString('id-ID', { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

function BIAResultCard({ result }: { result: EconBIAResult }): JSX.Element {
  const color = BIA_SEVERITY_COLOR[result.severity] ?? 'gray'
  const label = BIA_SEVERITY_LABEL[result.severity] ?? result.severity
  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Title order={4}>Dampak Anggaran (dengan cost offset)</Title>
        <Badge color={color} variant="filled" size="lg">
          {label}
        </Badge>
      </Group>

      <Grid>
        <Grid.Col span={{ base: 6, sm: 4 }}>
          <Text size="xs" c="dimmed">Dampak bersih kumulatif</Text>
          <Text ff="monospace" fw={600}>Rp {idr(result.cumulative_net_impact)}</Text>
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4 }}>
          <Text size="xs" c="dimmed">% dari anggaran (horizon)</Text>
          <Text ff="monospace" fw={600}>{Number(result.pct_of_total_baseline).toFixed(2)}%</Text>
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4 }}>
          <Text size="xs" c="dimmed">Skor anggaran (bobot 20%)</Text>
          <Text ff="monospace" fw={600}>{result.budget_score} / 100</Text>
        </Grid.Col>
      </Grid>

      {result.interpretation_text && (
        <Text size="sm" c="dimmed" mt="md">{result.interpretation_text}</Text>
      )}

      <Table.ScrollContainer minWidth={720} mt="md">
        <Table striped withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Tahun</Table.Th>
              <Table.Th>Pasien int.</Table.Th>
              <Table.Th>Δ biaya obat</Table.Th>
              <Table.Th>Cost offset kejadian</Table.Th>
              <Table.Th>Dampak bersih</Table.Th>
              <Table.Th>Kumulatif</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {result.per_year.map((r) => (
              <Table.Tr key={r.year}>
                <Table.Td>{r.year}</Table.Td>
                <Table.Td ff="monospace">{idr(r.patients_intervention)}</Table.Td>
                <Table.Td ff="monospace">{idr(r.incremental_drug_cost)}</Table.Td>
                <Table.Td ff="monospace">{idr(r.event_cost_offset)}</Table.Td>
                <Table.Td ff="monospace">{idr(r.net_budget_impact)}</Table.Td>
                <Table.Td ff="monospace">{idr(r.cumulative_net_impact)}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>

      <Text size="xs" c="dimmed" mt="sm">
        Algoritma v{result.algorithm_version} · {new Date(result.computed_at).toLocaleString('id-ID')}
      </Text>
    </Card>
  )
}

export function EconBIATab({ caseId, caseIsLocked }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canEdit = !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris')
  const queryClient = useQueryClient()

  const [missing, setMissing] = useState<string[]>([])

  const resultQuery = useQuery({
    queryKey: ['econ', caseId, 'bia'],
    queryFn: () => getLatestEconBIA(caseId),
  })

  const compute = useMutation({
    mutationFn: () => computeEconBIA(caseId),
    onSuccess: (result) => {
      setMissing([])
      queryClient.setQueryData(['econ', caseId, 'bia'], result)
      notifications.show({ color: 'teal', message: 'BIA berhasil dihitung.' })
    },
    onError: (err: { response?: { data?: { detail?: string; missing?: string[] } } }) => {
      const data = err.response?.data
      if (data?.missing) setMissing(data.missing)
      notifications.show({ color: 'orange', title: 'Belum dapat dihitung', message: data?.detail ?? 'Terjadi kesalahan.' })
    },
  })

  if (resultQuery.isLoading) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    )
  }

  const latest = resultQuery.data

  return (
    <Stack gap="lg">
      {latest && <BIAResultCard result={latest} />}

      {missing.length > 0 && (
        <Alert color="orange" title="Belum dapat dihitung — parameter yang kurang">
          <List size="sm">
            {missing.map((m) => (
              <List.Item key={m}>{m}</List.Item>
            ))}
          </List>
          <Text size="xs" c="dimmed" mt="xs">
            Lengkapi parameter (populasi, uptake, market share, anggaran baseline) di tab
            "Analisis Ekonomi", lalu hitung ulang.
          </Text>
        </Alert>
      )}

      <Card withBorder padding="md" radius="md">
        <Group justify="space-between">
          <Stack gap={2}>
            <Title order={5}>Hitung BIA (cost offset)</Title>
            <Text size="xs" c="dimmed">
              Memakai parameter bersama dari tab "Analisis Ekonomi": populasi eligible, uptake,
              market share, biaya obat, probabilitas & biaya kejadian, dan anggaran baseline.
            </Text>
          </Stack>
          <Button
            leftSection={<IconCalculator size={16} />}
            onClick={() => compute.mutate()}
            loading={compute.isPending}
            disabled={!canEdit}
            color="teal"
          >
            Hitung BIA
          </Button>
        </Group>
        {!canEdit && (
          <Text size="xs" c="dimmed" mt="xs">
            {caseIsLocked ? 'Kasus terkunci — tidak dapat dihitung ulang.' : 'Anda tidak memiliki izin.'}
          </Text>
        )}
      </Card>

      {!latest && (
        <Alert color="blue" variant="light">
          Belum ada hasil BIA. Lengkapi parameter di "Analisis Ekonomi" lalu klik "Hitung BIA".
        </Alert>
      )}
    </Stack>
  )
}
