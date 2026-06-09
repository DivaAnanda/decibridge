import { useEffect } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import {
  Anchor,
  Badge,
  Box,
  Button,
  Card,
  Container,
  Divider,
  Grid,
  Group,
  List,
  Paper,
  rem,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from '@mantine/core'
import {
  IconActivity,
  IconArchive,
  IconArrowRight,
  IconBulb,
  IconCalculator,
  IconChevronRight,
  IconCoin,
  IconFileText,
  IconHistory,
  IconLockSquare,
  IconReportAnalytics,
  IconScale,
  IconShieldCheck,
  IconStethoscope,
  IconUsersGroup,
} from '@tabler/icons-react'

import { useAuth } from '../auth/useAuth'

/**
 * Public landing page — the first impression for lecturer + portfolio viewers.
 * Adapted from the Accenprove capstone reference (Tailwind → Mantine).
 */
export function LandingPage(): JSX.Element {
  const { user } = useAuth()
  const navigate = useNavigate()

  // If user is already logged in, send them to the app dashboard.
  useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true })
    }
  }, [user, navigate])

  return (
    <Box className="db-landing">
      <LandingStyles />

      {/* Animated background blobs */}
      <Box className="db-bg">
        <div className="db-blob db-blob-1" />
        <div className="db-blob db-blob-2" />
        <div className="db-blob db-blob-3" />
      </Box>

      <PublicNavbar />

      {/* Hero */}
      <Box component="section" py={80} px="md" pos="relative">
        <Container size="lg">
          <Stack align="center" gap="xl" maw={900} mx="auto" mb={64}>
            <Badge
              variant="light"
              color="blue"
              size="lg"
              leftSection={<IconActivity size={14} />}
            >
              v1.0.0 — Pilot ARNI vs ACEI untuk HFrEF
            </Badge>

            <Title
              order={1}
              ta="center"
              fz={{ base: 44, sm: 64, lg: 78 }}
              fw={800}
              lh={1.05}
              className="db-headline"
            >
              Pendukung Keputusan
              <br />
              <span className="db-gradient-text">Formularium KFT</span>
              <br />
              berbasis Bukti
            </Title>

            <Text
              ta="center"
              c="dimmed"
              fz={{ base: 18, sm: 22 }}
              maw={720}
              fw={400}
            >
              Alur kerja end-to-end untuk Komite Farmasi & Terapi rumah sakit
              Indonesia — dari CEA, BIA, dan 9 domain GRADE EtD sampai sign-off
              Ketua KFT, arsip permanen, dan policy brief siap rapat.
            </Text>

            <Group gap="md" mt="lg">
              <Button
                component={RouterLink}
                to="/login"
                size="lg"
                rightSection={<IconArrowRight size={18} />}
                gradient={{ from: 'blue.6', to: 'indigo.7', deg: 135 }}
                variant="gradient"
                radius="md"
                className="db-cta-primary"
              >
                Masuk untuk Demo
              </Button>
              <Button
                component="a"
                href="#features"
                size="lg"
                variant="default"
                radius="md"
              >
                Pelajari Fitur
              </Button>
            </Group>

            <Text size="xs" c="dimmed" mt="xs">
              Akun demo siap pakai · password{' '}
              <Text component="span" ff="monospace" fz="xs">
                TestPass123!
              </Text>
            </Text>
          </Stack>

          {/* Hero preview card — fake "Rekomendasi" snapshot to show the product */}
          <HeroPreview />
        </Container>
      </Box>

      {/* Features */}
      <Box component="section" id="features" py={80} px="md">
        <Container size="lg">
          <Stack align="center" gap="md" mb={64}>
            <Badge variant="light" color="blue" size="md">
              Fitur Unggulan
            </Badge>
            <Title order={2} ta="center" fz={{ base: 36, sm: 48 }} fw={700}>
              Pipeline 12 Sprint, 1 Aplikasi
            </Title>
            <Text ta="center" c="dimmed" fz="lg" maw={620}>
              Setiap tahap audit-grade dengan invariant append-only, tanda tangan
              digital, dan jejak versi otomatis.
            </Text>
          </Stack>

          <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="lg">
            <FeatureCard
              icon={IconCalculator}
              gradient={['blue.5', 'cyan.6']}
              title="CEA Quick"
              description="ICER + 6 klasifikasi dominansi + analisis sensitivitas ±20% dalam satu kali hitung."
            />
            <FeatureCard
              icon={IconCoin}
              gradient={['teal.5', 'green.6']}
              title="BIA Proyeksi"
              description="Dampak anggaran 1 & 3 tahun dengan trajectory chart dan klasifikasi severity."
            />
            <FeatureCard
              icon={IconScale}
              gradient={['violet.5', 'grape.6']}
              title="EtD 9 Domain GRADE"
              description="Voting per anggota KFT, certainty 4-level, bobot domain, referensi tertaut."
            />
            <FeatureCard
              icon={IconBulb}
              gradient={['orange.5', 'red.6']}
              title="Traffic-Light Synthesis"
              description="HIJAU/KUNING/MERAH otomatis dari skor komposit + aturan CBA dengan justifikasi."
            />
            <FeatureCard
              icon={IconShieldCheck}
              gradient={['indigo.6', 'blue.7']}
              title="Sign-Off 2-Langkah"
              description="Ketua KFT konfirmasi + password re-verify. Append-only signature dengan IP & timestamp."
            />
            <FeatureCard
              icon={IconReportAnalytics}
              gradient={['pink.5', 'red.5']}
              title="Policy Brief DOCX/PDF"
              description="7 bagian otomatis dari kasus terkunci. Hash SHA-256 per dokumen."
            />
            <FeatureCard
              icon={IconHistory}
              gradient={['cyan.6', 'blue.6']}
              title="Versi & Diff"
              description="Snapshot otomatis pada lock. Timeline audit + perbandingan field per versi."
            />
            <FeatureCard
              icon={IconArchive}
              gradient={['gray.6', 'dark.5']}
              title="Arsip 7 Tahun"
              description="Manifest JSON SHA-256 segel. Setiap baris klinis di-fingerprint, tamper-evident."
            />
          </SimpleGrid>
        </Container>
      </Box>

      {/* How it works */}
      <Box component="section" py={80} px="md" bg="gray.0">
        <Container size="lg">
          <Stack align="center" gap="md" mb={64}>
            <Badge variant="light" color="teal" size="md">
              Alur Kerja
            </Badge>
            <Title order={2} ta="center" fz={{ base: 36, sm: 48 }} fw={700}>
              4 Langkah, Tertelusur Penuh
            </Title>
            <Text ta="center" c="dimmed" fz="lg" maw={620}>
              Dari kasus baru sampai arsip permanen. Setiap transisi tercatat
              dalam audit log yang tidak dapat diubah.
            </Text>
          </Stack>

          <SimpleGrid cols={{ base: 1, md: 4 }} spacing="md">
            <Step
              n="01"
              icon={IconFileText}
              color="teal"
              title="Buat & Isi"
              sub="HTA Analyst membuat kasus, mengisi CEA dan BIA. Sekretaris menambah kriteria CBA."
            />
            <Step
              n="02"
              icon={IconScale}
              color="violet"
              title="EtD & Bobot"
              sub="Anggota KFT memberi judgement 9 domain GRADE dan menetapkan bobot kepentingan."
            />
            <Step
              n="03"
              icon={IconShieldCheck}
              color="blue"
              title="Sign-Off Ketua"
              sub="Ketua KFT meninjau dossier, tanda tangan dengan password re-verify, lalu mengunci keputusan."
            />
            <Step
              n="04"
              icon={IconArchive}
              color="gray"
              title="Arsip & Brief"
              sub="Admin IT mengarsipkan dengan manifest SHA-256. Policy brief DOCX/PDF siap untuk rapat."
            />
          </SimpleGrid>
        </Container>
      </Box>

      {/* Role benefits */}
      <Box component="section" py={80} px="md">
        <Container size="lg">
          <Stack align="center" gap="md" mb={64}>
            <Badge variant="light" color="grape" size="md">
              5 Peran
            </Badge>
            <Title order={2} ta="center" fz={{ base: 36, sm: 48 }} fw={700}>
              Tampilan Berbeda untuk Tiap Peran
            </Title>
            <Text ta="center" c="dimmed" fz="lg" maw={620}>
              Setiap pengguna melihat aksi sesuai kewenangan. Pembatasan
              ditegakkan di backend, bukan hanya tampilan.
            </Text>
          </Stack>

          <SimpleGrid cols={{ base: 1, sm: 2, lg: 5 }} spacing="md">
            <RoleCard
              icon={IconStethoscope}
              color="blue"
              role="HTA Analyst"
              email="hta@test.local"
              perks={[
                'Buat kasus & jalankan CEA/BIA',
                'Kelola referensi ilmiah',
                'Hitung rekomendasi',
                'Terbitkan policy brief',
              ]}
            />
            <RoleCard
              icon={IconFileText}
              color="teal"
              role="Sekretaris KFT"
              email="sekre@test.local"
              perks={[
                'Manajemen siklus kasus',
                'Definisi kriteria CBA',
                'Submit untuk tinjauan',
                'Generate brief',
              ]}
            />
            <RoleCard
              icon={IconUsersGroup}
              color="grape"
              role="Anggota KFT"
              email="kft1@test.local"
              perks={[
                'Vote 9 domain GRADE',
                'Lampirkan referensi',
                'Set bobot domain',
                'Lihat dossier read-only',
              ]}
            />
            <RoleCard
              icon={IconShieldCheck}
              color="indigo"
              role="Ketua KFT"
              email="ketua@test.local"
              perks={[
                'Sign-off dengan 2-langkah',
                'Approve / Reject / Revisi',
                'Kunci keputusan permanen',
                'Arsipkan dengan manifest',
              ]}
              highlight
            />
            <RoleCard
              icon={IconLockSquare}
              color="gray"
              role="Admin IT"
              email="adminit@test.local"
              perks={[
                'Manajemen user & peran',
                'Arsipkan kasus terkunci',
                'Verifikasi hash manifest',
                'Tanpa akses klinis',
              ]}
            />
          </SimpleGrid>
        </Container>
      </Box>

      {/* CTA */}
      <Box
        component="section"
        py={96}
        px="md"
        className="db-cta-section"
      >
        <Container size="md">
          <Stack align="center" gap="lg">
            <Title order={2} ta="center" c="white" fz={{ base: 36, sm: 52 }} fw={800}>
              Siap mencoba pipelinenya?
            </Title>
            <Text ta="center" c="rgba(255,255,255,0.85)" fz="lg" maw={520}>
              Login sebagai salah satu dari 5 peran dan jalankan alur penuh dari
              kasus draft sampai arsip permanen — dalam ~10 menit.
            </Text>
            <Button
              component={RouterLink}
              to="/login"
              size="xl"
              radius="md"
              color="white"
              variant="white"
              rightSection={<IconArrowRight size={20} />}
              styles={{
                root: { color: 'var(--mantine-color-blue-7)', fontWeight: 700 },
              }}
            >
              Masuk untuk Demo
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* Footer */}
      <Box component="footer" py="xl" px="md" bg="gray.0">
        <Container size="lg">
          <Group justify="space-between" wrap="wrap" gap="md">
            <Stack gap={2}>
              <Group gap={6}>
                <IconActivity size={18} color="var(--mantine-color-blue-6)" />
                <Text fw={700}>DeciBridge</Text>
              </Group>
              <Text size="xs" c="dimmed">
                Decision support untuk Komite Farmasi & Terapi RS Indonesia
              </Text>
            </Stack>
            <Text size="xs" c="dimmed">
              Built as a university project — pilot case ARNI vs ACEI · MIT-style demo
            </Text>
          </Group>
        </Container>
      </Box>
    </Box>
  )
}

