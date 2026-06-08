import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  SegmentedControl,
  Slider,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconDeviceFloppy } from '@tabler/icons-react'

import { getWeightsSummary, listWeights, upsertWeights } from '../api/recommendation'
import { listDomains } from '../api/etd'
import { useAuth } from '../auth/useAuth'

interface Props {
  caseId: string
  caseIsLocked: boolean
}

export function WeightsCard({ caseId, caseIsLocked }: Props): JSX.Element {
  const { user, hasRole } = useAuth()
  const canVote = !caseIsLocked && hasRole('kft_member', 'ketua_kft')
  const queryClient = useQueryClient()

  const [method, setMethod] = useState<'mean' | 'median'>('mean')
  const [myWeights, setMyWeights] = useState<Record<string, number>>({})

  const domainsQuery = useQuery({ queryKey: ['etd', 'domains'], queryFn: listDomains })
  const votesQuery = useQuery({
    queryKey: ['recommendation', caseId, 'weights'],
    queryFn: () => listWeights(caseId),
  })
  const summaryQuery = useQuery({
    queryKey: ['recommendation', caseId, 'weights', 'summary', method],
    queryFn: () => getWeightsSummary(caseId, method),
  })

  useEffect(() => {
    if (!votesQuery.data || !user) return
    const mine: Record<string, number> = {}
    for (const v of votesQuery.data) {
      if (v.member.id === user.id) mine[v.domain_slug] = v.weight
    }
    if (Object.keys(mine).length > 0) setMyWeights(mine)
  }, [votesQuery.data, user])

  const saveMutation = useMutation({
    mutationFn: () => upsertWeights(caseId, myWeights),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['recommendation', caseId, 'weights'] })
      void queryClient.invalidateQueries({
        queryKey: ['recommendation', caseId, 'weights', 'summary'],
      })
      notifications.show({ color: 'teal', message: 'Bobot Anda tersimpan.' })
    },
    onError: () => {
      notifications.show({ color: 'red', message: 'Gagal menyimpan bobot.' })
    },
  })

  if (domainsQuery.isLoading) {
    return (
      <Center py="md">
        <Loader size="sm" />
      </Center>
    )
  }

  const domains = domainsQuery.data ?? []
  const aggregateBySlug = new Map(
    (summaryQuery.data?.aggregates ?? []).map((a) => [a.domain_slug, a]),
  )

  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Title order={4}>Bobot Domain EtD</Title>
        <SegmentedControl
          value={method}
          onChange={(v) => setMethod(v as 'mean' | 'median')}
          size="xs"
          data={[
            { value: 'mean', label: 'Mean' },
            { value: 'median', label: 'Median' },
          ]}
        />
      </Group>

      <Text size="sm" c="dimmed" mb="md">
        Anggota KFT memberi bobot 0–100 untuk setiap domain. Agregat di kolom kanan dipakai oleh
        engine sintesis (sebagai informasi — engine inti tetap memakai 0.40/0.30/0.20/0.10).
      </Text>

      <Table verticalSpacing="xs" striped>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Domain</Table.Th>
            <Table.Th style={{ width: '40%' }}>Bobot Anda (0-100)</Table.Th>
            <Table.Th>Agregat ({method})</Table.Th>
            <Table.Th>Suara</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {domains.map((d) => {
            const agg = aggregateBySlug.get(d.slug)
            return (
              <Table.Tr key={d.slug}>
                <Table.Td>
                  {d.order}. {d.display_name_id}
                </Table.Td>
                <Table.Td>
                  {canVote ? (
                    <Group gap="xs">
                      <Slider
                        min={0}
                        max={100}
                        step={5}
                        value={myWeights[d.slug] ?? 0}
                        onChange={(v) => setMyWeights((prev) => ({ ...prev, [d.slug]: v }))}
                        label={(v) => `${v}`}
                        style={{ flex: 1 }}
                      />
                      <Text size="sm" w={32} ta="right" ff="monospace">
                        {myWeights[d.slug] ?? 0}
                      </Text>
                    </Group>
                  ) : (
                    <Text size="sm" c="dimmed">
                      {caseIsLocked ? 'Terkunci' : 'Tidak ada izin'}
                    </Text>
                  )}
                </Table.Td>
                <Table.Td ff="monospace">
                  {agg?.chosen_weight ?? '—'}
                  {agg?.normalized_weight && (
                    <Text size="xs" c="dimmed">
                      ({(Number(agg.normalized_weight) * 100).toFixed(1)}%)
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>
                  {agg && agg.vote_count > 0 ? (
                    <Badge variant="light" size="sm">
                      {agg.vote_count}
                    </Badge>
                  ) : (
                    '—'
                  )}
                </Table.Td>
              </Table.Tr>
            )
          })}
        </Table.Tbody>
      </Table>

      {canVote && (
        <Group justify="flex-end" mt="md">
          <Button
            leftSection={<IconDeviceFloppy size={16} />}
            onClick={() => saveMutation.mutate()}
            loading={saveMutation.isPending}
          >
            Simpan Bobot Saya
          </Button>
        </Group>
      )}
    </Card>
  )
}
