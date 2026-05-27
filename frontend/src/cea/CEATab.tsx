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
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconCalculator, IconDeviceFloppy } from '@tabler/icons-react'

import { computeCEA, getCEAInput, listCEAResults, saveCEAInput } from '../api/cea'
import { useAuth } from '../auth/useAuth'
import {
  DATA_SOURCE_LABEL,
  EFFICACY_METRIC_LABEL,
  type CEAInputPayload,
  type DataSource,
  type EfficacyMetric,
} from './types'
import { CEAResultCard } from './CEAResultCard'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

const EFFICACY_OPTIONS = Object.entries(EFFICACY_METRIC_LABEL).map(([value, label]) => ({ value, label }))
const SOURCE_OPTIONS = Object.entries(DATA_SOURCE_LABEL).map(([value, label]) => ({ value, label }))

export function CEATab({ caseId, caseIsLocked }: Props) {
  const { hasRole } = useAuth()
  const canEdit = !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris')

  const queryClient = useQueryClient()

  const inputQuery = useQuery({
    queryKey: ['cea', caseId, 'input'],
    queryFn: () => getCEAInput(caseId),
  })

  const resultsQuery = useQuery({
    queryKey: ['cea', caseId, 'results'],
    queryFn: () => listCEAResults(caseId),
  })

  const form = useForm<CEAInputPayload>({
    initialValues: {
      drug_cost_per_unit: '',
      comparator_cost_per_unit: '',
      efficacy_metric: 'qaly',
      metric_label: '',
      drug_efficacy_value: '',
      comparator_efficacy_value: '',
      patient_population_size: 0,
      wtop_threshold: '250000000.00',
      data_source: 'literature',
      evidence_year: new Date().getFullYear(),
      notes: '',
    },
    validate: {
      drug_cost_per_unit: (v) => (Number(v) >= 0 ? null : 'Biaya tidak boleh negatif'),
      comparator_cost_per_unit: (v) => (Number(v) >= 0 ? null : 'Biaya tidak boleh negatif'),
      drug_efficacy_value: (v) => (Number(v) >= 0 ? null : 'Efikasi tidak boleh negatif'),
      comparator_efficacy_value: (v) => (Number(v) >= 0 ? null : 'Efikasi tidak boleh negatif'),
      wtop_threshold: (v) => (Number(v) > 0 ? null : 'Ambang WTOP harus > 0'),
      patient_population_size: (v) => (Number(v) > 0 ? null : 'Populasi pasien harus > 0'),
      metric_label: (v, values) =>
        values.efficacy_metric === 'other' && !v?.trim()
          ? 'Wajib diisi bila metrik = Lainnya'
          : null,
    },
  })

  // Hydrate form from server when query lands.
  useEffect(() => {
    if (inputQuery.data) {
      form.setValues({
        drug_cost_per_unit: inputQuery.data.drug_cost_per_unit,
        comparator_cost_per_unit: inputQuery.data.comparator_cost_per_unit,
        efficacy_metric: inputQuery.data.efficacy_metric,
        metric_label: inputQuery.data.metric_label,
        drug_efficacy_value: inputQuery.data.drug_efficacy_value,
        comparator_efficacy_value: inputQuery.data.comparator_efficacy_value,
        patient_population_size: inputQuery.data.patient_population_size,
        wtop_threshold: inputQuery.data.wtop_threshold,
        data_source: inputQuery.data.data_source,
        evidence_year: inputQuery.data.evidence_year ?? new Date().getFullYear(),
        notes: inputQuery.data.notes,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputQuery.data])

  const saveMutation = useMutation({
    mutationFn: (payload: CEAInputPayload) => saveCEAInput(caseId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cea', caseId, 'input'] })
      notifications.show({ color: 'teal', message: 'Input CEA disimpan.' })
    },
    onError: (err: { response?: { data?: Record<string, unknown> } }) => {
      const d = err.response?.data ?? {}
      const message = Object.entries(d).map(([k, v]) => `${k}: ${v}`).join('\n') || 'Gagal menyimpan.'
      notifications.show({ color: 'red', title: 'Gagal menyimpan input', message })
    },
  })

  const computeMutation = useMutation({
    mutationFn: () => computeCEA(caseId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cea', caseId, 'results'] })
      notifications.show({ color: 'teal', message: 'CEA berhasil dikomputasi.' })
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
    saveMutation.mutate({
      ...values,
      evidence_year: values.evidence_year || null,
    })
  })

  const latestResult = resultsQuery.data?.[0]

  return (
    <Stack gap="lg">
      {latestResult && <CEAResultCard result={latestResult} />}

      <Card withBorder padding="lg" radius="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>Input CEA</Title>
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
                  <TextInput
                    label="Biaya intervensi per unit (IDR)"
                    description="Total biaya per pasien per periode"
                    required
                    {...form.getInputProps('drug_cost_per_unit')}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <TextInput
                    label="Biaya komparator per unit (IDR)"
                    required
                    {...form.getInputProps('comparator_cost_per_unit')}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Select
                    label="Metrik efikasi"
                    data={EFFICACY_OPTIONS}
                    allowDeselect={false}
                    {...form.getInputProps('efficacy_metric')}
                    onChange={(v) => form.setFieldValue('efficacy_metric', (v ?? 'qaly') as EfficacyMetric)}
                  />
                </Grid.Col>
                {form.values.efficacy_metric === 'other' && (
                  <Grid.Col span={{ base: 12, sm: 6 }}>
                    <TextInput
                      label="Label metrik"
                      placeholder="mis. DALY averted"
                      required
                      {...form.getInputProps('metric_label')}
                    />
                  </Grid.Col>
                )}
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <TextInput
                    label="Nilai efikasi intervensi"
                    required
                    {...form.getInputProps('drug_efficacy_value')}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <TextInput
                    label="Nilai efikasi komparator"
                    required
                    {...form.getInputProps('comparator_efficacy_value')}
                  />
                </Grid.Col>

                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <NumberInput
                    label="Estimasi populasi pasien"
                    description="Per tahun"
                    min={1}
                    required
                    {...form.getInputProps('patient_population_size')}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <TextInput
                    label="Ambang WTOP (IDR per unit efikasi)"
                    description="Default 250 juta IDR per QALY"
                    required
                    {...form.getInputProps('wtop_threshold')}
                  />
                </Grid.Col>

                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Select
                    label="Sumber data"
                    data={SOURCE_OPTIONS}
                    allowDeselect={false}
                    {...form.getInputProps('data_source')}
                    onChange={(v) => form.setFieldValue('data_source', (v ?? 'literature') as DataSource)}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <NumberInput
                    label="Tahun bukti"
                    min={1900}
                    max={new Date().getFullYear()}
                    {...form.getInputProps('evidence_year')}
                  />
                </Grid.Col>
                <Grid.Col span={12}>
                  <Textarea
                    label="Catatan"
                    autosize
                    minRows={2}
                    placeholder="Sumber, asumsi, batasan data..."
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
                      Hitung CEA
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
                    {r.icer_value ?? '—'} IDR · {r.dominance}
                  </Text>
                </Group>
              </Box>
            ))}
          </Stack>
        </Card>
      )}

      {!latestResult && (
        <Alert color="blue" variant="light">
          Belum ada komputasi CEA untuk kasus ini. Isi input lalu klik "Hitung CEA".
        </Alert>
      )}
    </Stack>
  )
}