// ---------------------------------------------------------------------------
// Public navbar — minimal, just logo + login button
// ---------------------------------------------------------------------------

function PublicNavbar(): JSX.Element {
  return (
    <Box
      component="nav"
      py="sm"
      px="md"
      pos="sticky"
      top={0}
      style={{
        zIndex: 50,
        backdropFilter: 'blur(12px)',
        backgroundColor: 'rgba(255,255,255,0.7)',
        borderBottom: '1px solid var(--mantine-color-gray-2)',
      }}
    >
      <Container size="lg">
        <Group justify="space-between">
          <Anchor component={RouterLink} to="/" underline="never">
            <Group gap={8}>
              <ThemeIcon
                size="md"
                radius="md"
                variant="gradient"
                gradient={{ from: 'blue.6', to: 'indigo.7' }}
              >
                <IconActivity size={18} />
              </ThemeIcon>
              <Text fw={800} fz="lg">
                DeciBridge
              </Text>
              <Badge variant="light" color="blue" size="xs">
                v1.0.0
              </Badge>
            </Group>
          </Anchor>
          <Group gap="md">
            <Anchor href="#features" c="dimmed" size="sm" fw={500}>
              Fitur
            </Anchor>
            <Button
              component={RouterLink}
              to="/login"
              size="sm"
              radius="md"
              variant="filled"
              color="blue"
            >
              Masuk
            </Button>
          </Group>
        </Group>
      </Container>
    </Box>
  )
}

