import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Divider,
  Grid,
  Group,
  List,
  Loader,
  NumberInput,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconCalculator, IconDeviceFloppy, IconPlus, IconTrash } from '@tabler/icons-react'

import {
  computeEcon,
  getEconModel,
  getEconParameters,
  getLatestEconResult,
  saveEconModel,
  saveEconParameters,
} from '../api/econ'
import { useAuth } from '../auth/useAuth'
import {
  ALTERNATIVE_LABEL,
  DATA_STATUS_COLOR,
  DATA_STATUS_LABEL,
  PROVISIONAL_DATA_STATUSES,
  PARAM_KEY_DEFAULT_TYPE,
  PARAM_KEY_LABEL,
  PARAM_TYPE_LABEL,
  type Alternative,
  type DataStatus,
  type EconModelPayload,
  type EconParameterPayload,
} from './types'
import { EconResultCard } from './EconResultCard'
import { ValidationImportCard } from './ValidationImportCard'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

const KEY_OPTIONS = Object.entries(PARAM_KEY_LABEL).map(([value, label]) => ({ value, label }))
const ALT_OPTIONS = Object.entries(ALTERNATIVE_LABEL).map(([value, label]) => ({ value, label }))
const STATUS_OPTIONS = Object.entries(DATA_STATUS_LABEL).map(([value, label]) => ({ value, label }))

function rowKey(p: EconParameterPayload): string {
  return `${p.key}:${p.alternative}:${p.year_index ?? ''}`
}

interface ProvenanceSummaryProps {
  params: { data_status: DataStatus }[]
}

/** Round 3 item 6: proxy and assumption values must not read as final RS data. */
function ProvenanceSummary({ params }: ProvenanceSummaryProps): JSX.Element | null {
  if (params.length === 0) return null

  const counts = params.reduce<Record<string, number>>((acc, p) => {
    acc[p.data_status] = (acc[p.data_status] ?? 0) + 1
    return acc
  }, {})
  const provisional = PROVISIONAL_DATA_STATUSES.reduce(
    (sum, status) => sum + (counts[status] ?? 0),
    0,
  )

  return (
    <Stack gap="xs" mb="md">
      <Group gap="xs">
        {(Object.keys(DATA_STATUS_LABEL) as DataStatus[])
          .filter((status) => counts[status])
          .map((status) => (
            <Badge key={status} color={DATA_STATUS_COLOR[status]} variant="light">
              {DATA_STATUS_LABEL[status]}: {counts[status]}
            </Badge>
          ))}
      </Group>
      {provisional > 0 && (
        <Alert color="orange" variant="light" p="xs">
          <Text size="xs">
            {provisional} dari {params.length} parameter masih berstatus proxy atau
            asumsi, sehingga hasil ekonomi belum boleh diperlakukan sebagai data final
            rumah sakit. Ganti ke Observed atau Validated setelah diverifikasi terhadap
            sumbernya.
          </Text>
        </Alert>
      )}
    </Stack>
  )
}


