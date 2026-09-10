import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  MultiSelect,
  Stack,
  Switch,
  Table,
  Tabs,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconHistory, IconKey, IconSearch, IconUsers } from '@tabler/icons-react'

import { forcePasswordReset, listLoginHistory, listUsers, updateUser } from '../api/admin'
import { useAuth } from '../auth/useAuth'
import { ROLE_OPTIONS, type AdminUser, type RoleSlug } from '../admin/types'

function errorMessage(err: unknown): string {
  const data = (err as { response?: { data?: Record<string, unknown> } }).response?.data
  if (!data) return 'Terjadi kesalahan.'
  const first = Object.values(data)[0]
  if (Array.isArray(first)) return String(first[0])
  return String(first ?? 'Terjadi kesalahan.')
}

function UserRow({ user, isSelf }: { user: AdminUser; isSelf: boolean }): JSX.Element {
  const queryClient = useQueryClient()
  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })

  const update = useMutation({
    mutationFn: (payload: Parameters<typeof updateUser>[1]) => updateUser(user.id, payload),
    onSuccess: () => {
      invalidate()
      notifications.show({ color: 'teal', message: `Akun ${user.email} diperbarui.` })
    },
    onError: (err) =>
      notifications.show({ color: 'red', title: 'Gagal', message: errorMessage(err) }),
  })

  const reset = useMutation({
    mutationFn: () => forcePasswordReset(user.id),
    onSuccess: () => {
      invalidate()
      notifications.show({
        color: 'teal',
        message: `${user.email} wajib mengganti kata sandi saat masuk berikutnya.`,
      })
    },
    onError: (err) => notifications.show({ color: 'orange', message: errorMessage(err) }),
  })

  return (
    <Table.Tr>
      <Table.Td>
        <Stack gap={0}>
          <Text size="sm" fw={500}>
            {user.full_name}
            {isSelf && (
              <Badge ml="xs" size="xs" variant="light">
                Anda
              </Badge>
            )}
          </Text>
          <Text size="xs" c="dimmed">
            {user.email}
          </Text>
        </Stack>
      </Table.Td>
      <Table.Td style={{ minWidth: 260 }}>
        <MultiSelect
          data={ROLE_OPTIONS}
          value={user.roles}
          onChange={(roles) => update.mutate({ roles: roles as RoleSlug[] })}
          disabled={update.isPending}
          size="xs"
          searchable
          comboboxProps={{ withinPortal: true }}
        />
      </Table.Td>
      <Table.Td>
        <Switch
          checked={user.is_active}
          onChange={(e) => update.mutate({ is_active: e.currentTarget.checked })}
          disabled={update.isPending || isSelf}
          label={user.is_active ? 'Aktif' : 'Nonaktif'}
          size="sm"
        />
      </Table.Td>
      <Table.Td>
        <Stack gap={2}>
          <Text size="xs">
            {user.last_login
              ? new Date(user.last_login).toLocaleString('id-ID')
              : 'Belum pernah masuk'}
          </Text>
          {user.last_login_ip && (
            <Text size="xs" c="dimmed" ff="monospace">
              {user.last_login_ip}
            </Text>
          )}
        </Stack>
      </Table.Td>
      <Table.Td>
        {user.must_change_password ? (
          <Badge color="orange" variant="light" size="sm">
            Wajib ganti sandi
          </Badge>
        ) : (
          <Button
            size="xs"
            variant="light"
            leftSection={<IconKey size={14} />}
            loading={reset.isPending}
            onClick={() => reset.mutate()}
          >
            Paksa ganti sandi
          </Button>
        )}
      </Table.Td>
    </Table.Tr>
  )
}

