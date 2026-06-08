import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Code,
  Grid,
  Group,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import {
  IconArchive,
  IconCalendarStats,
  IconDownload,
  IconShieldLock,
} from '@tabler/icons-react'

import { downloadArchiveManifest, getArchiveRecord } from '../api/archive'

interface Props {
  caseId: string
  caseStatus: string
}

function fmtDateTime(value: string): string {
  return new Date(value).toLocaleString('id-ID', {
    dateStyle: 'long',
    timeStyle: 'short',
  })
}

function fmtDate(value: string): string {
  return new Date(value).toLocaleDateString('id-ID', { dateStyle: 'long' })
}

function fmtRetentionRemaining(retentionUntil: string): string {
  const now = new Date()
  const target = new Date(retentionUntil)
  const ms = target.getTime() - now.getTime()
  if (ms <= 0) return 'Retensi telah berakhir'
  const days = Math.floor(ms / (1000 * 60 * 60 * 24))
  const years = Math.floor(days / 365)
  const remainingDays = days - years * 365
  const months = Math.floor(remainingDays / 30)
  if (years > 0) {
    return `${years} tahun ${months} bulan lagi`
  }
  if (months > 0) {
    return `${months} bulan lagi`
  }
  return `${days} hari lagi`
}

function fmtBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function ArchivePanel({ caseId, caseStatus }: Props): JSX.Element {
  const archiveQuery = useQuery({
    queryKey: ['archive', caseId],
    queryFn: () => getArchiveRecord(caseId),
  })

  const archived = archiveQuery.data

  const handleDownloadManifest = async (): Promise<void> => {
    if (!archived) return
    await downloadArchiveManifest(caseId, `${caseId}_archive_manifest.json`)
  }

  if (archiveQuery.isLoading) {
    return (
      <Card withBorder padding="lg" radius="md">
        <Text size="sm" c="dimmed">
          Memuat status arsip...
        </Text>
      </Card>
    )
  }

  // Not yet archived
  if (!archived) {
    const canArchive = caseStatus === 'locked'
    return (
      <Card withBorder padding="lg" radius="md">
        <Group mb="sm">
          <IconArchive size={24} color="var(--mantine-color-gray-6)" />
          <Title order={5}>Belum Diarsipkan</Title>
        </Group>
        {canArchive ? (
          <Alert color="blue" variant="light">
            Kasus telah dikunci dan siap diarsipkan. Ketua KFT atau Admin IT
            dapat menjalankan aksi <Code>Arsipkan</Code> melalui menu Tindakan
            di kanan atas. Pengarsipan akan membuat manifest SHA-256 dari
            seluruh artefak kasus dengan retensi 7 tahun.
          </Alert>
        ) : (
          <Text size="sm" c="dimmed">
            Pengarsipan hanya tersedia untuk kasus yang sudah dikunci.
            Status kasus saat ini: <Code>{caseStatus}</Code>.
          </Text>
        )}
      </Card>
    )
  }

  // Archived
  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="md">
        <Group>
          <IconShieldLock size={28} color="var(--mantine-color-blue-7)" />
          <Stack gap={2}>
            <Title order={4}>Arsip Permanen</Title>
            <Text size="xs" c="dimmed">
              Kasus terkunci dan tersegel. Manifest SHA-256 mencegah perubahan
              tersembunyi pada data historis.
            </Text>
          </Stack>
        </Group>
        <Badge size="xl" color="blue" variant="filled">
          TERARSIPKAN
        </Badge>
      </Group>

      <Grid mt="md" gutter="md">
        <Grid.Col span={6}>
          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Diarsipkan pada
            </Text>
            <Text fw={500}>{fmtDateTime(archived.archived_at)}</Text>
          </Stack>
        </Grid.Col>
        <Grid.Col span={6}>
          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Oleh
            </Text>
            <Text fw={500}>{archived.archived_by_name}</Text>
            <Text size="xs" c="dimmed">
              {archived.archived_by_email}
            </Text>
          </Stack>
        </Grid.Col>
        <Grid.Col span={6}>
          <Stack gap={4}>
            <Group gap={4}>
              <IconCalendarStats size={14} />
              <Text size="xs" c="dimmed">
                Retensi berakhir
              </Text>
            </Group>
            <Text fw={500}>{fmtDate(archived.retention_until)}</Text>
            <Badge color="teal" variant="light" size="sm">
              {fmtRetentionRemaining(archived.retention_until)}
            </Badge>
          </Stack>
        </Grid.Col>
        <Grid.Col span={6}>
          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Ukuran manifest
            </Text>
            <Text fw={500}>{fmtBytes(archived.manifest_size_bytes)}</Text>
          </Stack>
        </Grid.Col>
        <Grid.Col span={12}>
          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              SHA-256 Manifest (segel anti-tampering)
            </Text>
            <Code block fz="xs">
              {archived.manifest_sha256}
            </Code>
          </Stack>
        </Grid.Col>
      </Grid>

      <Card.Section withBorder mt="md" pt="md" px="md" pb="md">
        <Title order={6} mb="xs">
          Inventaris Artefak
        </Title>
        <Grid gutter={6}>
          {Object.entries(archived.artifact_counts).map(([key, count]) => (
            <Grid.Col key={key} span={4}>
              <Group gap={4}>
                <Badge variant="light" size="sm">
                  {count}
                </Badge>
                <Text size="xs" c="dimmed">
                  {key.replace(/_/g, ' ')}
                </Text>
              </Group>
            </Grid.Col>
          ))}
        </Grid>
      </Card.Section>

      <Group justify="flex-end" mt="md">
        <Button
          leftSection={<IconDownload size={16} />}
          variant="default"
          onClick={() => void handleDownloadManifest()}
        >
          Unduh Manifest JSON
        </Button>
      </Group>
    </Card>
  )
}
