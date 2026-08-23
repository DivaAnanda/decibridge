import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Center,
  Grid,
  Group,
  List,
  Loader,
  NumberInput,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconChartDots, IconPlayerPlay } from '@tabler/icons-react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { computeEconPSA, getLatestEconPSA } from '../api/econ'
import { useAuth } from '../auth/useAuth'
import type { EconPSAResult } from './types'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

function Metric({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <Stack gap={2}>
      <Text size="xs" c="dimmed">{label}</Text>
      <Text ff="monospace" fw={600}>{value}</Text>
    </Stack>
  )
}

function PSACharts({ result }: { result: EconPSAResult }): JSX.Element {
  const scatterData = result.scatter.map(([x, y]) => ({ x, y }))
  const ceacData = result.ceac.map((p) => ({ wtp: p.wtp / 1_000_000, prob: p.prob * 100 }))
  const baseX = Number(result.base_case_incremental_qaly)
  const baseY = Number(result.base_case_incremental_cost)

  return (
    <Grid>
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card withBorder padding="md" radius="md">
          <Title order={5} mb="xs">Cost-Effectiveness Plane</Title>
          <Text size="xs" c="dimmed" mb="sm">
            X: incremental QALY · Y: incremental cost (IDR). Titik merah = base case deterministik.
          </Text>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ top: 8, right: 12, bottom: 8, left: 12 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="x" name="ΔQALY" tickFormatter={(v) => v.toFixed(3)} />
              <YAxis type="number" dataKey="y" name="ΔCost" tickFormatter={(v) => `${(v / 1_000_000).toFixed(0)}jt`} />
              <ReferenceLine x={0} stroke="#888" />
              <ReferenceLine y={0} stroke="#888" />
              <Tooltip
                formatter={(v: number, name) =>
                  name === 'y' ? `Rp ${v.toLocaleString('id-ID')}` : v.toFixed(4)
                }
              />
              <Scatter data={scatterData} fill="#4dabf7" fillOpacity={0.35} isAnimationActive={false} />
              <ReferenceDot x={baseX} y={baseY} r={6} fill="#e03131" stroke="white" />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>
      </Grid.Col>

      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card withBorder padding="md" radius="md">
          <Title order={5} mb="xs">CEAC</Title>
          <Text size="xs" c="dimmed" mb="sm">
            Probabilitas cost-effective (%) terhadap WTP (juta IDR/QALY).
          </Text>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={ceacData} margin={{ top: 8, right: 12, bottom: 8, left: 12 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="wtp" tickFormatter={(v) => `${v.toFixed(0)}jt`} />
              <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                formatter={(v: number) => `${v.toFixed(1)}%`}
                labelFormatter={(v) => `WTP ${v} jt IDR/QALY`}
              />
              <Line type="monotone" dataKey="prob" stroke="#2f9e44" dot={false} strokeWidth={2} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Grid.Col>
    </Grid>
  )
}

export function EconPSATab({ caseId, caseIsLocked }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canEdit = !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris')
  const queryClient = useQueryClient()

  const [nSim, setNSim] = useState<number>(1000)
  const [seed, setSeed] = useState<number>(42)
  const [missing, setMissing] = useState<string[]>([])

  const resultQuery = useQuery({
    queryKey: ['econ', caseId, 'psa'],
    queryFn: () => getLatestEconPSA(caseId),
  })

  const compute = useMutation({
    mutationFn: () => computeEconPSA(caseId, { n_simulations: nSim, seed }),
    onSuccess: (result) => {
      setMissing([])
      queryClient.setQueryData(['econ', caseId, 'psa'], result)
      notifications.show({ color: 'teal', message: 'PSA selesai.' })
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
      {latest && (
        <Card withBorder padding="lg" radius="md">
          <Group justify="space-between" mb="sm">
            <Title order={4}>Analisis Sensitivitas Probabilistik (PSA)</Title>
            <Group gap={4}>
              <IconChartDots size={18} />
              <Text fw={700}>
                P(cost-effective) = {(Number(latest.prob_cost_effective_base) * 100).toFixed(1)}%
              </Text>
            </Group>
          </Group>
          <Grid>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric label="Iterasi" value={String(latest.n_simulations)} />
            </Grid.Col>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric label="Seed" value={String(latest.random_seed)} />
            </Grid.Col>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric label="Mean Δcost" value={`Rp ${Number(latest.mean_incremental_cost).toLocaleString('id-ID', { maximumFractionDigits: 0 })}`} />
            </Grid.Col>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric label="Mean ΔQALY" value={Number(latest.mean_incremental_qaly).toFixed(4)} />
            </Grid.Col>
          </Grid>
          {latest.interpretation_text && (
            <Text size="sm" c="dimmed" mt="md">{latest.interpretation_text}</Text>
          )}
        </Card>
      )}

      {latest && <PSACharts result={latest} />}

      {missing.length > 0 && (
        <Alert color="orange" title="Belum dapat dihitung — parameter yang kurang">
          <List size="sm">
            {missing.map((m) => (
              <List.Item key={m}>{m}</List.Item>
            ))}
          </List>
          <Text size="xs" c="dimmed" mt="xs">
            Lengkapi parameter di tab "Analisis Ekonomi" (dan distribusinya) lalu jalankan ulang.
          </Text>
        </Alert>
      )}

      <Card withBorder padding="md" radius="md">
        <Group justify="space-between" align="flex-end">
          <Stack gap={2}>
            <Title order={5}>Jalankan PSA</Title>
            <Text size="xs" c="dimmed">
              Monte-Carlo memakai distribusi ketidakpastian tiap parameter (di tab Analisis Ekonomi).
              Seed tetap → hasil dapat direproduksi.
            </Text>
          </Stack>
          <Group align="flex-end">
            <NumberInput label="Iterasi" min={100} max={20000} step={500} value={nSim} onChange={(v) => setNSim(Number(v) || 1000)} w={120} />
            <NumberInput label="Seed" min={0} value={seed} onChange={(v) => setSeed(Number(v) || 0)} w={100} />
            <Button
              leftSection={<IconPlayerPlay size={16} />}
              onClick={() => compute.mutate()}
              loading={compute.isPending}
              disabled={!canEdit}
              color="teal"
            >
              Hitung PSA
            </Button>
          </Group>
        </Group>
        {!canEdit && (
          <Text size="xs" c="dimmed" mt="xs">
            {caseIsLocked ? 'Kasus terkunci — tidak dapat dijalankan.' : 'Anda tidak memiliki izin.'}
          </Text>
        )}
      </Card>

      {!latest && (
        <Alert color="blue" variant="light">
          Belum ada hasil PSA. Pastikan parameter deterministik lengkap, lalu klik "Hitung PSA".
        </Alert>
      )}
    </Stack>
  )
}