function UsersTab(): JSX.Element {
  const { user } = useAuth()
  const [search, setSearch] = useState('')

  const usersQuery = useQuery({
    queryKey: ['admin', 'users', search],
    queryFn: () => listUsers(search ? { search } : undefined),
  })

  return (
    <Stack gap="md">
      <Alert color="blue" variant="light">
        Admin IT hanya mengelola akun dan peran. Peran ini tidak dapat menilai EtD,
        menghitung rekomendasi, menandatangani, atau mengunci keputusan. Kata sandi tidak
        pernah ditetapkan oleh administrator: gunakan "Paksa ganti sandi" agar pengguna
        menetapkannya sendiri saat masuk berikutnya.
      </Alert>

      <TextInput
        placeholder="Cari nama atau email..."
        leftSection={<IconSearch size={16} />}
        value={search}
        onChange={(e) => setSearch(e.currentTarget.value)}
        w={320}
      />

      {usersQuery.isLoading ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : (
        <Table.ScrollContainer minWidth={900}>
          <Table striped withTableBorder verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Pengguna</Table.Th>
                <Table.Th>Peran</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Masuk terakhir</Table.Th>
                <Table.Th>Kata sandi</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(usersQuery.data ?? []).map((u) => (
                <UserRow key={u.id} user={u} isSelf={u.id === user?.id} />
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}
    </Stack>
  )
}

function LoginHistoryTab(): JSX.Element {
  const [onlyFailed, setOnlyFailed] = useState(false)

  const historyQuery = useQuery({
    queryKey: ['admin', 'login-history', onlyFailed],
    queryFn: () => listLoginHistory(onlyFailed ? { only_failed: 'true' } : undefined),
  })

  const entries = historyQuery.data ?? []

  return (
    <Stack gap="md">
      <Group>
        <Switch
          checked={onlyFailed}
          onChange={(e) => setOnlyFailed(e.currentTarget.checked)}
          label="Hanya kegagalan masuk"
        />
      </Group>

      {historyQuery.isLoading ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : entries.length === 0 ? (
        <Alert color="gray" variant="light">
          Belum ada aktivitas masuk yang tercatat.
        </Alert>
      ) : (
        <Table.ScrollContainer minWidth={720}>
          <Table striped withTableBorder verticalSpacing="xs">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Waktu</Table.Th>
                <Table.Th>Peristiwa</Table.Th>
                <Table.Th>Akun</Table.Th>
                <Table.Th>IP</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {entries.map((e) => (
                <Table.Tr key={e.id}>
                  <Table.Td>{new Date(e.created_at).toLocaleString('id-ID')}</Table.Td>
                  <Table.Td>
                    <Badge
                      size="sm"
                      variant="light"
                      color={e.action === 'login_failed' ? 'red' : 'teal'}
                    >
                      {e.action_label}
                    </Badge>
                  </Table.Td>
                  <Table.Td>{e.actor_email || e.actor_name}</Table.Td>
                  <Table.Td ff="monospace">{e.ip_address ?? 'tidak tercatat'}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}
    </Stack>
  )
}

export function AdminUsersPage(): JSX.Element {
  const { hasRole } = useAuth()

  if (!hasRole('admin_it')) {
    return (
      <Alert color="red" variant="light" title="Tidak memiliki izin">
        Halaman ini hanya untuk Admin IT.
      </Alert>
    )
  }

  return (
    <Stack gap="md">
      <Stack gap={2}>
        <Title order={3}>Administrasi Pengguna</Title>
        <Text size="sm" c="dimmed">
          Kelola akun, peran, dan pantau aktivitas masuk.
        </Text>
      </Stack>

      <Card withBorder padding="lg" radius="md">
        <Tabs defaultValue="users" keepMounted={false}>
          <Tabs.List mb="md">
            <Tabs.Tab value="users" leftSection={<IconUsers size={14} />}>
              Pengguna &amp; Peran
            </Tabs.Tab>
            <Tabs.Tab value="history" leftSection={<IconHistory size={14} />}>
              Riwayat Masuk
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="users">
            <UsersTab />
          </Tabs.Panel>
          <Tabs.Panel value="history">
            <LoginHistoryTab />
          </Tabs.Panel>
        </Tabs>
      </Card>
    </Stack>
  )
}
