import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Group,
  Loader,
  Modal,
  Select,
  Stack,
  Table,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconCheck, IconPencil, IconPlus, IconTrash, IconX } from '@tabler/icons-react'

import { createCBA, deleteCBA, listCBA, updateCBA } from '../api/recommendation'
import { useAuth } from '../auth/useAuth'
import {
  CBA_OPERATOR_LABEL,
  type CBACriterion,
  type CBACriterionPayload,
  type CBAOperator,
} from './types'

const OPERATOR_OPTIONS = Object.entries(CBA_OPERATOR_LABEL).map(([value, label]) => ({
  value,
  label,
}))

interface Props {
  caseId: string
  caseIsLocked: boolean
}

export function CBACard({ caseId, caseIsLocked }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canEdit = !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris', 'ketua_kft')
  const queryClient = useQueryClient()

  const [editing, setEditing] = useState<CBACriterion | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const cbaQuery = useQuery({
    queryKey: ['recommendation', caseId, 'cba'],
    queryFn: () => listCBA(caseId),
  })

  const form = useForm<CBACriterionPayload>({
    initialValues: {
      criterion_name: '',
      field_reference: '',
      operator: 'is_present',
      expected_value: '',
      description: '',
      is_satisfied: false,
    },
    validate: {
      criterion_name: (v) => (v.trim().length > 0 ? null : 'Nama kriteria wajib diisi'),
    },
  })

  const openCreate = (): void => {
    setEditing(null)
    form.reset()
    setModalOpen(true)
  }

  const openEdit = (c: CBACriterion): void => {
    setEditing(c)
    form.setValues({
      criterion_name: c.criterion_name,
      field_reference: c.field_reference,
      operator: c.operator,
      expected_value: c.expected_value,
      description: c.description,
      is_satisfied: c.is_satisfied,
    })
    setModalOpen(true)
  }

  const saveMutation = useMutation({
    mutationFn: (payload: CBACriterionPayload) =>
      editing ? updateCBA(caseId, editing.id, payload) : createCBA(caseId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['recommendation', caseId, 'cba'] })
      notifications.show({ color: 'teal', message: 'Kriteria CBA tersimpan.' })
      setModalOpen(false)
    },
    onError: () => {
      notifications.show({ color: 'red', message: 'Gagal menyimpan kriteria.' })
    },
  })

  const toggleSatisfied = useMutation({
    mutationFn: ({ id, value }: { id: number; value: boolean }) =>
      updateCBA(caseId, id, { is_satisfied: value }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['recommendation', caseId, 'cba'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCBA(caseId, id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['recommendation', caseId, 'cba'] })
      notifications.show({ color: 'teal', message: 'Kriteria dihapus.' })
    },
  })

  if (cbaQuery.isLoading) {
    return (
      <Center py="md">
        <Loader size="sm" />
      </Center>
    )
  }

  const criteria = cbaQuery.data ?? []
  const satisfied = criteria.filter((c) => c.is_satisfied).length

  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Stack gap={2}>
          <Title order={4}>Kriteria Akses (CBA)</Title>
          {criteria.length > 0 && (
            <Text size="xs" c="dimmed">
              {satisfied} dari {criteria.length} kriteria terpenuhi
            </Text>
          )}
        </Stack>
        {canEdit && (
          <Button leftSection={<IconPlus size={14} />} size="xs" onClick={openCreate}>
            Tambah Kriteria
          </Button>
        )}
      </Group>

      {criteria.length === 0 && (
        <Text c="dimmed" size="sm">
          Belum ada kriteria CBA. Tanpa kriteria, skor CBA otomatis 100 (tidak ada batasan).
          Tambahkan kriteria jika adopsi obat ini perlu dibatasi pada kondisi tertentu.
        </Text>
      )}

      {criteria.length > 0 && (
        <Table verticalSpacing="xs" striped>
          <Table.Thead>
            <Table.Tr>
              <Table.Th style={{ width: 40 }}>#</Table.Th>
              <Table.Th>Kriteria</Table.Th>
              <Table.Th>Field</Table.Th>
              <Table.Th>Operator</Table.Th>
              <Table.Th>Nilai</Table.Th>
              <Table.Th>Terpenuhi</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {criteria.map((c) => (
              <Table.Tr key={c.id}>
                <Table.Td>{c.order}</Table.Td>
                <Table.Td>
                  <Text size="sm" fw={500}>
                    {c.criterion_name}
                  </Text>
                  {c.description && (
                    <Text size="xs" c="dimmed">
                      {c.description}
                    </Text>
                  )}
                </Table.Td>
                <Table.Td ff="monospace" fz="xs">
                  {c.field_reference || '—'}
                </Table.Td>
                <Table.Td>
                  <Badge variant="light" size="sm">
                    {CBA_OPERATOR_LABEL[c.operator]}
                  </Badge>
                </Table.Td>
                <Table.Td>{c.expected_value || '—'}</Table.Td>
                <Table.Td>
                  {canEdit ? (
                    <Checkbox
                      checked={c.is_satisfied}
                      onChange={(e) =>
                        toggleSatisfied.mutate({ id: c.id, value: e.currentTarget.checked })
                      }
                    />
                  ) : c.is_satisfied ? (
                    <IconCheck size={16} color="green" />
                  ) : (
                    <IconX size={16} color="red" />
                  )}
                </Table.Td>
                <Table.Td>
                  {canEdit && (
                    <Group gap={4} justify="flex-end">
                      <ActionIcon variant="subtle" onClick={() => openEdit(c)} aria-label="Edit">
                        <IconPencil size={14} />
                      </ActionIcon>
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        onClick={() => {
                          if (confirm('Hapus kriteria ini?')) deleteMutation.mutate(c.id)
                        }}
                        aria-label="Hapus"
                      >
                        <IconTrash size={14} />
                      </ActionIcon>
                    </Group>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}

      <Modal
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? 'Edit Kriteria CBA' : 'Tambah Kriteria CBA'}
        size="lg"
      >
        <form onSubmit={form.onSubmit((values) => saveMutation.mutate(values))}>
          <Stack gap="sm">
            <TextInput
              label="Nama kriteria"
              placeholder="mis. Diresepkan oleh kardiolog"
              required
              {...form.getInputProps('criterion_name')}
            />
            <TextInput
              label="Field referensi (opsional)"
              placeholder="mis. prescriber.specialty"
              description="Field klinis yang akan diperiksa otomatis di masa depan"
              {...form.getInputProps('field_reference')}
            />
            <Group grow>
              <Select
                label="Operator"
                data={OPERATOR_OPTIONS}
                allowDeselect={false}
                {...form.getInputProps('operator')}
                onChange={(v) => form.setFieldValue('operator', (v ?? 'is_present') as CBAOperator)}
              />
              <TextInput
                label="Nilai yang diharapkan"
                placeholder="mis. kardiolog"
                {...form.getInputProps('expected_value')}
              />
            </Group>
            <Textarea
              label="Deskripsi"
              placeholder="Penjelasan lebih lanjut..."
              autosize
              minRows={2}
              {...form.getInputProps('description')}
            />
            <Checkbox
              label="Kriteria terpenuhi pada konteks RS saat ini"
              {...form.getInputProps('is_satisfied', { type: 'checkbox' })}
            />
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setModalOpen(false)}>
                Batal
              </Button>
              <Button type="submit" loading={saveMutation.isPending}>
                {editing ? 'Simpan' : 'Tambah'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Card>
  )
}
