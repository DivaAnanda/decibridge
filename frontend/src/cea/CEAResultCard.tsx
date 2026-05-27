import { Alert, Badge, Card, Grid, Group, Stack, Text, Title, Tooltip } from '@mantine/core'
import { IconAlertTriangle, IconInfoCircle } from '@tabler/icons-react'

import {
  DOMINANCE_COLOR,
  DOMINANCE_LABEL_ID,
  formatIDR,
  type CEAResult,
} from './types'

interface Props {
  result: CEAResult
}

export function CEAResultCard({ result }: Props) {
  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Stack gap={2}>
          <Text size="xs" c="dimmed">
            Hasil komputasi · {new Date(result.computed_at).toLocaleString('id-ID')}
          </Text>
          <Title order={4}>Cost-Effectiveness Analysis</Title>
        </Stack>
        <Badge color={DOMINANCE_COLOR[result.dominance]} size="lg" variant="filled">
          {DOMINANCE_LABEL_ID[result.dominance]}
        </Badge>
      </Group>

      <Grid mt="md">
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Card withBorder padding="md" radius="sm" bg="gray.0">
            <Text size="xs" c="dimmed">
              ICER (Incremental Cost-Effectiveness Ratio)
            </Text>
            <Text size="xl" fw={700}>
              {result.icer_value ? `${formatIDR(result.icer_value)} / unit` : '—'}
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              Ambang WTOP: {formatIDR(result.wtop_threshold_used)}
            </Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Card withBorder padding="md" radius="sm" bg="gray.0">
            <Text size="xs" c="dimmed">
              Skor CE (kontribusi ke rekomendasi akhir)
            </Text>
            <Text size="xl" fw={700}>
              {result.ce_score} / 100
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              Bobot 30% pada sintesis traffic-light
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Text size="xs" c="dimmed">
            Selisih biaya (Δ Cost)
          </Text>
          <Text>{formatIDR(result.incremental_cost)}</Text>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Text size="xs" c="dimmed">
            Selisih efikasi (Δ Effect)
          </Text>
          <Text>{Number(result.incremental_effect).toFixed(4)}</Text>
        </Grid.Col>

        <Grid.Col span={12}>
          <Card withBorder padding="md" radius="sm">
            <Group gap="xs" mb={4}>
              <IconInfoCircle size={14} />
              <Text size="sm" fw={600}>
                Interpretasi
              </Text>
            </Group>
            <Text size="sm">{result.interpretation_text}</Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={12}>
          <Stack gap={4}>
            <Group justify="space-between">
              <Tooltip label="ICER dengan asumsi merugikan (biaya +20%, efikasi -20%)">
                <Text size="xs" c="dimmed">
                  ICER batas bawah (skenario adverse)
                </Text>
              </Tooltip>
              <Text size="sm" ff="monospace">
                {result.sensitivity_low_icer ? formatIDR(result.sensitivity_low_icer) : '—'}
              </Text>
            </Group>
            <Group justify="space-between">
              <Tooltip label="ICER dengan asumsi favourable (biaya -20%, efikasi +20%)">
                <Text size="xs" c="dimmed">
                  ICER batas atas (skenario favourable)
                </Text>
              </Tooltip>
              <Text size="sm" ff="monospace">
                {result.sensitivity_high_icer ? formatIDR(result.sensitivity_high_icer) : '—'}
              </Text>
            </Group>
          </Stack>
        </Grid.Col>

        {result.threshold_sensitivity_flag && (
          <Grid.Col span={12}>
            <Alert color="yellow" icon={<IconAlertTriangle size={16} />} variant="light">
              ICER berada dalam ±20% dari ambang WTOP. Pertimbangkan analisis sensitivitas lebih lanjut
              dan input domain EtD yang lain sebelum mengambil keputusan.
            </Alert>
          </Grid.Col>
        )}
      </Grid>

      <Text size="xs" c="dimmed" mt="md" ta="right">
        Algoritma v{result.algorithm_version}
        {result.computed_by ? ` · oleh ${result.computed_by.full_name}` : ''}
      </Text>
    </Card>
  )
}
