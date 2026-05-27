import { Card, Text } from '@mantine/core'
import { AreaChart } from '@mantine/charts'

import { formatIDR, type BIAResult } from './types'

interface Props {
  result: BIAResult
  budgetBaseline: number
}

/**
 * Stacked area chart of cumulative net budget impact across the projection horizon.
 * Y-axis: cumulative IDR added to (or removed from) the pharmacy budget.
 * X-axis: Year 0 (baseline) -> Year 1 -> Year 2 (interpolated) -> Year 3.
 */
export function BIATrajectoryChart({ result, budgetBaseline }: Props): JSX.Element {
  const y1 = Number(result.year1_net_impact)
  const y2 = result.year2_net_impact_interpolated ? Number(result.year2_net_impact_interpolated) : null
  const y3 = result.year3_net_impact ? Number(result.year3_net_impact) : null

  const data = [
    { year: 'Y0 (baseline)', cumulative: 0, baseline: budgetBaseline },
    { year: 'Y1', cumulative: y1, baseline: budgetBaseline },
  ]
  if (y2 !== null) {
    data.push({ year: 'Y2 (interp.)', cumulative: y1 + y2, baseline: budgetBaseline })
  }
  if (y3 !== null && y2 !== null) {
    data.push({ year: 'Y3', cumulative: y1 + y2 + y3, baseline: budgetBaseline })
  }

  return (
    <Card withBorder padding="md" radius="md">
      <Text size="sm" fw={600} mb="xs">
        Proyeksi Dampak Anggaran Kumulatif
      </Text>
      <Text size="xs" c="dimmed" mb="sm">
        Sumbu Y = dampak bersih kumulatif (IDR). Garis baseline = anggaran tahunan.
      </Text>
      <AreaChart
        h={260}
        data={data}
        dataKey="year"
        series={[
          { name: 'cumulative', label: 'Kumulatif (IDR)', color: 'blue.6' },
          { name: 'baseline', label: 'Anggaran tahunan', color: 'gray.5' },
        ]}
        curveType="monotone"
        withGradient
        valueFormatter={(value) => formatIDR(value)}
        withLegend
      />
    </Card>
  )
}
