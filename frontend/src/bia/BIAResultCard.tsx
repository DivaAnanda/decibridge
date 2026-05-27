import { Badge, Card, Grid, Group, Stack, Text, Title } from '@mantine/core'
import { IconInfoCircle } from '@tabler/icons-react'

import {
  DIRECTION_LABEL_ID,
  SEVERITY_COLOR,
  SEVERITY_LABEL_ID,
  formatIDR,
  type BIAResult,
} from './types'
import { BIATrajectoryChart } from './BIATrajectoryChart'

interface Props {
  result: BIAResult
  budgetBaseline: number
}

export function BIAResultCard({ result, budgetBaseline }: Props): JSX.Element {
  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Stack gap={2}>
          <Text size="xs" c="dimmed">
            Hasil komputasi · {new Date(result.computed_at).toLocaleString('id-ID')}
          </Text>
          <Title order={4}>Budget Impact Analysis</Title>
        </Stack>
        <Stack gap={4} align="flex-end">
          <Badge color={SEVERITY_COLOR[result.severity]} size="lg" variant="filled">
            {SEVERITY_LABEL_ID[result.severity]}
          </Badge>
          <Text size="xs" c="dimmed">
            {DIRECTION_LABEL_ID[result.direction]}
          </Text>
        </Stack>
      </Group>

      <Grid mt="md">
        <Grid.Col span={{ base: 12, sm: 4 }}>
          <Card withBorder padding="md" radius="sm" bg="gray.0">
            <Text size="xs" c="dimmed">
              Dampak Tahun 1
            </Text>
            <Text size="lg" fw={700}>
              {formatIDR(result.year1_net_impact)}
            </Text>
          </Card>
        </Grid.Col>
        {result.year3_net_impact && (
          <Grid.Col span={{ base: 12, sm: 4 }}>
            <Card withBorder padding="md" radius="sm" bg="gray.0">
              <Text size="xs" c="dimmed">
                Dampak Tahun 3
              </Text>
              <Text size="lg" fw={700}>
                {formatIDR(result.year3_net_impact)}
              </Text>
            </Card>
          </Grid.Col>
        )}
        <Grid.Col span={{ base: 12, sm: 4 }}>
          <Card withBorder padding="md" radius="sm" bg="gray.0">
            <Text size="xs" c="dimmed">
              Kumulatif
            </Text>
            <Text size="lg" fw={700}>
              {formatIDR(result.cumulative_impact)}
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              {result.pct_of_annual_budget}% dari anggaran horison
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={12}>
          <BIATrajectoryChart result={result} budgetBaseline={budgetBaseline} />
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
          <Group justify="space-between">
            <Text size="xs" c="dimmed">
              Skor Anggaran (kontribusi ke rekomendasi akhir, bobot 20%)
            </Text>
            <Text size="sm" fw={600}>
              {result.budget_score} / 100
            </Text>
          </Group>
        </Grid.Col>
      </Grid>

      <Text size="xs" c="dimmed" mt="md" ta="right">
        Algoritma v{result.algorithm_version}
        {result.computed_by ? ` · oleh ${result.computed_by.full_name}` : ''}
      </Text>
    </Card>
  )
}
