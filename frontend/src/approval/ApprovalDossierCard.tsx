import { useQuery } from '@tanstack/react-query'
import { Alert, Badge, Card, Center, Grid, Group, Loader, Stack, Text, Title } from '@mantine/core'

import { getLatestCEAResult } from '../api/cea'
import { listCEAResults } from '../api/cea'
import { listBIAResults } from '../api/bia'
import { getSummary as getEtDSummary } from '../api/etd'
import { getLatestRecommendation } from '../api/recommendation'
import { DOMINANCE_LABEL_ID, formatIDR as formatCEA } from '../cea/types'
import { SEVERITY_LABEL_ID, formatIDR as formatBIA } from '../bia/types'
import { TRAFFIC_LIGHT_COLOR, TRAFFIC_LIGHT_LABEL_ID } from '../recommendation/types'
import { CERTAINTY_COLOR } from '../etd/types'

interface Props {
  caseId: string
}

export function ApprovalDossierCard({ caseId }: Props): JSX.Element {
  const ceaQuery = useQuery({ queryKey: ['cea', caseId, 'latest'], queryFn: () => getLatestCEAResult(caseId) })
  const ceaListQuery = useQuery({ queryKey: ['cea', caseId, 'results'], queryFn: () => listCEAResults(caseId) })
  const biaQuery = useQuery({ queryKey: ['bia', caseId, 'results'], queryFn: () => listBIAResults(caseId) })
  const etdQuery = useQuery({ queryKey: ['etd', caseId, 'summary'], queryFn: () => getEtDSummary(caseId) })
  const recoQuery = useQuery({
    queryKey: ['recommendation', caseId, 'latest'],
    queryFn: () => getLatestRecommendation(caseId),
  })

  const isLoading =
    ceaQuery.isLoading || ceaListQuery.isLoading || biaQuery.isLoading || etdQuery.isLoading || recoQuery.isLoading

  if (isLoading) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    )
  }

  const cea = ceaQuery.data
  const bia = biaQuery.data?.[0] ?? null
  const etd = etdQuery.data
  const reco = recoQuery.data

  return (
    <Card withBorder padding="lg" radius="md">
      <Title order={4} mb="md">
        Dossier Kasus untuk Tinjauan
      </Title>
      <Text size="sm" c="dimmed" mb="md">
        Ringkasan seluruh komponen evaluasi. Tinjau dengan saksama sebelum sign-off — keputusan
        Anda akan dicatat permanen.
      </Text>

      {!reco && (
        <Alert color="yellow" variant="light" mb="md">
          Belum ada rekomendasi terkomputasi. Buka tab Rekomendasi dan klik
          "Hitung Rekomendasi" terlebih dahulu sebelum sign-off.
        </Alert>
      )}

      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder padding="md" radius="sm">
            <Text size="xs" c="dimmed">
              CEA (Cost-Effectiveness)
            </Text>
            {cea ? (
              <Stack gap={4} mt={4}>
                <Group justify="space-between">
                  <Text size="sm">ICER</Text>
                  <Text size="sm" fw={600}>
                    {cea.icer_value ? `${formatCEA(cea.icer_value)} / unit` : '—'}
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Dominance</Text>
                  <Badge variant="light" size="sm">
                    {DOMINANCE_LABEL_ID[cea.dominance]}
                  </Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Skor CE</Text>
                  <Text size="sm" fw={600}>
                    {cea.ce_score} / 100
                  </Text>
                </Group>
              </Stack>
            ) : (
              <Text size="sm" c="red" mt={4}>
                Belum dihitung.
              </Text>
            )}
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder padding="md" radius="sm">
            <Text size="xs" c="dimmed">
              BIA (Budget Impact)
            </Text>
            {bia ? (
              <Stack gap={4} mt={4}>
                <Group justify="space-between">
                  <Text size="sm">Kumulatif</Text>
                  <Text size="sm" fw={600}>
                    {formatBIA(bia.cumulative_impact)}
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">% Anggaran</Text>
                  <Text size="sm" fw={600}>
                    {bia.pct_of_annual_budget}%
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Severity</Text>
                  <Badge variant="light" size="sm">
                    {SEVERITY_LABEL_ID[bia.severity]}
                  </Badge>
                </Group>
              </Stack>
            ) : (
              <Text size="sm" c="red" mt={4}>
                Belum dihitung.
              </Text>
            )}
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder padding="md" radius="sm">
            <Text size="xs" c="dimmed">
              EtD (Evidence-to-Decision)
            </Text>
            {etd && etd.overall.domains_completed > 0 ? (
              <Stack gap={4} mt={4}>
                <Group justify="space-between">
                  <Text size="sm">Skor Kekuatan Bukti</Text>
                  <Text size="sm" fw={600}>
                    {etd.overall.evidence_strength_score ?? '—'} / 100
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Domain terisi</Text>
                  <Text size="sm" fw={600}>
                    {etd.overall.domains_completed} / {etd.overall.domains_total}
                  </Text>
                </Group>
                {etd.overall.average_certainty && (
                  <Group justify="space-between">
                    <Text size="sm">Kepastian rata-rata</Text>
                    <Badge color={CERTAINTY_COLOR[etd.overall.average_certainty]} variant="light" size="sm">
                      {etd.overall.average_certainty}
                    </Badge>
                  </Group>
                )}
              </Stack>
            ) : (
              <Text size="sm" c="red" mt={4}>
                Belum ada penilaian anggota KFT.
              </Text>
            )}
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder padding="md" radius="sm">
            <Text size="xs" c="dimmed">
              Rekomendasi
            </Text>
            {reco ? (
              <Stack gap={4} mt={4}>
                <Group justify="space-between">
                  <Text size="sm">Traffic-light</Text>
                  <Badge color={TRAFFIC_LIGHT_COLOR[reco.traffic_light]} variant="filled" size="sm">
                    {TRAFFIC_LIGHT_LABEL_ID[reco.traffic_light]}
                  </Badge>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Skor Komposit</Text>
                  <Text size="sm" fw={600}>
                    {Number(reco.composite_score).toFixed(2)} / 100
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Kriteria CBA</Text>
                  <Text size="sm" fw={600}>
                    {reco.cba_satisfied_count} / {reco.cba_criteria_count}
                  </Text>
                </Group>
                <Group justify="space-between">
                  <Text size="sm">Dihitung</Text>
                  <Text size="sm">
                    {new Date(reco.computed_at).toLocaleString('id-ID')}
                  </Text>
                </Group>
              </Stack>
            ) : (
              <Text size="sm" c="red" mt={4}>
                Belum terkomputasi.
              </Text>
            )}
          </Card>
        </Grid.Col>

        {reco && (
          <Grid.Col span={12}>
            <Card withBorder padding="md" radius="sm">
              <Text size="xs" c="dimmed">
                Justifikasi Rekomendasi
              </Text>
              <Text size="sm" mt={4}>
                {reco.justification_text}
              </Text>
            </Card>
          </Grid.Col>
        )}
      </Grid>
    </Card>
  )
}