export function EconTab({ caseId, caseIsLocked }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canEdit = !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris')
  const queryClient = useQueryClient()

  const modelQuery = useQuery({ queryKey: ['econ', caseId, 'model'], queryFn: () => getEconModel(caseId) })
  const paramsQuery = useQuery({ queryKey: ['econ', caseId, 'params'], queryFn: () => getEconParameters(caseId) })
  const resultQuery = useQuery({ queryKey: ['econ', caseId, 'result'], queryFn: () => getLatestEconResult(caseId) })

  const [params, setParams] = useState<EconParameterPayload[]>([])
  const [missing, setMissing] = useState<string[]>([])
  const [newKey, setNewKey] = useState<string>('drug_cost')
  const [newAlt, setNewAlt] = useState<Alternative>('intervention')

  const form = useForm<EconModelPayload>({
    initialValues: {
      horizon_years: 1,
      cost_discount_rate: '0',
      outcome_discount_rate: '0',
      wtp_threshold: '85000000',
      annual_budget_baseline: '',
      notes: '',
    },
    validate: {
      horizon_years: (v) => (Number(v) >= 1 ? null : 'Minimal 1 tahun'),
      wtp_threshold: (v) => (Number(v) > 0 ? null : 'WTP harus > 0'),
      cost_discount_rate: (v) => (Number(v) >= 0 ? null : 'Tidak boleh negatif'),
      outcome_discount_rate: (v) => (Number(v) >= 0 ? null : 'Tidak boleh negatif'),
    },
  })

  useEffect(() => {
    if (modelQuery.data) {
      form.setValues({
        horizon_years: modelQuery.data.horizon_years,
        cost_discount_rate: modelQuery.data.cost_discount_rate,
        outcome_discount_rate: modelQuery.data.outcome_discount_rate,
        wtp_threshold: modelQuery.data.wtp_threshold,
        annual_budget_baseline: modelQuery.data.annual_budget_baseline ?? '',
        notes: modelQuery.data.notes,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modelQuery.data])

  useEffect(() => {
    if (paramsQuery.data) {
      setParams(
        paramsQuery.data.map((p) => ({
          key: p.key,
          alternative: p.alternative,
          year_index: p.year_index,
          value: p.value,
          unit: p.unit,
          param_type: p.param_type,
          data_status: p.data_status,
          source_reference: p.source_reference,
          source_year: p.source_year,
          notes: p.notes,
          label: p.label,
        })),
      )
    }
  }, [paramsQuery.data])

  const saveModel = useMutation({
    mutationFn: (payload: EconModelPayload) => saveEconModel(caseId, payload),
    onSuccess: (saved) => {
      queryClient.setQueryData(['econ', caseId, 'model'], saved)
      notifications.show({ color: 'teal', message: 'Model ekonomi disimpan.' })
    },
    onError: () => notifications.show({ color: 'red', message: 'Gagal menyimpan model.' }),
  })

  const saveParams = useMutation({
    mutationFn: (payload: EconParameterPayload[]) => saveEconParameters(caseId, payload),
    onSuccess: (saved) => {
      queryClient.setQueryData(['econ', caseId, 'params'], saved)
      notifications.show({ color: 'teal', message: 'Parameter disimpan.' })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      notifications.show({ color: 'red', message: err.response?.data?.detail ?? 'Gagal menyimpan parameter.' }),
  })

  const compute = useMutation({
    mutationFn: () => computeEcon(caseId),
    onSuccess: (result) => {
      setMissing([])
      queryClient.setQueryData(['econ', caseId, 'result'], result)
      void queryClient.invalidateQueries({ queryKey: ['econ', caseId, 'result'] })
      notifications.show({ color: 'teal', message: 'Perhitungan selesai.' })
    },
    onError: (err: { response?: { data?: { detail?: string; missing?: string[] } } }) => {
      const data = err.response?.data
      if (data?.missing) setMissing(data.missing)
      notifications.show({ color: 'red', title: 'Belum dapat dihitung', message: data?.detail ?? 'Terjadi kesalahan.' })
    },
  })

  if (modelQuery.isLoading) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    )
  }

  const updateParam = (idx: number, patch: Partial<EconParameterPayload>): void => {
    setParams((prev) => prev.map((p, i) => (i === idx ? { ...p, ...patch } : p)))
  }

  const removeParam = (idx: number): void => {
    setParams((prev) => prev.filter((_, i) => i !== idx))
  }

  const addParam = (): void => {
    const candidate: EconParameterPayload = {
      key: newKey,
      alternative: newAlt,
      year_index: null,
      value: '0',
      unit: '',
      param_type: PARAM_KEY_DEFAULT_TYPE[newKey] ?? 'cost',
      data_status: 'assumption',
    }
    if (params.some((p) => rowKey(p) === rowKey(candidate))) {
      notifications.show({ color: 'yellow', message: 'Parameter dengan kunci & alternatif itu sudah ada.' })
      return
    }
    setParams((prev) => [...prev, candidate])
  }

  const latestResult = resultQuery.data

  return (
    <Stack gap="lg">
      {latestResult && <EconResultCard result={latestResult} />}

      {missing.length > 0 && (
        <Alert color="orange" title="Belum dapat dihitung — input wajib yang kurang">
          <List size="sm">
            {missing.map((m) => (
              <List.Item key={m}>{m}</List.Item>
            ))}
          </List>
        </Alert>
      )}

      {/* ── Model scalars ─────────────────────────────────────────── */}
      <Card withBorder padding="lg" radius="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>Parameter Model Ekonomi</Title>
          {!canEdit && (
            <Text size="xs" c="dimmed">
              {caseIsLocked ? 'Kasus terkunci — read-only' : 'Tidak ada izin edit'}
            </Text>
          )}
        </Group>
        <form
          onSubmit={form.onSubmit((values) =>
            saveModel.mutate({ ...values, annual_budget_baseline: values.annual_budget_baseline || null }),
          )}
        >
          <fieldset disabled={!canEdit} style={{ border: 'none', padding: 0, margin: 0 }}>
            <Grid>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <NumberInput label="Horizon (tahun)" min={1} disabled={!canEdit} {...form.getInputProps('horizon_years')} />
              </Grid.Col>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <TextInput label="Discount rate biaya" description="mis. 0.03" disabled={!canEdit} {...form.getInputProps('cost_discount_rate')} />
              </Grid.Col>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <TextInput label="Discount rate QALY" description="mis. 0.03" disabled={!canEdit} {...form.getInputProps('outcome_discount_rate')} />
              </Grid.Col>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <TextInput label="WTP threshold (IDR/QALY)" disabled={!canEdit} {...form.getInputProps('wtp_threshold')} />
              </Grid.Col>
              <Grid.Col span={{ base: 6, sm: 3 }}>
                <TextInput
                  label="Anggaran tahunan baseline (BIA)"
                  description="Dasar % dampak anggaran"
                  disabled={!canEdit} {...form.getInputProps('annual_budget_baseline')}
                />
              </Grid.Col>
              <Grid.Col span={12}>
                <Textarea label="Catatan" autosize minRows={1} disabled={!canEdit} {...form.getInputProps('notes')} />
              </Grid.Col>
            </Grid>
            {canEdit && (
              <Group justify="flex-end" mt="md">
                <Button type="submit" leftSection={<IconDeviceFloppy size={16} />} loading={saveModel.isPending} variant="default">
                  Simpan Model
                </Button>
              </Group>
            )}
          </fieldset>
        </form>
      </Card>

      {/* ── Parameter registry ─────────────────────────────────────── */}
      <Card withBorder padding="lg" radius="md">
        <Title order={4} mb="xs">
          Registri Parameter
        </Title>

        <ProvenanceSummary params={params} />
        <Table.ScrollContainer minWidth={860}>
          <Table verticalSpacing="xs">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Parameter</Table.Th>
                <Table.Th>Alternatif</Table.Th>
                <Table.Th>Nilai</Table.Th>
                <Table.Th>Satuan</Table.Th>
                <Table.Th>Tipe</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Sumber</Table.Th>
                {canEdit && <Table.Th />}
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {params.map((p, idx) => (
                <Table.Tr key={`${rowKey(p)}:${idx}`}>
                  <Table.Td>
                    <Text size="sm">{PARAM_KEY_LABEL[p.key] ?? p.key}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{ALTERNATIVE_LABEL[p.alternative]}</Text>
                  </Table.Td>
                  <Table.Td>
                    <TextInput
                      size="xs"
                      w={140}
                      disabled={!canEdit}
                      value={p.value}
                      onChange={(e) => updateParam(idx, { value: e.currentTarget.value })}
                    />
                  </Table.Td>
                  <Table.Td>
                    <TextInput
                      size="xs"
                      w={110}
                      disabled={!canEdit}
                      value={p.unit ?? ''}
                      onChange={(e) => updateParam(idx, { unit: e.currentTarget.value })}
                    />
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {PARAM_TYPE_LABEL[p.param_type]}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Select
                      size="xs"
                      w={130}
                      disabled={!canEdit}
                      data={STATUS_OPTIONS}
                      allowDeselect={false}
                      value={p.data_status}
                      onChange={(v) => updateParam(idx, { data_status: (v ?? 'assumption') as DataStatus })}
                    />
                  </Table.Td>
                  <Table.Td>
                    <TextInput
                      size="xs"
                      w={180}
                      disabled={!canEdit}
                      value={p.source_reference ?? ''}
                      onChange={(e) => updateParam(idx, { source_reference: e.currentTarget.value })}
                    />
                  </Table.Td>
                  {canEdit && (
                    <Table.Td>
                      <ActionIcon color="red" variant="subtle" onClick={() => removeParam(idx)}>
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Table.Td>
                  )}
                </Table.Tr>
              ))}
              {params.length === 0 && (
                <Table.Tr>
                  <Table.Td colSpan={canEdit ? 8 : 7}>
                    <Text size="sm" c="dimmed">
                      Belum ada parameter. Tambahkan di bawah.
                    </Text>
                  </Table.Td>
                </Table.Tr>
              )}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>

        {canEdit && (
          <>
            <Divider my="md" label="Tambah parameter" labelPosition="left" />
            <Group align="flex-end">
              <Select label="Parameter" data={KEY_OPTIONS} value={newKey} allowDeselect={false} onChange={(v) => setNewKey(v ?? 'drug_cost')} w={260} />
              <Select label="Alternatif" data={ALT_OPTIONS} value={newAlt} allowDeselect={false} onChange={(v) => setNewAlt((v ?? 'intervention') as Alternative)} w={160} />
              <Button variant="light" leftSection={<IconPlus size={16} />} onClick={addParam}>
                Tambah
              </Button>
            </Group>
            <Group justify="flex-end" mt="md">
              <Button
                leftSection={<IconDeviceFloppy size={16} />}
                loading={saveParams.isPending}
                variant="default"
                onClick={() => saveParams.mutate(params)}
              >
                Simpan Parameter
              </Button>
              <Button
                leftSection={<IconCalculator size={16} />}
                loading={compute.isPending}
                color="teal"
                onClick={() => compute.mutate()}
                disabled={!modelQuery.data}
              >
                Hitung
              </Button>
            </Group>
            {!modelQuery.data && (
              <Text size="xs" c="dimmed" ta="right" mt="xs">
                Simpan model terlebih dahulu sebelum menghitung.
              </Text>
            )}
          </>
        )}
      </Card>

      {!latestResult && (
        <Alert color="blue" variant="light">
          Belum ada perhitungan deterministik. Lengkapi model + parameter lalu klik "Hitung".
        </Alert>
      )}

      <ValidationImportCard caseId={caseId} canEdit={canEdit} />
    </Stack>
  )
}
