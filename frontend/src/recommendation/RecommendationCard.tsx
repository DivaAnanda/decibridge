import { Badge, Card, Grid, Group, Progress, Stack, Text, Title } from '@mantine/core'
import { IconInfoCircle } from '@tabler/icons-react'

import {
  TRAFFIC_LIGHT_COLOR,
  TRAFFIC_LIGHT_LABEL_ID,
  type Recommendation,
} from './types'

interface Props {
  result: Recommendation
}

interface SubScoreProps {
  label: string
  score: string | null
  weightPct: number
}

function SubScore({ label, score, weightPct }: SubScoreProps): JSX.Element {
  const numeric = score === null ? null : Number(score)
  return (
    <Card withBorder padding="sm" radius="sm" bg="gray.0">
      <Text size="xs" c="dimmed">
        {label} (bobot {weightPct}%)
      </Text>
      <Group justify="space-between" align="baseline" mt={4}>
        <Text size="lg" fw={700}>
          {numeric === null ? '—' : numeric.toFixed(1)}
        </Text>
        <Text size="xs" c="dimmed">
          / 100
        </Text>
      </Group>
      <Progress
        value={numeric ?? 0}
        color={numeric === null ? 'gray' : numeric >= 75 ? 'green' : numeric >= 60 ? 'yellow' : 'red'}
        size="xs"
        mt={4}
      />
    </Card>
  )
}

export function RecommendationCard({ result }: Props): JSX.Element {
  return (
    <Card withBorder padding="lg" radius="md" shadow="sm">
      <Group justify="space-between" mb="sm">
        <Stack gap={2}>
          <Text size="xs" c="dimmed">
            Hasil komputasi · {new Date(result.computed_at).toLocaleString('id-ID')}
          </Text>
          <Title order={3}>Rekomendasi Akhir</Title>
        </Stack>
        <Badge color={TRAFFIC_LIGHT_COLOR[result.traffic_light]} size="xl" variant="filled">
          {TRAFFIC_LIGHT_LABEL_ID[result.traffic_light]}
        </Badge>
      </Group>

      <Card withBorder padding="md" radius="sm" bg="blue.0" mb="md">
        <Group justify="space-between">
          <Text size="sm" c="dimmed">
            Skor Komposit
          </Text>
          <Text size="xl" fw={700}>
            {Number(result.composite_score).toFixed(2)} / 100
          </Text>
        </Group>
      </Card>

      <Grid mt="md">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <SubScore label="Bukti EtD" score={result.evidence_strength_score} weightPct={40} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <SubScore label="Cost-Effectiveness" score={result.ce_score} weightPct={30} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <SubScore label="Dampak Anggaran" score={result.budget_score} weightPct={20} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <SubScore label="CBA" score={result.cba_score} weightPct={10} />
        </Grid.Col>

        <Grid.Col span={12}>
          <Card withBorder padding="md" radius="sm">
            <Group gap="xs" mb={4}>
              <IconInfoCircle size={14} />
              <Text size="sm" fw={600}>
                Justifikasi
              </Text>
            </Group>
            <Text size="sm">{result.justification_text}</Text>
          </Card>
        </Grid.Col>

        {result.cba_criteria_count > 0 && (
          <Grid.Col span={12}>
            <Text size="xs" c="dimmed">
              Kriteria CBA: {result.cba_satisfied_count} / {result.cba_criteria_count} terpenuhi
            </Text>
          </Grid.Col>
        )}
      </Grid>

      <Text size="xs" c="dimmed" mt="md" ta="right">
        Algoritma v{result.algorithm_version} · Aggregasi bobot: {result.weight_aggregation_method}
        {result.computed_by ? ` · oleh ${result.computed_by.full_name}` : ''}
      </Text>
    </Card>
  )
}
