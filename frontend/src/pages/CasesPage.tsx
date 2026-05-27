import { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { IconPlus, IconSearch } from '@tabler/icons-react'

import { listCases } from '../api/cases'
import { useAuth } from '../auth/useAuth'
import {
  STATUS_COLOR,
  STATUS_LABEL_ID,
  type CaseStatus,
} from '../cases/types'

const STATUS_OPTIONS: { value: CaseStatus | ''; label: string }[] = [
  { value: '', label: 'Semua status' },
  { value: 'draft', label: 'Draft' },
  { value: 'in_review', label: 'Dalam tinjauan' },
  { value: 'approved', label: 'Disetujui' },
  { value: 'locked', label: 'Terkunci' },
  { value: 'archived', label: 'Diarsipkan' },
]

export function CasesPage() {
  const { hasRole } = useAuth()
  const canCreate = hasRole('hta_analyst', 'farmasi_sekretaris')

  const [status, setStatus] = useState<CaseStatus | ''>('')
  const [search, setSearch] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['cases', status, search],
    queryFn: () =>
      listCases({
        ...(status ? { status } : {}),
        ...(search ? { search } : {}),
      }),
  })

  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-end">
        <Stack gap={4}>
          <Title order={2}>Daftar Kasus</Title>
          <Text c="dimmed" size="sm">
            Semua kasus keputusan formularium yang sedang berjalan
          </Text>
        </Stack>
        {canCreate && (
          <Button component={RouterLink} to="/cases/new" leftSection={<IconPlus size={16} />}>
            Buat Kasus
          </Button>
        )}
      </Group>

      <Card withBorder padding="md" radius="md">
        <Group>
          <TextInput
            placeholder="Cari berdasarkan ID, judul, intervensi..."
            leftSection={<IconSearch size={14} />}
            value={search}
            onChange={(e) => setSearch(e.currentTarget.value)}
            style={{ flex: 1 }}
          />
          <Select
            data={STATUS_OPTIONS}
            value={status}
            onChange={(v) => setStatus((v ?? '') as CaseStatus | '')}
            allowDeselect={false}
            w={200}
          />
        </Group>
      </Card>

      {isLoading && (
        <Center py="xl">
          <Loader />
        </Center>
      )}

      {isError && (
        <Card withBorder padding="md" radius="md">
          <Text c="red">Gagal memuat daftar kasus. Periksa koneksi backend.</Text>
        </Card>
      )}

      {data && data.count === 0 && (
        <Card withBorder padding="xl" radius="md">
          <Stack align="center" gap="xs">
            <Text fw={500}>Belum ada kasus</Text>
            <Text c="dimmed" size="sm">
              {canCreate
                ? 'Mulai dengan menekan tombol "Buat Kasus" di kanan atas.'
                : 'Hubungi Sekretaris KFT atau HTA Analyst untuk membuat kasus baru.'}
            </Text>
          </Stack>
        </Card>
      )}

      {data && data.count > 0 && (
        <Card withBorder padding={0} radius="md">
          <Table verticalSpacing="sm" horizontalSpacing="md" striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>ID Kasus</Table.Th>
                <Table.Th>Judul</Table.Th>
                <Table.Th>Intervensi</Table.Th>
                <Table.Th>Komparator</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Dibuat oleh</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.results.map((c) => (
                <Table.Tr key={c.id}>
                  <Table.Td>
                    <Anchor component={RouterLink} to={`/cases/${c.case_id}`} ff="monospace">
                      {c.case_id}
                    </Anchor>
                  </Table.Td>
                  <Table.Td>{c.case_title}</Table.Td>
                  <Table.Td>{c.technology}</Table.Td>
                  <Table.Td>{c.comparator}</Table.Td>
                  <Table.Td>
                    <Badge color={STATUS_COLOR[c.status]} variant="light">
                      {STATUS_LABEL_ID[c.status]}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">
                      {c.created_by_email}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      )}
    </Stack>
  )
}
