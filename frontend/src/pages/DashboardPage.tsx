import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link as RouterLink } from 'react-router-dom'
import {
  Anchor,
  Badge,
  Card,
  Center,
  Grid,
  Group,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from '@mantine/core'
import {
  IconArchive,
  IconArrowRight,
  IconBulb,
  IconCalculator,
  IconChevronRight,
  IconClipboardCheck,
  IconFileText,
  IconLockSquare,
  IconPlus,
  IconScale,
  IconShieldCheck,
} from '@tabler/icons-react'

import { listCases } from '../api/cases'
import { STATUS_COLOR, STATUS_LABEL_ID, type CaseListItem } from '../cases/types'
import { useAuth } from '../auth/useAuth'
import { HealthCheck } from '../components/HealthCheck'

type RoleSlug =
  | 'admin_it'
  | 'hta_analyst'
  | 'farmasi_sekretaris'
  | 'kft_member'
  | 'ketua_kft'

interface QuickLink {
  label: string
  description: string
  to: string
  icon: typeof IconPlus
  color: string
}

const ROLE_QUICK_LINKS: Record<RoleSlug, QuickLink[]> = {
  hta_analyst: [
    {
      label: 'Buat Kasus Baru',
      description: 'Mulai evaluasi formularium baru',
      to: '/cases/new',
      icon: IconPlus,
      color: 'teal',
    },
    {
      label: 'Daftar Kasus',
      description: 'Hitung CEA / BIA, lengkapi EtD',
      to: '/cases',
      icon: IconCalculator,
      color: 'blue',
    },
  ],
  farmasi_sekretaris: [
    {
      label: 'Buat Kasus Baru',
      description: 'Inisiasi kasus formularium',
      to: '/cases/new',
      icon: IconPlus,
      color: 'teal',
    },
    {
      label: 'Daftar Kasus',
      description: 'Kelola siklus hidup kasus & CBA',
      to: '/cases',
      icon: IconFileText,
      color: 'blue',
    },
  ],
  kft_member: [
    {
      label: 'Daftar Kasus',
      description: 'Beri penilaian EtD & bobot domain',
      to: '/cases',
      icon: IconScale,
      color: 'violet',
    },
  ],
  ketua_kft: [
    {
      label: 'Kasus Menunggu Tinjauan',
      description: 'Setujui, tolak, atau minta revisi',
      to: '/cases?status=in_review',
      icon: IconClipboardCheck,
      color: 'orange',
    },
    {
      label: 'Daftar Kasus',
      description: 'Lihat seluruh kasus aktif',
      to: '/cases',
      icon: IconFileText,
      color: 'blue',
    },
  ],
  admin_it: [
    {
      label: 'Daftar Kasus',
      description: 'Lihat status kasus formularium',
      to: '/cases',
      icon: IconFileText,
      color: 'blue',
    },
    {
      label: 'Kasus Terarsipkan',
      description: 'Audit arsip 7 tahun',
      to: '/cases?status=archived',
      icon: IconArchive,
      color: 'gray',
    },
  ],
}

interface StatBox {
  status: 'draft' | 'in_review' | 'approved' | 'locked' | 'archived'
  label: string
  icon: typeof IconPlus
}

const STAT_BOXES: StatBox[] = [
  { status: 'draft', label: 'Draft', icon: IconFileText },
  { status: 'in_review', label: 'Dalam Tinjauan', icon: IconClipboardCheck },
  { status: 'approved', label: 'Disetujui', icon: IconShieldCheck },
  { status: 'locked', label: 'Terkunci', icon: IconLockSquare },
  { status: 'archived', label: 'Terarsipkan', icon: IconArchive },
]

function countByStatus(cases: CaseListItem[]): Record<string, number> {
  const counts: Record<string, number> = {
    draft: 0,
    in_review: 0,
    approved: 0,
    locked: 0,
    archived: 0,
  }
  for (const c of cases) {
    const current = counts[c.status]
    if (current !== undefined) counts[c.status] = current + 1
  }
  return counts
}

export function DashboardPage(): JSX.Element {
  const { user } = useAuth()

  const casesQuery = useQuery({
    queryKey: ['cases', 'all'],
    queryFn: () => listCases(),
  })

  const cases: CaseListItem[] = useMemo(
    () => casesQuery.data?.results ?? [],
    [casesQuery.data],
  )
  const counts = useMemo(() => countByStatus(cases), [cases])
  const recent = useMemo(() => cases.slice(0, 5), [cases])

  const userRoles = (user?.roles ?? []).map((r) => r.slug as RoleSlug)
  const primaryRole: RoleSlug | null = userRoles[0] ?? null
  const quickLinks = primaryRole ? ROLE_QUICK_LINKS[primaryRole] ?? [] : []

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-end">
        <Stack gap={4}>
          <Text size="sm" c="dimmed">
            Beranda
          </Text>
          <Title order={2}>
            Selamat datang{user?.full_name ? `, ${user.full_name}` : ''}
          </Title>
          {user && user.roles.length > 0 && (
            <Group gap={6} mt={4}>
              {user.roles.map((r) => (
                <Badge key={r.slug} variant="light" color="blue">
                  {r.display_name_id}
                </Badge>
              ))}
              {user.is_superuser && (
                <Badge color="grape" variant="filled">
                  Superuser
                </Badge>
              )}
            </Group>
          )}
        </Stack>
        <Stack gap={2} align="flex-end">
          <Text size="xs" c="dimmed">
            {user?.email}
          </Text>
          {user?.institution && (
            <Text size="xs" c="dimmed">
              {user.institution}
            </Text>
          )}
        </Stack>
      </Group>

      {/* Case-status stats */}
      <SimpleGrid cols={{ base: 2, sm: 3, lg: 5 }} spacing="md">
        {STAT_BOXES.map((box) => {
          const Icon = box.icon
          return (
            <Paper key={box.status} withBorder p="md" radius="md">
              <Group justify="space-between" align="flex-start">
                <Stack gap={2}>
                  <Text size="xs" c="dimmed">
                    {box.label}
                  </Text>
                  <Text size="xl" fw={700}>
                    {casesQuery.isLoading ? '…' : counts[box.status]}
                  </Text>
                </Stack>
                <ThemeIcon
                  variant="light"
                  color={STATUS_COLOR[box.status]}
                  size="lg"
                  radius="md"
                >
                  <Icon size={18} />
                </ThemeIcon>
              </Group>
            </Paper>
          )
        })}
      </SimpleGrid>

      <Grid gutter="md">
        {/* Quick links per role */}
        <Grid.Col span={{ base: 12, md: 7 }}>
          <Card withBorder padding="lg" radius="md" h="100%">
            <Title order={5} mb="sm">
              Aksi Cepat
            </Title>
            <Text size="xs" c="dimmed" mb="md">
              Berdasarkan peran Anda, berikut tindakan utama yang biasanya
              dijalankan dalam alur kerja KFT.
            </Text>
            {quickLinks.length === 0 ? (
              <Text size="sm" c="dimmed">
                Belum ada peran ditugaskan. Hubungi Admin IT.
              </Text>
            ) : (
              <Stack gap="xs">
                {quickLinks.map((link) => {
                  const Icon = link.icon
                  return (
                    <Anchor
                      key={link.to}
                      component={RouterLink}
                      to={link.to}
                      underline="never"
                    >
                      <Paper withBorder p="sm" radius="sm">
                        <Group justify="space-between">
                          <Group>
                            <ThemeIcon
                              color={link.color}
                              variant="light"
                              size="lg"
                              radius="md"
                            >
                              <Icon size={18} />
                            </ThemeIcon>
                            <Stack gap={0}>
                              <Text fw={500}>{link.label}</Text>
                              <Text size="xs" c="dimmed">
                                {link.description}
                              </Text>
                            </Stack>
                          </Group>
                          <IconChevronRight size={16} />
                        </Group>
                      </Paper>
                    </Anchor>
                  )
                })}
              </Stack>
            )}
          </Card>
        </Grid.Col>

        {/* Recent cases */}
        <Grid.Col span={{ base: 12, md: 5 }}>
          <Card withBorder padding="lg" radius="md" h="100%">
            <Group justify="space-between" mb="sm">
              <Title order={5}>Kasus Terbaru</Title>
              <Anchor component={RouterLink} to="/cases" size="xs">
                Lihat semua{' '}
                <IconArrowRight size={12} style={{ verticalAlign: 'middle' }} />
              </Anchor>
            </Group>
            {casesQuery.isLoading && (
              <Center py="md">
                <Loader size="sm" />
              </Center>
            )}
            {!casesQuery.isLoading && recent.length === 0 && (
              <Text size="sm" c="dimmed">
                Belum ada kasus. Mulai dengan tombol "Buat Kasus Baru" di atas.
              </Text>
            )}
            {recent.length > 0 && (
              <Stack gap="xs">
                {recent.map((c) => (
                  <Anchor
                    key={c.case_id}
                    component={RouterLink}
                    to={`/cases/${c.case_id}`}
                    underline="never"
                  >
                    <Paper withBorder p="xs" radius="sm">
                      <Group justify="space-between" wrap="nowrap">
                        <Stack gap={0} style={{ minWidth: 0 }}>
                          <Text size="xs" ff="monospace" c="dimmed" truncate>
                            {c.case_id}
                          </Text>
                          <Text size="sm" fw={500} truncate>
                            {c.case_title}
                          </Text>
                        </Stack>
                        <Badge
                          color={STATUS_COLOR[c.status]}
                          variant="light"
                          size="sm"
                        >
                          {STATUS_LABEL_ID[c.status]}
                        </Badge>
                      </Group>
                    </Paper>
                  </Anchor>
                ))}
              </Stack>
            )}
          </Card>
        </Grid.Col>
      </Grid>

      {/* Workflow refresher */}
      <Card withBorder padding="lg" radius="md">
        <Title order={5} mb="sm">
          Alur Kerja Singkat
        </Title>
        <SimpleGrid cols={{ base: 2, md: 4 }} spacing="md">
          <WorkflowStep
            icon={IconPlus}
            color="teal"
            n={1}
            title="Buat & isi"
            sub="Sekretaris / HTA membuat kasus, isi CEA & BIA"
          />
          <WorkflowStep
            icon={IconScale}
            color="violet"
            n={2}
            title="Penilaian EtD"
            sub="Anggota KFT memberi judgement 9 domain GRADE"
          />
          <WorkflowStep
            icon={IconBulb}
            color="blue"
            n={3}
            title="Rekomendasi"
            sub="Skor komposit & traffic-light dihitung otomatis"
          />
          <WorkflowStep
            icon={IconShieldCheck}
            color="green"
            n={4}
            title="Sign-off & Kunci"
            sub="Ketua KFT menyetujui, kunci, lalu arsipkan"
          />
        </SimpleGrid>
      </Card>

      <HealthCheck />
    </Stack>
  )
}

interface WorkflowStepProps {
  icon: typeof IconPlus
  color: string
  n: number
  title: string
  sub: string
}

function WorkflowStep({ icon: Icon, color, n, title, sub }: WorkflowStepProps): JSX.Element {
  return (
    <Stack gap={6} align="flex-start">
      <Group gap="xs">
        <ThemeIcon color={color} variant="light" size="lg" radius="xl">
          <Icon size={18} />
        </ThemeIcon>
        <Badge color={color} variant="filled" radius="sm">
          {n}
        </Badge>
      </Group>
      <Text fw={500}>{title}</Text>
      <Text size="xs" c="dimmed">
        {sub}
      </Text>
    </Stack>
  )
}

