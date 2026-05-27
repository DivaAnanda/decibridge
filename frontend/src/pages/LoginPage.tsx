import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Card,
  Center,
  PasswordInput,
  Stack,
  TextInput,
  Title,
  Text,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { IconAlertCircle } from '@tabler/icons-react'

import { useAuth } from '../auth/useAuth'

interface LocationState {
  from?: { pathname: string }
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as LocationState | null)?.from?.pathname ?? '/'

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
      <Box w={420}>
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
          </Stack>
        </Card>
      </Box>
    </Center>
  )
}