// ---------------------------------------------------------------------------
// Hero preview — fake "Recommendation" card showing what the app produces
// ---------------------------------------------------------------------------

function HeroPreview(): JSX.Element {
  return (
    <Box maw={1024} mx="auto" mt="xl" pos="relative">
      <Paper
        shadow="xl"
        radius="xl"
        p="xl"
        withBorder
        style={{
          backgroundColor: 'rgba(255,255,255,0.85)',
          backdropFilter: 'blur(20px)',
        }}
      >
        <Group justify="space-between" mb="lg">
          <Group gap={6}>
            <div style={{ width: 10, height: 10, borderRadius: 999, background: '#fa5252' }} />
            <div style={{ width: 10, height: 10, borderRadius: 999, background: '#fab005' }} />
            <div style={{ width: 10, height: 10, borderRadius: 999, background: '#40c057' }} />
            <Text size="xs" c="dimmed" ml="xs">
              Pratinjau Dashboard
            </Text>
          </Group>
          <Badge color="blue" variant="light" size="sm">
            HF_ARNI_ACEI_006
          </Badge>
        </Group>

        <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="md" mb="lg">
          <PreviewStat label="Kasus aktif" value="12" color="blue" />
          <PreviewStat label="Menunggu KFT" value="3" color="orange" />
          <PreviewStat label="Disetujui" value="7" color="teal" />
          <PreviewStat label="Diarsipkan" value="4" color="gray" />
        </SimpleGrid>

        <Grid gutter="md">
          <Grid.Col span={{ base: 12, md: 7 }}>
            <Card withBorder padding="md" radius="md">
              <Stack gap="xs">
                <Group justify="space-between">
                  <Text size="sm" c="dimmed">
                    Rekomendasi
                  </Text>
                  <Badge size="lg" color="teal" variant="filled">
                    HIJAU — Adopsi tanpa syarat
                  </Badge>
                </Group>
                <Group gap="md">
                  <Stack gap={0}>
                    <Text size="xs" c="dimmed">
                      Skor Komposit
                    </Text>
                    <Text fw={800} fz={32}>
                      92.0
                    </Text>
                  </Stack>
                  <Divider orientation="vertical" />
                  <SimpleGrid cols={2} spacing={4} verticalSpacing={4}>
                    <MiniMetric label="Bukti EtD" value="90" />
                    <MiniMetric label="CE Score" value="100" />
                    <MiniMetric label="Anggaran" value="80" />
                    <MiniMetric label="CBA" value="100" />
                  </SimpleGrid>
                </Group>
              </Stack>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 5 }}>
            <Card withBorder padding="md" radius="md" h="100%">
              <Stack gap={6}>
                <Text size="sm" c="dimmed">
                  Tanda Tangan Ketua KFT
                </Text>
                <Group gap={6}>
                  <ThemeIcon color="teal" variant="light" size="sm" radius="xl">
                    <IconShieldCheck size={14} />
                  </ThemeIcon>
                  <Text fw={600} size="sm">
                    Dr. Bambang Sutrisno, Sp.JP
                  </Text>
                </Group>
                <Text size="xs" c="dimmed">
                  ketua@test.local · 8 Juni 2026
                </Text>
                <Divider my={4} />
                <Text size="xs" c="dimmed" ff="monospace">
                  manifest SHA-256:
                </Text>
                <Text
                  size="xs"
                  ff="monospace"
                  c="blue.7"
                  truncate
                  title="b6be31431298e5...d847f"
                >
                  b6be31431298e5...d847f
                </Text>
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>
      </Paper>

      {/* Floating notification badges */}
      <Paper
        shadow="lg"
        radius="md"
        p="sm"
        withBorder
        pos="absolute"
        top={-24}
        right={-12}
        className="db-float db-float-a"
        visibleFrom="sm"
        style={{ background: 'white' }}
      >
        <Group gap="xs">
          <ThemeIcon color="teal" radius="md" variant="light">
            <IconShieldCheck size={16} />
          </ThemeIcon>
          <Stack gap={0}>
            <Text size="xs" c="dimmed">
              Sign-off baru
            </Text>
            <Text size="sm" fw={600}>
              +2 hari ini
            </Text>
          </Stack>
        </Group>
      </Paper>

      <Paper
        shadow="lg"
        radius="md"
        p="sm"
        withBorder
        pos="absolute"
        bottom={-24}
        left={-12}
        className="db-float db-float-b"
        visibleFrom="sm"
        style={{ background: 'white' }}
      >
        <Group gap="xs">
          <ThemeIcon color="blue" radius="md" variant="light">
            <IconArchive size={16} />
          </ThemeIcon>
          <Stack gap={0}>
            <Text size="xs" c="dimmed">
              Arsip permanen
            </Text>
            <Text size="sm" fw={600}>
              4 kasus
            </Text>
          </Stack>
        </Group>
      </Paper>
    </Box>
  )
}

