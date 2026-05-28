import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Modal,
  NumberInput,
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
import { IconPencil, IconPlus, IconTrash } from '@tabler/icons-react'

import {
  createReference,
  deleteReference,
  listReferences,
  updateReference,
} from '../api/etd'
import { useAuth } from '../auth/useAuth'
import {
  REFERENCE_TYPE_LABEL,
  type ReferenceCitation,
  type ReferenceCitationPayload,
  type ReferenceType,
} from './types'

const TYPE_OPTIONS = Object.entries(REFERENCE_TYPE_LABEL).map(([value, label]) => ({ value, label }))

interface Props {
  caseId: string
  caseIsLocked: boolean
}

export function ReferencesPanel({ caseId, caseIsLocked }: Props): JSX.Element {
  const { hasRole } = useAuth()
  const canEdit = !caseIsLocked && hasRole('hta_analyst', 'farmasi_sekretaris')
  const queryClient = useQueryClient()

  const [editing, setEditing] = useState<ReferenceCitation | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const refsQuery = useQuery({
    queryKey: ['references', caseId],
    queryFn: () => listReferences(caseId),
  })

  const form = useForm<ReferenceCitationPayload>({
    initialValues: {
      reference_type: 'journal_article',
      citation_text: '',
      authors: '',
      publication_year: new Date().getFullYear(),
      title: '',
      journal_name: '',
      doi_pmid: '',
      url: '',
      evidence_summary: '',
    },
    validate: {
      citation_text: (v) => (v.trim().length > 0 ? null : 'Sitasi wajib diisi'),
    },
  })

  const openCreate = (): void => {
    setEditing(null)
    form.reset()
    setModalOpen(true)
  }

  const openEdit = (ref: ReferenceCitation): void => {
    setEditing(ref)
    form.setValues({
      reference_type: ref.reference_type,
      citation_text: ref.citation_text,
      authors: ref.authors,
      publication_year: ref.publication_year ?? new Date().getFullYear(),
      title: ref.title,
      journal_name: ref.journal_name,
      doi_pmid: ref.doi_pmid,
      url: ref.url,
      evidence_summary: ref.evidence_summary,
    })
    setModalOpen(true)
  }

  const saveMutation = useMutation({
    mutationFn: async (payload: ReferenceCitationPayload) =>
      editing ? updateReference(caseId, editing.id, payload) : createReference(caseId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['references', caseId] })
      void queryClient.invalidateQueries({ queryKey: ['etd', caseId] })
      notifications.show({ color: 'teal', message: 'Referensi tersimpan.' })
      setModalOpen(false)
    },
    onError: () => {
      notifications.show({ color: 'red', message: 'Gagal menyimpan referensi.' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteReference(caseId, id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['references', caseId] })
      notifications.show({ color: 'teal', message: 'Referensi dihapus.' })
    },
  })

  return (
    <Card withBorder padding="lg" radius="md">
      <Group justify="space-between" mb="sm">
        <Title order={4}>Referensi Bukti</Title>
        {canEdit && (
          <Button leftSection={<IconPlus size={14} />} onClick={openCreate} size="xs">
            Tambah Referensi
          </Button>
        )}
      </Group>

      {refsQuery.isLoading && (
        <Center py="md">
          <Loader size="sm" />
        </Center>
      )}

      {refsQuery.data && refsQuery.data.length === 0 && (
        <Text c="dimmed" size="sm">
          Belum ada referensi. Tambahkan minimal satu sumber bukti agar anggota KFT dapat
          mengaitkannya dengan appraisal mereka.
        </Text>
      )}

      {refsQuery.data && refsQuery.data.length > 0 && (
        <Table verticalSpacing="xs" striped>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Jenis</Table.Th>
              <Table.Th>Sitasi</Table.Th>
              <Table.Th>DOI/PMID</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {refsQuery.data.map((r) => (
              <Table.Tr key={r.id}>
                <Table.Td>
                  <Badge variant="light" size="sm">
                    {REFERENCE_TYPE_LABEL[r.reference_type]}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{r.citation_text}</Text>
                  {r.url && (
                    <Anchor href={r.url} target="_blank" size="xs">
                      {r.url}
                    </Anchor>
                  )}
                </Table.Td>
                <Table.Td ff="monospace" fz="xs">
                  {r.doi_pmid || '—'}
                </Table.Td>
                <Table.Td>
                  {canEdit && (
                    <Group gap={4} justify="flex-end">
                      <ActionIcon variant="subtle" onClick={() => openEdit(r)} aria-label="Edit">
                        <IconPencil size={14} />
                      </ActionIcon>
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        onClick={() => {
                          if (confirm('Hapus referensi ini?')) deleteMutation.mutate(r.id)
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
        title={editing ? 'Edit Referensi' : 'Tambah Referensi'}
        size="lg"
      >
        <form
          onSubmit={form.onSubmit((values) => {
            saveMutation.mutate({
              ...values,
              publication_year: values.publication_year || null,
            })
          })}
        >
          <Stack gap="sm">
            <Select
              label="Jenis"
              data={TYPE_OPTIONS}
              allowDeselect={false}
              {...form.getInputProps('reference_type')}
              onChange={(v) =>
                form.setFieldValue('reference_type', (v ?? 'journal_article') as ReferenceType)
              }
            />
            <Textarea
              label="Sitasi (format bebas)"
              placeholder="Smith J et al. 2024. Title. Journal."
              autosize
              minRows={2}
              required
              {...form.getInputProps('citation_text')}
            />
            <Group grow>
              <TextInput label="Penulis" {...form.getInputProps('authors')} />
              <NumberInput
                label="Tahun"
                min={1900}
                max={new Date().getFullYear()}
                {...form.getInputProps('publication_year')}
              />
            </Group>
            <TextInput label="Judul" {...form.getInputProps('title')} />
            <Group grow>
              <TextInput label="Jurnal / Sumber" {...form.getInputProps('journal_name')} />
              <TextInput label="DOI / PMID" {...form.getInputProps('doi_pmid')} />
            </Group>
            <TextInput label="URL" {...form.getInputProps('url')} />
            <Textarea
              label="Ringkasan bukti"
              placeholder="Temuan utama, populasi, ukuran efek..."
              autosize
              minRows={2}
              {...form.getInputProps('evidence_summary')}
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
