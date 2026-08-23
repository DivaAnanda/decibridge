import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  Card,
  Center,
  Divider,
  Grid,
  Group,
  Loader,
  NumberInput,
  Select,
  Slider,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconCalculator, IconDeviceFloppy } from '@tabler/icons-react'

import { computeBIA, getBIAInput, listBIAResults, saveBIAInput } from '../api/bia'
import { useAuth } from '../auth/useAuth'
import type { BIAInputPayload, ProjectionHorizon } from './types'
import { BIAResultCard } from './BIAResultCard'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

const HORIZON_OPTIONS = [
  { value: '1', label: '1 tahun' },
  { value: '3', label: '3 tahun' },
]

export function BIATab({ caseId, caseIsLocked }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canEdit = !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris')

  const queryClient = useQueryClient()

  const inputQuery = useQuery({
    queryKey: ['bia', caseId, 'input'],
    queryFn: () => getBIAInput(caseId),
  })

  const resultsQuery = useQuery({
    queryKey: ['bia', caseId, 'results'],
    queryFn: () => listBIAResults(caseId),
  })

  const form = useForm<BIAInputPayload>({
    initialValues: {
      eligible_population: 1000,
      patient_uptake_year1: '0.30',
      patient_uptake_year3: '0.60',
      market_share_year1: '0.50',
      market_share_year3: '0.70',
      unit_cost_drug: '',
      unit_cost_comparator: '',
      budget_baseline: '10000000000',
      projection_horizon: 3,
      notes: '',
    },
    validate: {
      eligible_population: (v) => (Number(v) > 0 ? null : 'Populasi harus > 0'),
      patient_uptake_year1: (v) =>
        Number(v) >= 0 && Number(v) <= 1 ? null : 'Harus 0–1 (mis. 0.30)',
      patient_uptake_year3: (v) =>
        Number(v) >= 0 && Number(v) <= 1 ? null : 'Harus 0–1',
      market_share_year1: (v) => (Number(v) >= 0 && Number(v) <= 1 ? null : 'Harus 0–1'),
      market_share_year3: (v) => (Number(v) >= 0 && Number(v) <= 1 ? null : 'Harus 0–1'),
      unit_cost_drug: (v) => (Number(v) >= 0 ? null : 'Tidak boleh negatif'),
      unit_cost_comparator: (v) => (Number(v) >= 0 ? null : 'Tidak boleh negatif'),
      budget_baseline: (v) => (Number(v) > 0 ? null : 'Harus > 0'),
    },
  })

  useEffect(() => {
    if (inputQuery.data) {
      form.setValues({
        eligible_population: inputQuery.data.eligible_population,
        patient_uptake_year1: inputQuery.data.patient_uptake_year1,
        patient_uptake_year3: inputQuery.data.patient_uptake_year3,
        market_share_year1: inputQuery.data.market_share_year1,
        market_share_year3: inputQuery.data.market_share_year3,
        unit_cost_drug: inputQuery.data.unit_cost_drug,
        unit_cost_comparator: inputQuery.data.unit_cost_comparator,
        budget_baseline: inputQuery.data.budget_baseline,
        projection_horizon: inputQuery.data.projection_horizon,
        notes: inputQuery.data.notes,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputQuery.data])

  const saveMutation = useMutation({
    mutationFn: (payload: BIAInputPayload) => saveBIAInput(caseId, payload),
    onSuccess: (saved) => {
      // Seed the cache from the PUT response so the "Hitung BIA" button enables
      // immediately — no refetch round-trip, no page refresh needed.
      queryClient.setQueryData(['bia', caseId, 'input'], saved)
      notifications.show({ color: 'teal', message: 'Input BIA disimpan.' })
    },
    onError: (err: { response?: { data?: Record<string, unknown> } }) => {
      const d = err.response?.data ?? {}
      const message = Object.entries(d).map(([k, v]) => `${k}: ${v}`).join('\n') || 'Gagal menyimpan.'
      notifications.show({ color: 'red', title: 'Gagal menyimpan input', message })
    },
  })

  const computeMutation = useMutation({
    mutationFn: () => computeBIA(caseId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['bia', caseId, 'results'] })
      notifications.show({ color: 'teal', message: 'BIA berhasil dikomputasi.' })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      notifications.show({
        color: 'red',
        title: 'Komputasi gagal',
        message: err.response?.data?.detail ?? 'Terjadi kesalahan.',
      })
    },
  })

  if (inputQuery.isLoading) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    )
  }

  const handleSubmit = form.onSubmit((values) => {
    saveMutation.mutate(values)
  })

  const latestResult = resultsQuery.data?.[0]
  const budgetBaseline = Number(form.values.budget_baseline) || 0

  return (
    <Stack gap="lg">
      {latestResult && <BIAResultCard result={latestResult} budgetBaseline={budgetBaseline} />}

      <Card withBorder padding="lg" radius="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>Input BIA</Title>
          {!canEdit && (
            <Text size="xs" c="dimmed">
              {caseIsLocked ? 'Kasus terkunci — input read-only' : 'Anda tidak memiliki izin edit'}
            </Text>
          )}
        </Group>

        <form onSubmit={handleSubmit}>
          <fieldset disabled={!canEdit} style={{ border: 'none', padding: 0, margin: 0 }}>
            <Stack gap="md">
              <Grid>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <NumberInput
                    label="Populasi pasien yang memenuhi syarat (per tahun)"
                    min={1}
                    required
                    {...form.getInputProps('eligible_population')}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Select
                    label="Horison proyeksi"
                    data={HORIZON_OPTIONS}
                    allowDeselect={false}
                    value={String(form.values.projection_horizon)}
                    onChange={(v) =>
                      form.setFieldValue(
                        'projection_horizon',
                        (Number(v) || 3) as ProjectionHorizon,
                      )
                    }
                  />
                </Grid.Col>

                <Grid.Col span={12}>
                  <Divider label="Uptake & pangsa pasar" labelPosition="left" />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Text size="sm" mb={4}>
                    Uptake Tahun 1: {(Number(form.values.patient_uptake_year1) * 100).toFixed(0)}%
                  </Text>
                  <Slider
                    min={0}
                    max={1}
                    step={0.01}
                    value={Number(form.values.patient_uptake_year1) || 0}
                    onChange={(v) => form.setFieldValue('patient_uptake_year1', v.toFixed(4))}
                    label={(v) => `${(v * 100).toFixed(0)}%`}
                    disabled={!canEdit}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Text size="sm" mb={4}>
                    Uptake Tahun 3: {(Number(form.values.patient_uptake_year3) * 100).toFixed(0)}%
                  </Text>
                  <Slider
                    min={0}
                    max={1}
                    step={0.01}
                    value={Number(form.values.patient_uptake_year3) || 0}
                    onChange={(v) => form.setFieldValue('patient_uptake_year3', v.toFixed(4))}
                    label={(v) => `${(v * 100).toFixed(0)}%`}
                    disabled={!canEdit}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Text size="sm" mb={4}>
                    Pangsa pasar Tahun 1: {(Number(form.values.market_share_year1) * 100).toFixed(0)}%
                  </Text>
                  <Slider
                    min={0}
                    max={1}
                    step={0.01}
                    value={Number(form.values.market_share_year1) || 0}
                    onChange={(v) => form.setFieldValue('market_share_year1', v.toFixed(4))}
                    label={(v) => `${(v * 100).toFixed(0)}%`}
                    disabled={!canEdit}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Text size="sm" mb={4}>
                    Pangsa pasar Tahun 3: {(Number(form.values.market_share_year3) * 100).toFixed(0)}%
                  </Text>
                  <Slider
                    min={0}
                    max={1}
                    step={0.01}
                    value={Number(form.values.market_share_year3) || 0}
                    onChange={(v) => form.setFieldValue('market_share_year3', v.toFixed(4))}
                    label={(v) => `${(v * 100).toFixed(0)}%`}
                    disabled={!canEdit}
                  />
                </Grid.Col>

                <Grid.Col span={12}>
                  <Divider label="Biaya & anggaran (IDR)" labelPosition="left" />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <TextInput
                    label="Biaya intervensi per pasien per tahun"
                    required
                    {...form.getInputProps('unit_cost_drug')}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <TextInput
                    label="Biaya komparator per pasien per tahun"
                    required
                    {...form.getInputProps('unit_cost_comparator')}
                  />
                </Grid.Col>
                <Grid.Col span={12}>
                  <TextInput
                    label="Anggaran farmasi tahunan baseline"
                    description="Total anggaran obat RS per tahun — dasar perhitungan % dampak"
                    required
                    {...form.getInputProps('budget_baseline')}
                  />
                </Grid.Col>

                <Grid.Col span={12}>
                  <Textarea
                    label="Catatan"
                    placeholder="Asumsi uptake, sumber data pangsa pasar, sensitivitas..."
                    autosize
                    minRows={2}
                    {...form.getInputProps('notes')}
                  />
                </Grid.Col>
              </Grid>

              {canEdit && (
                <>
                  <Divider />
                  <Group justify="flex-end">
                    <Button
                      type="submit"
                      leftSection={<IconDeviceFloppy size={16} />}
                      loading={saveMutation.isPending}
                      variant="default"
                    >
                      Simpan Input
                    </Button>
                    <Button
                      onClick={() => computeMutation.mutate()}
                      leftSection={<IconCalculator size={16} />}
                      loading={computeMutation.isPending}
                      disabled={!inputQuery.data}
                      color="teal"
                    >
                      Hitung BIA
                    </Button>
                  </Group>
                  {!inputQuery.data && (
                    <Text size="xs" c="dimmed" ta="right">
                      Simpan input terlebih dahulu sebelum menghitung.
                    </Text>
                  )}
                </>
              )}
            </Stack>
          </fieldset>
        </form>
      </Card>

      {resultsQuery.data && resultsQuery.data.length > 1 && (
        <Card withBorder padding="lg" radius="md">
          <Title order={5} mb="sm">
            Riwayat komputasi
          </Title>
          <Stack gap="xs">
            {resultsQuery.data.slice(1).map((r) => (
              <Box key={r.id} pb="xs" style={{ borderBottom: '1px solid var(--mantine-color-gray-2)' }}>
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    {new Date(r.computed_at).toLocaleString('id-ID')}
                  </Text>
                  <Text size="sm" ff="monospace">
                    {r.cumulative_impact} IDR · {r.severity}
                  </Text>
                </Group>
              </Box>
            ))}
          </Stack>
        </Card>
      )}

      {!latestResult && (
        <Alert color="blue" variant="light">
          Belum ada komputasi BIA untuk kasus ini. Isi input lalu klik "Hitung BIA".
        </Alert>
      )}
    </Stack>
  )
}