function PreviewStat({
  label,
  value,
  color,
}: {
  label: string
  value: string
  color: string
}): JSX.Element {
  return (
    <Paper
      withBorder
      p="md"
      radius="md"
      style={{ background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)' }}
    >
      <Stack gap={2}>
        <Text size="xs" c="dimmed">
          {label}
        </Text>
        <Text fw={800} fz={24} c={`${color}.7`}>
          {value}
        </Text>
      </Stack>
    </Paper>
  )
}

function MiniMetric({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <Stack gap={0}>
      <Text size="xs" c="dimmed">
        {label}
      </Text>
      <Text fw={600}>{value}</Text>
    </Stack>
  )
}

// ---------------------------------------------------------------------------
// Section cards
// ---------------------------------------------------------------------------

interface FeatureCardProps {
  icon: typeof IconCalculator
  gradient: [string, string]
  title: string
  description: string
}

function FeatureCard({ icon: Icon, gradient, title, description }: FeatureCardProps): JSX.Element {
  return (
    <Paper
      withBorder
      p="lg"
      radius="lg"
      h="100%"
      className="db-feature-card"
    >
      <Stack gap="md">
        <ThemeIcon
          size={52}
          radius="md"
          variant="gradient"
          gradient={{ from: gradient[0], to: gradient[1], deg: 135 }}
        >
          <Icon size={26} />
        </ThemeIcon>
        <Title order={4} fz={18}>
          {title}
        </Title>
        <Text size="sm" c="dimmed" lh={1.6}>
          {description}
        </Text>
      </Stack>
    </Paper>
  )
}

interface StepProps {
  n: string
  icon: typeof IconCalculator
  color: string
  title: string
  sub: string
}

function Step({ n, icon: Icon, color, title, sub }: StepProps): JSX.Element {
  return (
    <Paper
      withBorder
      p="lg"
      radius="lg"
      h="100%"
      className="db-feature-card"
      style={{ background: 'white' }}
    >
      <Stack gap="md">
        <Group justify="space-between">
          <ThemeIcon
            size={56}
            radius="xl"
            variant="gradient"
            gradient={{ from: `${color}.5`, to: `${color}.7`, deg: 135 }}
          >
            <Icon size={28} />
          </ThemeIcon>
          <Text fz={28} fw={900} c={`${color}.2`}>
            {n}
          </Text>
        </Group>
        <Title order={4} fz={18}>
          {title}
        </Title>
        <Text size="sm" c="dimmed" lh={1.6}>
          {sub}
        </Text>
      </Stack>
    </Paper>
  )
}

interface RoleCardProps {
  icon: typeof IconCalculator
  color: string
  role: string
  email: string
  perks: string[]
  highlight?: boolean
}

function RoleCard({
  icon: Icon,
  color,
  role,
  email,
  perks,
  highlight = false,
}: RoleCardProps): JSX.Element {
  return (
    <Paper
      withBorder={!highlight}
      p="lg"
      radius="lg"
      h="100%"
      className="db-feature-card"
      style={
        highlight
          ? {
              background: 'linear-gradient(135deg, var(--mantine-color-indigo-6) 0%, var(--mantine-color-blue-7) 100%)',
              color: 'white',
              border: 'none',
            }
          : undefined
      }
    >
      <Stack gap="sm">
        <ThemeIcon
          size={44}
          radius="md"
          variant={highlight ? 'white' : 'light'}
          color={color}
          style={highlight ? { color: 'var(--mantine-color-indigo-7)' } : undefined}
        >
          <Icon size={22} />
        </ThemeIcon>
        <Stack gap={0}>
          <Title order={5} c={highlight ? 'white' : undefined}>
            {role}
          </Title>
          <Text size="xs" ff="monospace" c={highlight ? 'rgba(255,255,255,0.7)' : 'dimmed'}>
            {email}
          </Text>
        </Stack>
        <List
          spacing={4}
          size="sm"
          icon={
            <ThemeIcon
              size={16}
              radius="xl"
              color={highlight ? 'white' : color}
              variant={highlight ? 'white' : 'light'}
              style={highlight ? { color: 'var(--mantine-color-indigo-7)' } : undefined}
            >
              <IconChevronRight size={10} />
            </ThemeIcon>
          }
        >
          {perks.map((p) => (
            <List.Item key={p} c={highlight ? 'rgba(255,255,255,0.92)' : undefined}>
              {p}
            </List.Item>
          ))}
        </List>
      </Stack>
    </Paper>
  )
}

// ---------------------------------------------------------------------------
// Inline CSS for animations/gradient effects (Mantine doesn't have these built in)
// ---------------------------------------------------------------------------

function LandingStyles(): JSX.Element {
  return (
    <style>{`
      .db-landing {
        position: relative;
        min-height: 100vh;
        background: linear-gradient(180deg, #f0f7ff 0%, #ffffff 50%, #ffffff 100%);
        overflow: hidden;
      }

      .db-bg {
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
      }

      .db-blob {
        position: absolute;
        width: ${rem(288)};
        height: ${rem(288)};
        border-radius: 9999px;
        mix-blend-mode: multiply;
        filter: blur(40px);
        opacity: 0.22;
        animation: db-blob 8s ease-in-out infinite;
      }
      .db-blob-1 { top: 0; left: -16px; background: #74c0fc; }
      .db-blob-2 { top: 0; right: -16px; background: #4dabf7; animation-delay: 2s; }
      .db-blob-3 { bottom: -32px; left: 25%; background: #a5d8ff; animation-delay: 4s; }

      @keyframes db-blob {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(20px, -20px) scale(1.1); }
        50% { transform: translate(-20px, 20px) scale(0.95); }
        75% { transform: translate(20px, 20px) scale(1.05); }
      }

      .db-gradient-text {
        background: linear-gradient(120deg, #1c7ed6 0%, #4263eb 50%, #5f3dc4 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        color: transparent;
        animation: db-gradient 4s linear infinite;
      }

      @keyframes db-gradient {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
      }

      .db-headline {
        letter-spacing: -0.02em;
      }

      .db-float {
        animation: db-float 4s ease-in-out infinite;
      }
      .db-float-b {
        animation-delay: 2s;
      }

      @keyframes db-float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-12px); }
      }

      .db-feature-card {
        transition: transform 0.25s ease, box-shadow 0.25s ease;
      }
      .db-feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px -12px rgba(28, 126, 214, 0.18);
      }

      .db-cta-section {
        background: linear-gradient(135deg, #1c7ed6 0%, #4263eb 50%, #5f3dc4 100%);
        position: relative;
        overflow: hidden;
      }

      .db-cta-section::before {
        content: '';
        position: absolute;
        top: -50px;
        left: -50px;
        width: 300px;
        height: 300px;
        background: rgba(255,255,255,0.1);
        border-radius: 9999px;
        mix-blend-mode: overlay;
        filter: blur(60px);
        animation: db-blob 10s ease-in-out infinite;
      }

      .db-cta-section::after {
        content: '';
        position: absolute;
        bottom: -80px;
        right: -50px;
        width: 360px;
        height: 360px;
        background: rgba(116, 192, 252, 0.4);
        border-radius: 9999px;
        mix-blend-mode: overlay;
        filter: blur(80px);
        animation: db-blob 12s ease-in-out infinite;
        animation-delay: 3s;
      }
    `}</style>
  )
}
