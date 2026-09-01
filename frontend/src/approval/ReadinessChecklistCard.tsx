import { useQuery } from '@tanstack/react-query'
import { Alert, Badge, Card, Group, Loader, Stack, Text, Title } from '@mantine/core'
import { IconCheck, IconX } from '@tabler/icons-react'

import { getCaseReadiness } from '../api/cases'

interface Props {
  caseId: string
}

/**
 * Makes the approve/lock gate explicit in the UI.
 *
 * The lecturer asked that if all 9 EtD domains are mandatory the system must
 * block sign-off until they are complete — and that whichever rule we chose be
 * stated visibly rather than only appearing as a rejection.
 */
export function ReadinessChecklistCard({ caseId }: Props): JSX.Element {
  const { data, isLoading } = useQuery({
    queryKey: ['case', caseId, 'readiness'],
    queryFn: () => getCaseReadiness(caseId),
  })

  if (isLoading || !data) {
    return (
      <Card withBorder padding="lg" radius="md">
        <Loader size="sm" />
      </Card>
    )
  }

  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="xs">
        <Title order={4}>Kelengkapan Dossier</Title>
        <Badge color={data.is_ready ? 'teal' : 'orange'} size="lg" variant="filled">
          {data.is_ready ? 'SIAP SIGN-OFF' : 'BELUM LENGKAP'}
        </Badge>
      </Group>
      <Text size="xs" c="dimmed" mb="md">
        Persetujuan dan penguncian keputusan hanya dapat dilakukan bila seluruh komponen wajib
        di bawah sudah terpenuhi. Seluruh 9 domain EtD bersifat wajib.
      </Text>

      <Stack gap="xs">
        {data.requirements.map((r) => (
          <Group key={r.key} justify="space-between" wrap="nowrap">
            <Group gap={8} wrap="nowrap">
              {r.satisfied ? (
                <IconCheck size={16} color="var(--mantine-color-teal-6)" />
              ) : (
                <IconX size={16} color="var(--mantine-color-red-6)" />
              )}
              <Text size="sm">
                {r.label}
                {!r.mandatory && (
                  <Text span size="xs" c="dimmed">
                    {' '}
                    (tidak wajib)
                  </Text>
                )}
              </Text>
            </Group>
            <Text size="xs" c="dimmed" ta="right" style={{ whiteSpace: 'nowrap' }}>
              {r.detail}
            </Text>
          </Group>
        ))}
      </Stack>

      {!data.is_ready && (
        <Alert color="orange" variant="light" mt="md">
          Belum dapat disetujui/dikunci. Lengkapi: {data.missing.join('; ')}.
        </Alert>
      )}
    </Card>
  )
}
