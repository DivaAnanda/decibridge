import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Card,
  Code,
  Drawer,
  Group,
  Loader,
  Modal,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  Title,
} from '@mantine/core'
import { IconHistory, IconScale, IconTimeline } from '@tabler/icons-react'

import {
  getVersionDiff,
  getVersionState,
  getVersionTimeline,
  listVersions,
} from '../api/versioning'
import { ArchivePanel } from '../archive/ArchivePanel'
import {
  STATUS_COLOR,
  TRIGGER_COLOR,
  type CaseVersionRow,
} from './types'

interface Props {
  caseId: string
  caseStatus: string
}

function fmtDateTime(value: string | null): string {
  if (!value) return '—'
  return new Date(value).toLocaleString('id-ID')
}

function fmtVal(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string' || typeof value === 'number') return String(value)
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  return JSON.stringify(value)
}

export function VersioningTab({ caseId, caseStatus }: Props): JSX.Element {
  const [selectedVersion, setSelectedVersion] = useState<CaseVersionRow | null>(null)
  const [diffFromId, setDiffFromId] = useState<string | null>(null)
  const [diffToId, setDiffToId] = useState<string | null>(null)
  const [diffOpen, setDiffOpen] = useState(false)

  const versionsQuery = useQuery({
    queryKey: ['versions', caseId],
    queryFn: () => listVersions(caseId),
  })

  const versions = versionsQuery.data ?? []

  const versionOptions = useMemo(
    () =>
      versions.map((v) => ({
        value: String(v.id),
        label: `v${v.version_number} · ${v.trigger_label}`,
      })),
    [versions],
  )

  const canDiff = diffFromId !== null && diffToId !== null && diffFromId !== diffToId

  return (
    <Stack gap="lg">
      <ArchivePanel caseId={caseId} caseStatus={caseStatus} />

      <Card withBorder padding="lg" radius="md">
        <Stack gap={4} mb="md">
          <Title order={4}>Riwayat Versi</Title>
          <Text size="xs" c="dimmed">
            Setiap penguncian keputusan oleh Ketua KFT menghasilkan satu baris
            versi baru. Data versi bersifat append-only dan tidak dapat diubah
            atau dihapus. Klik baris untuk melihat timeline audit dan keadaan
            data pada saat itu.
          </Text>
        </Stack>

        {versionsQuery.isLoading && (
          <Group justify="center" py="md">
            <Loader size="sm" />
          </Group>
        )}

        {!versionsQuery.isLoading && versions.length === 0 && (
          <Alert color="gray" variant="light">
            Belum ada versi. Versi pertama akan dibuat otomatis saat kasus
            dikunci oleh Ketua KFT.
          </Alert>
        )}

        {versions.length > 0 && (
          <Table verticalSpacing="sm" striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Versi</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Pemicu</Table.Th>
                <Table.Th>Waktu</Table.Th>
                <Table.Th>Oleh</Table.Th>
                <Table.Th>Alasan</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {versions.map((v) => (
                <Table.Tr
                  key={v.id}
                  onClick={() => setSelectedVersion(v)}
                  style={{ cursor: 'pointer' }}
                >
                  <Table.Td ff="monospace" fw={600}>
                    v{v.version_number}
                  </Table.Td>
                  <Table.Td>
                    <Badge color={STATUS_COLOR[v.status]} variant="light" size="sm">
                      {v.status_label}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={TRIGGER_COLOR[v.trigger]} variant="filled" size="sm">
                      {v.trigger_label}
                    </Badge>
                  </Table.Td>
                  <Table.Td>{fmtDateTime(v.locked_at ?? v.created_at)}</Table.Td>
                  <Table.Td>
                    <Stack gap={0}>
                      <Text size="sm">
                        {v.locked_by_name ?? v.created_by_name}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {v.locked_by_email}
                      </Text>
                    </Stack>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c={v.lock_reason ? undefined : 'dimmed'}>
                      {v.lock_reason || '—'}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Card>

      {versions.length >= 2 && (
        <Card withBorder padding="lg" radius="md">
          <Group justify="space-between" mb="sm">
            <Stack gap={2}>
              <Title order={5}>Bandingkan Versi</Title>
              <Text size="xs" c="dimmed">
                Pilih dua versi untuk melihat perbedaan nilai inti (skor, ICER,
                rekomendasi, dampak anggaran).
              </Text>
            </Stack>
          </Group>
          <Group>
            <Select
              label="Dari versi"
              placeholder="Pilih versi"
              data={versionOptions}
              value={diffFromId}
              onChange={setDiffFromId}
              w={240}
            />
            <Select
              label="Ke versi"
              placeholder="Pilih versi"
              data={versionOptions}
              value={diffToId}
              onChange={setDiffToId}
              w={240}
            />
            {canDiff && (
              <Badge
                color="blue"
                variant="filled"
                style={{ cursor: 'pointer', alignSelf: 'flex-end' }}
                onClick={() => setDiffOpen(true)}
              >
                Tampilkan Diff
              </Badge>
            )}
          </Group>
        </Card>
      )}

      <VersionDetailDrawer
        caseId={caseId}
        version={selectedVersion}
        onClose={() => setSelectedVersion(null)}
      />

      {canDiff && (
        <VersionDiffModal
          caseId={caseId}
          opened={diffOpen}
          fromId={Number(diffFromId)}
          toId={Number(diffToId)}
          onClose={() => setDiffOpen(false)}
        />
      )}
    </Stack>
  )
}

// ---------------------------------------------------------------------------
// Detail drawer — timeline + state for one version
// ---------------------------------------------------------------------------

interface DrawerProps {
  caseId: string
  version: CaseVersionRow | null
  onClose: () => void
}

function VersionDetailDrawer({ caseId, version, onClose }: DrawerProps): JSX.Element {
  const open = version !== null

  const timelineQuery = useQuery({
    queryKey: ['version-timeline', caseId, version?.id],
    queryFn: () => getVersionTimeline(caseId, version!.id),
    enabled: open,
  })

  const stateQuery = useQuery({
    queryKey: ['version-state', caseId, version?.id],
    queryFn: () => getVersionState(caseId, version!.id),
    enabled: open,
  })

  return (
    <Drawer
      opened={open}
      onClose={onClose}
      position="right"
      size="xl"
      title={
        version ? (
          <Stack gap={2}>
            <Title order={4}>Versi v{version.version_number}</Title>
            <Text size="xs" c="dimmed">
              {version.trigger_label} · {fmtDateTime(version.locked_at ?? version.created_at)}
            </Text>
          </Stack>
        ) : null
      }
    >
      {version && (
        <Tabs defaultValue="timeline" keepMounted={false}>
          <Tabs.List>
            <Tabs.Tab value="timeline" leftSection={<IconTimeline size={14} />}>
              Timeline Audit
            </Tabs.Tab>
            <Tabs.Tab value="state" leftSection={<IconHistory size={14} />}>
              Keadaan Data
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="timeline" pt="md">
            {timelineQuery.isLoading && <Loader size="sm" />}
            {timelineQuery.data && timelineQuery.data.length === 0 && (
              <Text size="sm" c="dimmed">
                Tidak ada entri audit untuk rentang waktu versi ini.
              </Text>
            )}
            {timelineQuery.data && timelineQuery.data.length > 0 && (
              <Stack gap="xs">
                {timelineQuery.data.map((entry) => (
                  <Card key={entry.id} withBorder padding="sm" radius="sm">
                    <Group justify="space-between">
                      <Badge variant="light" size="sm">
                        {entry.action_label}
                      </Badge>
                      <Text size="xs" c="dimmed">
                        {fmtDateTime(entry.created_at)}
                      </Text>
                    </Group>
                    <Text size="sm" mt={4}>
                      <strong>{entry.actor_name}</strong>{' '}
                      <Text component="span" size="xs" c="dimmed">
                        ({entry.actor_email})
                      </Text>
                    </Text>
                    {entry.target_label && (
                      <Text size="xs" c="dimmed">
                        Target: {entry.target_label}
                      </Text>
                    )}
                    {entry.diff && (
                      <Code block fz="xs" mt={4}>
                        {JSON.stringify(entry.diff, null, 2)}
                      </Code>
                    )}
                    {entry.ip_address && (
                      <Text size="xs" c="dimmed" ff="monospace" mt={2}>
                        IP: {entry.ip_address}
                      </Text>
                    )}
                  </Card>
                ))}
              </Stack>
            )}
          </Tabs.Panel>

          <Tabs.Panel value="state" pt="md">
            {stateQuery.isLoading && <Loader size="sm" />}
            {stateQuery.data && (
              <Stack gap="md">
                <StateBlock title="Rekomendasi" data={stateQuery.data.recommendation} />
                <StateBlock title="CEA" data={stateQuery.data.cea} />
                <StateBlock title="BIA" data={stateQuery.data.bia} />
                <StateBlock title="Tanda Tangan" data={stateQuery.data.approval} />
                <StateBlock title="Policy Brief" data={stateQuery.data.policy_brief} />
              </Stack>
            )}
          </Tabs.Panel>
        </Tabs>
      )}
    </Drawer>
  )
}

interface StateBlockProps {
  title: string
  data: Record<string, unknown> | null
}

function StateBlock({ title, data }: StateBlockProps): JSX.Element {
  return (
    <Card withBorder padding="sm" radius="sm">
      <Title order={6}>{title}</Title>
      {!data && (
        <Text size="xs" c="dimmed">
          Tidak ada data untuk versi ini.
        </Text>
      )}
      {data && (
        <Table verticalSpacing="xs">
          <Table.Tbody>
            {Object.entries(data).map(([k, v]) => (
              <Table.Tr key={k}>
                <Table.Td>
                  <Text size="xs" c="dimmed" ff="monospace">
                    {k}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text size="xs">{fmtVal(v)}</Text>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Diff modal
// ---------------------------------------------------------------------------

interface DiffModalProps {
  caseId: string
  opened: boolean
  fromId: number
  toId: number
  onClose: () => void
}

function VersionDiffModal({ caseId, opened, fromId, toId, onClose }: DiffModalProps): JSX.Element {
  const diffQuery = useQuery({
    queryKey: ['version-diff', caseId, fromId, toId],
    queryFn: () => getVersionDiff(caseId, fromId, toId),
    enabled: opened,
  })

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Perbandingan Versi"
      size="xl"
      centered
    >
      {diffQuery.isLoading && <Loader size="sm" />}
      {diffQuery.data && (
        <Stack gap="md">
          <Group>
            <Badge color="gray" variant="light" size="lg">
              v{diffQuery.data.from_version}
            </Badge>
            <IconScale size={16} />
            <Badge color="blue" variant="filled" size="lg">
              v{diffQuery.data.to_version}
            </Badge>
          </Group>

          {Object.keys(diffQuery.data.diff).length === 0 && (
            <Alert color="green" variant="light">
              Tidak ada perbedaan terdeteksi antara kedua versi.
            </Alert>
          )}

          {Object.entries(diffQuery.data.diff).map(([block, changes]) => (
            <Card key={block} withBorder padding="sm" radius="sm">
              <Title order={6} tt="capitalize">
                {block.replace('_', ' ')}
              </Title>
              <Table verticalSpacing="xs">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Field</Table.Th>
                    <Table.Th>Dari</Table.Th>
                    <Table.Th>Ke</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {Object.entries(changes).map(([field, change]) => (
                    <Table.Tr key={field}>
                      <Table.Td ff="monospace" fz="xs">
                        {field}
                      </Table.Td>
                      <Table.Td>
                        <Code fz="xs">{fmtVal(change.from)}</Code>
                      </Table.Td>
                      <Table.Td>
                        <Code fz="xs" c="blue">
                          {fmtVal(change.to)}
                        </Code>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Card>
          ))}
        </Stack>
      )}
    </Modal>
  )
}
