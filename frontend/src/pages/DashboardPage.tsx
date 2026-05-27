import { Badge, Card, Group, Stack, Text, Title } from '@mantine/core'

import { HealthCheck } from '../components/HealthCheck'
import { useAuth } from '../auth/useAuth'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <Stack gap="md">
      <Title order={2}>Selamat datang{user ? `, ${user.full_name}` : ''}</Title>
      <Text c="dimmed">
        Sistem pendukung keputusan formularium RS. Sprint 1 selesai — autentikasi, peran, dan
        audit log sudah aktif. Modul kasus dan upload Excel menyusul di Sprint 2 dan 3.
      </Text>

      {user && (
        <Card withBorder padding="md" radius="md">
          <Stack gap="xs">
            <Group justify="space-between">
              <Text fw={600}>Profil Anda</Text>
              {user.is_superuser && <Badge color="grape">Superuser</Badge>}
            </Group>
            <Group>
              <Text size="sm" c="dimmed" w={120}>
                Email
              </Text>
              <Text size="sm">{user.email}</Text>
            </Group>
            {user.nip && (
              <Group>
                <Text size="sm" c="dimmed" w={120}>
                  NIP
                </Text>
                <Text size="sm">{user.nip}</Text>
              </Group>
            )}
            {user.institution && (
              <Group>
                <Text size="sm" c="dimmed" w={120}>
                  Institusi
                </Text>
                <Text size="sm">{user.institution}</Text>
              </Group>
            )}
            <Group align="flex-start">
              <Text size="sm" c="dimmed" w={120}>
                Peran
              </Text>
              <Group gap="xs">
                {user.roles.length === 0 ? (
                  <Badge color="gray" variant="light">
                    Belum ditugaskan
                  </Badge>
                ) : (
                  user.roles.map((r) => (
                    <Badge key={r.slug} variant="light">
                      {r.display_name_id}
                    </Badge>
                  ))
                )}
              </Group>
            </Group>
          </Stack>
        </Card>
      )}

      <HealthCheck />
    </Stack>
  )
}
