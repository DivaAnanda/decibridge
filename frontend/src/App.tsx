import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import {
  AppShell,
  Burger,
  Group,
  Title,
  Text,
  Stack,
  Anchor,
  Badge,
  Menu,
  Avatar,
  UnstyledButton,
  NavLink,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconLogout, IconUser, IconHome, IconFolders } from '@tabler/icons-react'

import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { CasesPage } from './pages/CasesPage'
import { CaseDetailPage } from './pages/CaseDetailPage'
import { CaseCreatePage } from './pages/CaseCreatePage'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { useAuth } from './auth/useAuth'

function NotFoundPage() {
  return (
    <Stack gap="md">
      <Title order={3}>404 — Halaman tidak ditemukan</Title>
      <Anchor component={Link} to="/">
        Kembali ke beranda
      </Anchor>
    </Stack>
  )
}

function UserMenu() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  const initial = (user.full_name || user.email).slice(0, 1).toUpperCase()

  return (
    <Menu position="bottom-end" withinPortal shadow="md">
      <Menu.Target>
        <UnstyledButton>
          <Group gap="xs">
            <Avatar radius="xl" size={32} color="blue">
              {initial}
            </Avatar>
            <Text size="sm" visibleFrom="sm">
              {user.full_name || user.email}
            </Text>
          </Group>
        </UnstyledButton>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>{user.email}</Menu.Label>
        <Menu.Item leftSection={<IconUser size={14} />} disabled>
          Profil (segera)
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item
          color="red"
          leftSection={<IconLogout size={14} />}
          onClick={async () => {
            await logout()
            navigate('/login', { replace: true })
          }}
        >
          Keluar
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}

function AppLayout({ children }: { children: React.ReactNode }) {
  const [opened, { toggle, close }] = useDisclosure()

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 240, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Title order={4}>DeciBridge</Title>
          </Group>
          <Group>
            <Badge variant="light">v0.2.0</Badge>
            <UserMenu />
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Stack gap={4}>
          <NavLink
            component={Link}
            to="/"
            label="Beranda"
            leftSection={<IconHome size={16} />}
            onClick={close}
          />
          <NavLink
            component={Link}
            to="/cases"
            label="Kasus"
            leftSection={<IconFolders size={16} />}
            onClick={close}
          />
          <Text size="xs" c="dimmed" mt="md">
            Modul berikutnya: Upload Excel · CEA · BIA · EtD · Approval
          </Text>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/cases" element={<CasesPage />} />
                <Route path="/cases/new" element={<CaseCreatePage />} />
                <Route path="/cases/:caseId" element={<CaseDetailPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
