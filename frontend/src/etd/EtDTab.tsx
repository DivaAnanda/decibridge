import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Card,
  Center,
  Grid,
  Group,
  Loader,
  Progress,
  Stack,
  Tabs,
  Text,
  Title,
} from '@mantine/core'

import {
  getSummary,
  listAppraisals,
  listDomains,
  listReferences,
} from '../api/etd'
import { CERTAINTY_COLOR, type DomainAggregate } from './types'
import { DomainCard } from './DomainCard'
import { ReferencesPanel } from './ReferencesPanel'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

export function EtDTab({ caseId, caseIsLocked }: Props): JSX.Element {
  const domainsQuery = useQuery({ queryKey: ['etd', 'domains'], queryFn: listDomains })
  const refsQuery = useQuery({ queryKey: ['references', caseId], queryFn: () => listReferences(caseId) })
  const appraisalsQuery = useQuery({
    queryKey: ['etd', caseId, 'appraisals'],
    queryFn: () => listAppraisals(caseId),
  })
  const summaryQuery = useQuery({
    queryKey: ['etd', caseId, 'summary'],
    queryFn: () => getSummary(caseId),
  })

  const aggregateBySlug = useMemo<Record<string, DomainAggregate | undefined>>(() => {
    const out: Record<string, DomainAggregate | undefined> = {}
    for (const d of summaryQuery.data?.per_domain ?? []) {
      out[d.domain_slug] = d
    }
    return out
  }, [summaryQuery.data])

  if (domainsQuery.isLoading) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    )
  }

  const domains = domainsQuery.data ?? []
  const overall = summaryQuery.data?.overall
  const completionPct = overall
    ? Math.round((overall.domains_completed / Math.max(overall.domains_total, 1)) * 100)
    : 0

  return (
    <Stack gap="lg">
      {overall && (
        <Card withBorder padding="lg" radius="md">
          <Group justify="space-between" mb="sm">
            <Title order={4}>Ringkasan EtD</Title>
            {overall.average_certainty && (
              <Badge color={CERTAINTY_COLOR[overall.average_certainty]} variant="filled" size="lg">
                Kepastian rata-rata: {overall.average_certainty}
              </Badge>
            )}
          </Group>
          <Grid>
            <Grid.Col span={{ base: 12, sm: 4 }}>
              <Card withBorder padding="md" radius="sm" bg="gray.0">
                <Text size="xs" c="dimmed">
                  Skor Kekuatan Bukti
                </Text>
                <Text size="xl" fw={700}>
                  {overall.evidence_strength_score ?? '—'} / 100
                </Text>
                <Text size="xs" c="dimmed" mt={4}>
                  Bobot 40% pada sintesis traffic-light
                </Text>
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 4 }}>
              <Card withBorder padding="md" radius="sm" bg="gray.0">
                <Text size="xs" c="dimmed">
                  Domain Terisi
                </Text>
                <Text size="xl" fw={700}>
                  {overall.domains_completed} / {overall.domains_total}
                </Text>
                <Progress value={completionPct} mt="xs" size="sm" />
              </Card>
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 4 }}>
              <Card withBorder padding="md" radius="sm" bg="gray.0">
                <Text size="xs" c="dimmed">
                  Total suara KFT
                </Text>
                <Text size="xl" fw={700}>
                  {(summaryQuery.data?.per_domain ?? []).reduce(
                    (sum, d) => sum + d.appraisal_count,
                    0,
                  )}
                </Text>
              </Card>
            </Grid.Col>
          </Grid>
        </Card>
      )}

      <ReferencesPanel caseId={caseId} caseIsLocked={caseIsLocked} />

      <Card withBorder padding="lg" radius="md">
        <Title order={4} mb="md">
          9 Domain GRADE EtD
        </Title>
        <Tabs defaultValue={domains[0]?.slug} orientation="vertical" variant="pills">
          <Tabs.List>
            {domains.map((d) => {
              const agg = aggregateBySlug[d.slug]
              const done = agg && agg.appraisal_count > 0
              return (
                <Tabs.Tab
                  key={d.slug}
                  value={d.slug}
                  rightSection={
                    done && (
                      <Badge size="xs" variant="light">
                        {agg.appraisal_count}
                      </Badge>
                    )
                  }
                >
                  {d.order}. {d.display_name_id}
                </Tabs.Tab>
              )
            })}
          </Tabs.List>

          {domains.map((d) => (
            <Tabs.Panel key={d.slug} value={d.slug} pl="md">
              <DomainCard
                caseId={caseId}
                caseIsLocked={caseIsLocked}
                domain={d}
                references={refsQuery.data ?? []}
                allAppraisals={appraisalsQuery.data ?? []}
                domainAggregate={aggregateBySlug[d.slug]}
              />
            </Tabs.Panel>
          ))}
        </Tabs>
      </Card>
    </Stack>
  )
}
