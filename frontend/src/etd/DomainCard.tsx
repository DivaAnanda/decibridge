import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Badge,
  Box,
  Button,
  Card,
  Divider,
  Grid,
  Group,
  MultiSelect,
  Radio,
  Select,
  Stack,
  Text,
  Textarea,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconDeviceFloppy } from '@tabler/icons-react'

import { upsertAppraisal } from '../api/etd'
import { useAuth } from '../auth/useAuth'
import {
  CERTAINTY_COLOR,
  CERTAINTY_OPTIONS,
  JUDGEMENT_OPTIONS,
  type Certainty,
  type DomainAggregate,
  type EtDAppraisal,
  type EtDDomain,
  type Judgement,
  type ReferenceCitation,
} from './types'

interface Props {
  caseId: string
  caseIsLocked: boolean
  domain: EtDDomain
  references: ReferenceCitation[]
  allAppraisals: EtDAppraisal[]
  domainAggregate: DomainAggregate | undefined
}

export function DomainCard({
  caseId,
  caseIsLocked,
  domain,
  references,
  allAppraisals,
  domainAggregate,
}: Props): JSX.Element {
  const { user, hasRole } = useAuth()
  const canVote = !caseIsLocked && user !== null && hasRole('kft_member', 'ketua_kft')
  const queryClient = useQueryClient()

  const myAppraisal = allAppraisals.find(
    (a) => a.domain_slug === domain.slug && a.member.id === user?.id,
  )
  const otherAppraisals = allAppraisals.filter(
    (a) => a.domain_slug === domain.slug && a.member.id !== user?.id,
  )

  const [judgement, setJudgement] = useState<Judgement>(myAppraisal?.judgement ?? 50)
  const [certainty, setCertainty] = useState<Certainty>(myAppraisal?.certainty ?? 'moderate')
  const [narrative, setNarrative] = useState(myAppraisal?.narrative ?? '')
  const [refIds, setRefIds] = useState<string[]>(
    myAppraisal?.references.map((r) => String(r.id)) ?? [],
  )

  useEffect(() => {
    if (myAppraisal) {
      setJudgement(myAppraisal.judgement)
      setCertainty(myAppraisal.certainty)
      setNarrative(myAppraisal.narrative)
      setRefIds(myAppraisal.references.map((r) => String(r.id)))
    }
  }, [myAppraisal])

  const saveMutation = useMutation({
    mutationFn: () =>
      upsertAppraisal(caseId, {
        domain_slug: domain.slug,
        judgement,
        certainty,
        narrative,
        reference_ids: refIds.map((s) => Number(s)),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['etd', caseId, 'appraisals'] })
      void queryClient.invalidateQueries({ queryKey: ['etd', caseId, 'summary'] })
      notifications.show({ color: 'teal', message: `Penilaian Anda untuk domain "${domain.display_name_id}" disimpan.` })
    },
    onError: () => {
      notifications.show({ color: 'red', message: 'Gagal menyimpan penilaian.' })
    },
  })

  const refOptions = references.map((r) => ({
    value: String(r.id),
    label: r.citation_text.slice(0, 80),
  }))

  return (
    <Card withBorder padding="lg" radius="md">
      <Stack gap="md">
        <Box>
          <Group justify="space-between">
            <Title order={4}>
              {domain.order}. {domain.display_name_id}
            </Title>
            {domainAggregate && domainAggregate.appraisal_count > 0 && (
              <Badge variant="light" size="lg">
                Skor: {domainAggregate.combined_domain_score ?? '—'} · {domainAggregate.appraisal_count} suara
              </Badge>
            )}
          </Group>
          {domain.description && (
            <Text size="sm" c="dimmed" mt={4}>
              {domain.description}
            </Text>
          )}
          {domain.prompt_text_id && (
            <Card withBorder padding="sm" radius="sm" mt="sm" bg="blue.0">
              <Text size="sm" fs="italic">
                {domain.prompt_text_id}
              </Text>
            </Card>
          )}
        </Box>

        {!canVote && (
          <Text size="xs" c="dimmed">
            {caseIsLocked
              ? 'Kasus terkunci — penilaian read-only.'
              : 'Hanya Anggota KFT atau Ketua KFT yang dapat memberikan penilaian.'}
          </Text>
        )}

        {canVote && (
          <fieldset disabled={!canVote} style={{ border: 'none', padding: 0, margin: 0 }}>
            <Stack gap="md">
              <Radio.Group
                label="Penilaian Anda"
                value={String(judgement)}
                onChange={(v) => setJudgement(Number(v) as Judgement)}
              >
                <Group gap="md" mt="xs">
                  {JUDGEMENT_OPTIONS.map((opt) => (
                    <Radio key={opt.value} value={String(opt.value)} label={opt.label} />
                  ))}
                </Group>
              </Radio.Group>

              <Grid>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <Select
                    label="Kepastian bukti (GRADE)"
                    data={CERTAINTY_OPTIONS}
                    value={certainty}
                    onChange={(v) => setCertainty((v ?? 'moderate') as Certainty)}
                    allowDeselect={false}
                  />
                </Grid.Col>
                <Grid.Col span={{ base: 12, sm: 6 }}>
                  <MultiSelect
                    label="Referensi pendukung"
                    placeholder={refOptions.length === 0 ? 'Belum ada referensi' : 'Pilih...'}
                    data={refOptions}
                    value={refIds}
                    onChange={setRefIds}
                    searchable
                    disabled={refOptions.length === 0}
                  />
                </Grid.Col>
              </Grid>

              <Textarea
                label="Pertimbangan (narasi)"
                placeholder="Penjelasan singkat alasan penilaian Anda..."
                autosize
                minRows={2}
                value={narrative}
                onChange={(e) => setNarrative(e.currentTarget.value)}
              />

              <Group justify="flex-end">
                <Button
                  leftSection={<IconDeviceFloppy size={16} />}
                  loading={saveMutation.isPending}
                  onClick={() => saveMutation.mutate()}
                >
                  Simpan Penilaian Saya
                </Button>
              </Group>
            </Stack>
          </fieldset>
        )}

        {otherAppraisals.length > 0 && (
          <>
            <Divider label="Penilaian anggota lain" labelPosition="left" />
            <Stack gap="xs">
              {otherAppraisals.map((a) => (
                <Card key={a.id} withBorder padding="sm" radius="sm">
                  <Group justify="space-between">
                    <Text size="sm" fw={500}>
                      {a.member.full_name}
                    </Text>
                    <Group gap="xs">
                      <Badge variant="light">{a.judgement_label}</Badge>
                      <Badge variant="light" color={CERTAINTY_COLOR[a.certainty]}>
                        {a.certainty_label}
                      </Badge>
                    </Group>
                  </Group>
                  {a.narrative && (
                    <Text size="sm" c="dimmed" mt={4}>
                      {a.narrative}
                    </Text>
                  )}
                </Card>
              ))}
            </Stack>
          </>
        )}
      </Stack>
    </Card>
  )
}
