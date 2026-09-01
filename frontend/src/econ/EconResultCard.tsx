import { Badge, Card, Divider, Grid, Group, Stack, Table, Text, Title } from '@mantine/core'

import { DECISION_COLOR, DECISION_LABEL, type EconResult } from './types'

interface Props {
  result: EconResult
}

function idr(value: string | null, dp = 2): string {
  if (value === null) return 'N/A'
  const n = Number(value)
  if (Number.isNaN(n)) return value
  return n.toLocaleString('id-ID', { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

function qaly(value: string, dp = 6): string {
  const n = Number(value)
  return Number.isNaN(n) ? value : n.toFixed(dp)
}

interface MetricProps {
  label: string
  value: string
  mono?: boolean
}

function Metric({ label, value, mono = true }: MetricProps): JSX.Element {
  return (
    <Stack gap={2}>
      <Text size="xs" c="dimmed">
        {label}
      </Text>
      <Text ff={mono ? 'monospace' : undefined} fw={500}>
        {value}
      </Text>
    </Stack>
  )
}

export function EconResultCard({ result }: Props): JSX.Element {
  const decisionLabel = DECISION_LABEL[result.decision_code] ?? result.decision_code
  const decisionColor = DECISION_COLOR[result.decision_code] ?? 'gray'

  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Title order={4}>Hasil Deterministik (Cost-Utility)</Title>
        <Badge color={decisionColor} variant="filled" size="lg">
          {decisionLabel}
        </Badge>
      </Group>

      <Grid>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="Total cost intervensi" value={`Rp ${idr(result.total_cost_intervention)}`} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="Total cost komparator" value={`Rp ${idr(result.total_cost_comparator)}`} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="Total QALY intervensi" value={qaly(result.total_qaly_intervention)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="Total QALY komparator" value={qaly(result.total_qaly_comparator)} />
        </Grid.Col>
      </Grid>

      <Divider my="md" />

      <Grid>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="Incremental cost" value={`Rp ${idr(result.incremental_cost)}`} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="Incremental QALY" value={qaly(result.incremental_qaly)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric
            label="ICER (Rp/QALY)"
            value={result.icer === null ? 'N/A' : idr(result.icer, 2)}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label={`INB @ WTP ${idr(result.wtp_threshold_used, 0)}`} value={`Rp ${idr(result.inb)}`} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="NMB intervensi" value={`Rp ${idr(result.nmb_intervention)}`} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Metric label="NMB komparator" value={`Rp ${idr(result.nmb_comparator)}`} />
        </Grid.Col>
      </Grid>

      {result.interpretation_text && (
        <Text size="sm" c="dimmed" mt="md">
          {result.interpretation_text}
        </Text>
      )}

      {result.clinical && 'absolute_risk_reduction' in result.clinical && (
        <>
          <Divider my="md" label="Validasi klinis (sekunder)" labelPosition="left" />
          <Grid>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric
                label="Penurunan risiko absolut"
                value={qaly(result.clinical.absolute_risk_reduction, 4)}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric
                label="Relative risk (RR)"
                value={result.clinical.relative_risk ? qaly(result.clinical.relative_risk, 4) : '—'}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric
                label="NNT (12 bulan)"
                value={result.clinical.nnt ? qaly(result.clinical.nnt, 2) : '—'}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 6, sm: 3 }}>
              <Metric
                label="Penghematan admisi/pasien/thn"
                value={`Rp ${idr(result.clinical.admission_cost_saving_per_patient_year, 0)}`}
              />
            </Grid.Col>
          </Grid>
        </>
      )}

      <Divider my="md" label="Rincian per tahun (sebelum → sesudah discounting)" labelPosition="left" />

      <Table.ScrollContainer minWidth={640}>
        <Table striped withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Tahun</Table.Th>
              <Table.Th>Cost int. (annual)</Table.Th>
              <Table.Th>Cost int. (disc.)</Table.Th>
              <Table.Th>Cost komp. (disc.)</Table.Th>
              <Table.Th>QALY int. (disc.)</Table.Th>
              <Table.Th>QALY komp. (disc.)</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {result.per_year.intervention.map((iv, i) => {
              const cv = result.per_year.comparator[i]
              return (
                <Table.Tr key={iv.year}>
                  <Table.Td>{iv.year}</Table.Td>
                  <Table.Td ff="monospace">{idr(iv.annual_cost, 0)}</Table.Td>
                  <Table.Td ff="monospace">{idr(iv.discounted_cost, 0)}</Table.Td>
                  <Table.Td ff="monospace">{cv ? idr(cv.discounted_cost, 0) : '—'}</Table.Td>
                  <Table.Td ff="monospace">{qaly(iv.discounted_qaly, 5)}</Table.Td>
                  <Table.Td ff="monospace">{cv ? qaly(cv.discounted_qaly, 5) : '—'}</Table.Td>
                </Table.Tr>
              )
            })}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>

      <Text size="xs" c="dimmed" mt="sm">
        Algoritma v{result.algorithm_version} · {new Date(result.computed_at).toLocaleString('id-ID')}
      </Text>
    </Card>
  )
}
