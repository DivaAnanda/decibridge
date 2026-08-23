import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  List,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconFileSpreadsheet, IconDownload, IconUpload } from '@tabler/icons-react'

import { downloadValidationTemplate, validateWorkbook } from '../api/econ'
import type { ValidationReport } from './types'

interface Props {
  caseId: string
  canEdit: boolean
}

export function ValidationImportCard({ caseId, canEdit }: Props): JSX.Element {
  const fileRef = useRef<HTMLInputElement>(null)
  const [report, setReport] = useState<ValidationReport | null>(null)

  const download = useMutation({
    mutationFn: () => downloadValidationTemplate(caseId),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'DeciBridge_Economic_Validation_Model.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    },
    onError: () => notifications.show({ color: 'red', message: 'Gagal mengunduh template.' }),
  })

  const validate = useMutation({
    mutationFn: (file: File) => validateWorkbook(caseId, file),
    onSuccess: (data) => {
      setReport(data)
      notifications.show({
        color: data.status === 'PASS' ? 'teal' : 'orange',
        message: `Validasi selesai: ${data.status}`,
      })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      notifications.show({ color: 'red', title: 'Gagal', message: err.response?.data?.detail ?? 'Kesalahan.' }),
  })

  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Group gap={6}>
          <IconFileSpreadsheet size={18} />
          <Title order={4}>Import & Validasi Excel</Title>
        </Group>
        <Button
          size="xs"
          variant="light"
          leftSection={<IconDownload size={14} />}
          loading={download.isPending}
          onClick={() => download.mutate()}
        >
          Unduh Template
        </Button>
      </Group>
      <Text size="xs" c="dimmed" mb="md">
        Unggah workbook validasi (.xlsx) untuk mengisi parameter model, menjalankan perhitungan,
        dan membandingkan hasil aktual dengan nilai acuan (expected) beserta toleransinya.
      </Text>

      {canEdit && (
        <Group>
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx"
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.currentTarget.files?.[0]
              if (file) validate.mutate(file)
              e.currentTarget.value = ''
            }}
          />
          <Button
            leftSection={<IconUpload size={16} />}
            loading={validate.isPending}
            onClick={() => fileRef.current?.click()}
          >
            Unggah & Validasi
          </Button>
        </Group>
      )}

      {report && (
        <Stack gap="sm" mt="md">
          <Group>
            <Text fw={600}>Hasil:</Text>
            <Badge color={report.status === 'PASS' ? 'teal' : 'red'} size="lg">
              {report.status}
            </Badge>
          </Group>

          {report.issues.length > 0 && (
            <Alert color="orange" title="Masalah validasi">
              <List size="sm">
                {report.issues.map((i) => (
                  <List.Item key={i}>{i}</List.Item>
                ))}
              </List>
            </Alert>
          )}

          {report.checks.length > 0 && (
            <Table.ScrollContainer minWidth={560}>
              <Table striped withTableBorder>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Metrik</Table.Th>
                    <Table.Th>Expected</Table.Th>
                    <Table.Th>Actual</Table.Th>
                    <Table.Th>Selisih</Table.Th>
                    <Table.Th>Toleransi</Table.Th>
                    <Table.Th>Status</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {report.checks.map((c) => (
                    <Table.Tr key={c.metric}>
                      <Table.Td>{c.metric}</Table.Td>
                      <Table.Td ff="monospace">{c.expected}</Table.Td>
                      <Table.Td ff="monospace">{c.actual ?? '—'}</Table.Td>
                      <Table.Td ff="monospace">{c.diff ?? '—'}</Table.Td>
                      <Table.Td ff="monospace">{c.tolerance}</Table.Td>
                      <Table.Td>
                        <Badge color={c.pass ? 'teal' : 'red'} variant="light">
                          {c.pass ? 'PASS' : 'FAIL'}
                        </Badge>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          )}
        </Stack>
      )}
    </Card>
  )
}
