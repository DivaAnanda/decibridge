import { Link as RouterLink } from 'react-router-dom'
import { Alert, Anchor, Badge, Card, Grid, Group, Stack, Text, Title } from '@mantine/core'
import { IconArrowLeft, IconLock } from '@tabler/icons-react'

import { ArchivePanel } from '../archive/ArchivePanel'
import { IntegrityAlert } from './IntegrityAlert'
import { STATUS_COLOR, STATUS_LABEL_ID, type CaseMetadata } from './types'

interface Props {
  data: CaseMetadata
}

function fmtDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString('id-ID') : 'Belum pernah'
}

/**
 * The case as Admin IT sees it: identity, status, integrity and the archive seal.
 *
 * Round 5 item 5 limits Admin IT to users, the system and backups; the Panduan's
 * least-privilege rule keeps clinical and economic content away from it, so the
 * backend sends no PICO, figures or appraisals for this role.
 */
export function CaseMetadataView({ data }: Props): JSX.Element {
  return (
    <Stack gap="md">
      <Anchor component={RouterLink} to="/cases" size="sm">
        <Group gap={4}>
          <IconArrowLeft size={14} />
          Kembali ke daftar kasus
        </Group>
      </Anchor>

      <IntegrityAlert caseDetail={data} />

      <Card withBorder padding="lg" radius="md">
        <Group justify="space-between" mb="sm">
          <Stack gap={2}>
            <Text size="xs" c="dimmed" ff="monospace">
              {data.case_id}
            </Text>
            <Title order={3}>{data.case_title}</Title>
          </Stack>
          <Badge color={STATUS_COLOR[data.status]} variant="filled" size="lg">
            {STATUS_LABEL_ID[data.status]}
          </Badge>
        </Group>

        <Grid mt="md">
          <Grid.Col span={{ base: 12, sm: 6 }}>
            <Text size="xs" c="dimmed">
              Dibuat oleh
            </Text>
            <Text>{data.created_by.full_name || data.created_by.email}</Text>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6 }}>
            <Text size="xs" c="dimmed">
              Dibuat pada
            </Text>
            <Text>{fmtDateTime(data.created_at)}</Text>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6 }}>
            <Text size="xs" c="dimmed">
              Terakhir diperbarui
            </Text>
            <Text>{fmtDateTime(data.updated_at)}</Text>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6 }}>
            <Text size="xs" c="dimmed">
              Pemeriksaan integritas terakhir
            </Text>
            <Text>{fmtDateTime(data.integrity_checked_at)}</Text>
          </Grid.Col>
        </Grid>
      </Card>

      <Alert color="gray" variant="light" icon={<IconLock size={18} />} title="Tampilan metadata">
        Peran Admin IT mengurus pengguna, sistem, dan cadangan. Isi analisis (PICO, CEA, BIA, PSA,
        EtD, rekomendasi, sign-off, brief, dan versi) hanya dapat dibuka oleh HTA Analyst,
        Sekretaris KFT, Anggota KFT, dan Ketua KFT.
      </Alert>

      <ArchivePanel caseId={data.case_id} caseStatus={data.status} canDownloadManifest={false} />
    </Stack>
  )
}
