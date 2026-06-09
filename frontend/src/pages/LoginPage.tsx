import { useState } from 'react'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Alert,
  Anchor,
  Box,
  Button,
  Card,
  Center,
  Code,
  Divider,
  Group,
  PasswordInput,
  Stack,
  TextInput,
  Title,
  Text,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { IconAlertCircle, IconArrowLeft } from '@tabler/icons-react'

import { useAuth } from '../auth/useAuth'

interface LocationState {
  from?: { pathname: string }
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  // After login, send the user to wherever they were trying to reach, defaulting
  // to /dashboard (the new authed home — `/` is the public landing page).
  const from = (location.state as LocationState | null)?.from?.pathname ?? '/dashboard'

  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const form = useForm({
    initialValues: { email: '', password: '' },
    validate: {
      email: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : 'Format email tidak valid'),
      password: (v) => (v.length >= 1 ? null : 'Kata sandi wajib diisi'),
    },
  })

  const handleSubmit = form.onSubmit(async (values) => {
    setError(null)
    setSubmitting(true)
    try {
      await login(values.email, values.password)
      navigate(from, { replace: true })
    } catch (e) {
      setError('Email atau kata sandi salah.')
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <Center mih="100vh" bg="gray.0">
      <Stack w={420} gap="sm">
        <Anchor
          component={RouterLink}
          to="/"
          size="sm"
          c="dimmed"
          underline="never"
        >
          <Group gap={4}>
            <IconArrowLeft size={14} />
            Kembali ke beranda
          </Group>
        </Anchor>

        <Card withBorder radius="md" padding="xl" shadow="sm">
          <Stack gap="md">
            <Box>
              <Title order={3}>DeciBridge</Title>
              <Text size="sm" c="dimmed">
                Masuk ke sistem pendukung keputusan KFT
              </Text>
            </Box>

            {error && (
              <Alert color="red" icon={<IconAlertCircle size={16} />} variant="light">
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <Stack gap="md">
                <TextInput
                  label="Email"
                  placeholder="nama@rumahsakit.id"
                  autoComplete="email"
                  required
                  {...form.getInputProps('email')}
                />
                <PasswordInput
                  label="Kata sandi"
                  autoComplete="current-password"
                  required
                  {...form.getInputProps('password')}
                />
                <Button type="submit" loading={submitting} fullWidth mt="sm">
                  Masuk
                </Button>
              </Stack>
            </form>

            <Divider label="Akun demo" labelPosition="center" />

            <Stack gap={4}>
              <Text size="xs" c="dimmed">
                Password untuk semua akun:{' '}
                <Code fz="xs">TestPass123!</Code>
              </Text>
              <Text size="xs" c="dimmed">
                Email:{' '}
                <Code fz="xs">hta@test.local</Code>,{' '}
                <Code fz="xs">sekre@test.local</Code>,{' '}
                <Code fz="xs">kft1@test.local</Code>,{' '}
                <Code fz="xs">ketua@test.local</Code>,{' '}
                <Code fz="xs">adminit@test.local</Code>
              </Text>
            </Stack>
          </Stack>
        </Card>
      </Stack>
    </Center>
  )
}
