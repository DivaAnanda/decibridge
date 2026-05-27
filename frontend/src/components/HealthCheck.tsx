import { useQuery } from '@tanstack/react-query'
import { Card, Group, Text, Badge, Loader, Stack } from '@mantine/core'

import { getHealth } from '../api/client'

export function HealthCheck() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30_000,
  })

  return (
    <Card withBorder padding="md" radius="md">
      <Group justify="space-between" mb="sm">
        <Text fw={600}>Backend health</Text>
        <Badge
          color={data?.status === 'ok' ? 'green' : isError ? 'red' : 'gray'}
          variant="filled"
          onClick={() => void refetch()}
          style={{ cursor: 'pointer' }}
        >
          {isFetching ? '...' : (data?.status ?? (isError ? 'unreachable' : 'unknown'))}
        </Badge>
      </Group>

      {isLoading && <Loader size="sm" />}

      {isError && (
        <Text size="sm" c="red">
          Could not reach API at {import.meta.env.VITE_API_BASE_URL}: {String(error)}
        </Text>
      )}

      {data && (
        <Stack gap={4}>
          {Object.entries(data.checks).map(([key, value]) => (
            <Group key={key} justify="space-between">
              <Text size="sm">{key}</Text>
              <Text size="sm" c={value === 'ok' ? 'green' : 'red'}>
                {value}
              </Text>
            </Group>
          ))}
        </Stack>
      )}
    </Card>
  )
}
