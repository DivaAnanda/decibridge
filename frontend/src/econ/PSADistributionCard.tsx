import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Card, Group, Select, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconDeviceFloppy } from '@tabler/icons-react'

import { getEconParameters, saveEconPSADistributions } from '../api/econ'
import { trimDecimal } from './format'
import {
  DISTRIBUTION_LABEL,
  DISTRIBUTION_PARAM_NAMES,
  PSA_SAMPLED_KEYS,
  allowedDistributions,
  deriveParams,
  impliedMean,
  impliedSd,
  meanMismatch,
  parseNumber,
  parseUncertainty,
} from './psaDistribution'
import {
  ALTERNATIVE_LABEL,
  PARAM_KEY_LABEL,
  type Alternative,
  type EconParameter,
  type PSADistribution,
  type PSADistributionPayload,
} from './types'

interface Props {
  caseId: string
  canEdit: boolean
  onDirtyChange: (dirty: boolean) => void
}

interface Draft {
  distribution: PSADistribution
  // What the user typed as SE/SD; the two parameters are what gets stored.
  uncertainty: string
  p1: string
  p2: string
}

interface RowError {
  index: number
  id: number | null
  field: string
  message: string
}

type FieldErrors = Record<string, string[]>

const ALTERNATIVE_ORDER: Alternative[] = ['intervention', 'comparator', 'shared']

const FIXED_DRAFT: Draft = { distribution: 'fixed', uncertainty: '', p1: '', p2: '' }

function compact(value: number): string {
  return Number(value.toPrecision(6)).toString()
}

function formatNumber(value: number): string {
  return value.toLocaleString('id-ID', { maximumFractionDigits: 4 })
}

function sdText(distribution: PSADistribution, p1: string, p2: string): string {
  const a = parseNumber(p1)
  const b = parseNumber(p2)
  if (a === null || b === null) return ''
  const sd = impliedSd(distribution, a, b)
  return sd === null ? '' : compact(sd)
}

function toDraft(p: EconParameter): Draft {
  const p1 = p.dist_param1 === null ? '' : trimDecimal(p.dist_param1)
  const p2 = p.dist_param2 === null ? '' : trimDecimal(p.dist_param2)
  return { distribution: p.distribution, uncertainty: sdText(p.distribution, p1, p2), p1, p2 }
}

function toPayload(id: number, draft: Draft): PSADistributionPayload {
  const clean = (text: string): string | null => text.trim().replace(',', '.') || null
  return {
    id,
    distribution: draft.distribution,
    dist_param1: draft.distribution === 'fixed' ? null : clean(draft.p1),
    dist_param2: draft.distribution === 'fixed' ? null : clean(draft.p2),
  }
}

function withDerivedParams(draft: Draft, base: number): Draft {
  const sd = parseUncertainty(draft.uncertainty, base)
  const derived = sd === null ? null : deriveParams(draft.distribution, base, sd)
  return { ...draft, p1: derived?.p1 ?? '', p2: derived?.p2 ?? '' }
}

/** Why the typed SE/SD produced no parameters, in the user's terms. */
function uncertaintyHint(draft: Draft, base: number): string | null {
  if (draft.distribution === 'fixed' || draft.uncertainty.trim() === '') return null
  const sd = parseUncertainty(draft.uncertainty, base)
  if (sd === null) return 'Isi angka atau persen, mis. 600000 atau 10%.'
  if (sd <= 0) return 'Harus lebih besar dari 0.'
  if (deriveParams(draft.distribution, base, sd) !== null) return null
  if (draft.distribution === 'beta') {
    return base > 0 && base < 1
      ? 'SD terlalu besar untuk nilai dasar ini.'
      : 'Beta memerlukan nilai dasar di antara 0 dan 1.'
  }
  return 'Nilai dasar harus lebih besar dari 0; jika 0, pilih Tetap.'
}

/**
 * How the typed SE/SD was understood. The dot is the decimal point here, as in
 * the parameter table, while the base column prints grouped thousands
 * ("600.000"); reading the value back makes a mistyped "600.000" (= 600) visible.
 */
function uncertaintyReadback(draft: Draft, base: number): string | null {
  if (draft.distribution === 'fixed') return null
  const sd = parseUncertainty(draft.uncertainty, base)
  if (sd === null || !(sd > 0)) return null
  if (base === 0) return `= ${formatNumber(sd)}`
  const share = ((sd / Math.abs(base)) * 100).toLocaleString('id-ID', { maximumFractionDigits: 2 })
  return `= ${formatNumber(sd)} (${share}% nilai dasar)`
}

function distributionMean(draft: Draft): number | null {
  const a = parseNumber(draft.p1)
  const b = parseNumber(draft.p2)
  if (a === null || b === null) return null
  return impliedMean(draft.distribution, a, b)
}

export function PSADistributionCard({ caseId, canEdit, onDirtyChange }: Props): JSX.Element {
  const queryClient = useQueryClient()
  const paramsQuery = useQuery({
    queryKey: ['econ', caseId, 'params'],
    queryFn: () => getEconParameters(caseId),
  })

  // PSA reads the year-agnostic rows only; per-year rows belong to the BIA.
  const sampled = useMemo(
    () =>
      (paramsQuery.data ?? [])
        .filter((p) => PSA_SAMPLED_KEYS.includes(p.key) && p.year_index === null)
        .sort(
          (a, b) =>
            PSA_SAMPLED_KEYS.indexOf(a.key) - PSA_SAMPLED_KEYS.indexOf(b.key) ||
            ALTERNATIVE_ORDER.indexOf(a.alternative) - ALTERNATIVE_ORDER.indexOf(b.alternative),
        ),
    [paramsQuery.data],
  )

  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [errors, setErrors] = useState<Record<number, FieldErrors>>({})

  useEffect(() => {
    setDrafts(Object.fromEntries(sampled.map((p) => [p.id, toDraft(p)])))
    setErrors({})
  }, [sampled])

  const draftOf = (p: EconParameter): Draft => drafts[p.id] ?? toDraft(p)

  const isDirty = sampled.some(
    (p) => JSON.stringify(toPayload(p.id, draftOf(p))) !== JSON.stringify(toPayload(p.id, toDraft(p))),
  )

  useEffect(() => {
    onDirtyChange(isDirty)
  }, [isDirty, onDirtyChange])

  const save = useMutation({
    mutationFn: (payload: PSADistributionPayload[]) => saveEconPSADistributions(caseId, payload),
    onSuccess: (saved) => {
      queryClient.setQueryData(['econ', caseId, 'params'], saved)
      void queryClient.invalidateQueries({ queryKey: ['econ', caseId, 'psa'] })
      notifications.show({
        color: 'teal',
        message: 'Distribusi PSA disimpan. Jalankan ulang PSA agar hasil memakainya.',
      })
    },
    onError: (err: { response?: { data?: { detail?: string; row_errors?: RowError[] } } }) => {
      const data = err.response?.data
      const byRow: Record<number, FieldErrors> = {}
      for (const e of data?.row_errors ?? []) {
        if (e.id === null) continue
        const row = (byRow[e.id] ??= {})
        row[e.field] = [...(row[e.field] ?? []), e.message]
      }
      setErrors(byRow)
      notifications.show({
        color: 'red',
        title: 'Distribusi belum tersimpan',
        message: data?.detail ?? 'Gagal menyimpan distribusi.',
        autoClose: 10000,
      })
    },
  })

  const update = (id: number, next: Draft): void => {
    setDrafts((prev) => ({ ...prev, [id]: next }))
    setErrors((prev) => {
      if (!(id in prev)) return prev
      const rest = { ...prev }
      delete rest[id]
      return rest
    })
  }

  const changeDistribution = (p: EconParameter, distribution: PSADistribution): void => {
    if (distribution === 'fixed') {
      update(p.id, FIXED_DRAFT)
      return
    }
    update(p.id, withDerivedParams({ ...draftOf(p), distribution }, Number(p.value)))
  }

  const changeUncertainty = (p: EconParameter, uncertainty: string): void => {
    update(p.id, withDerivedParams({ ...draftOf(p), uncertainty }, Number(p.value)))
  }

  const changeParam = (p: EconParameter, field: 'p1' | 'p2', text: string): void => {
    const next = { ...draftOf(p), [field]: text }
    update(p.id, { ...next, uncertainty: sdText(next.distribution, next.p1, next.p2) })
  }

  const mismatched = sampled.filter((p) => {
    const mean = distributionMean(draftOf(p))
    return mean !== null && meanMismatch(Number(p.value), mean)
  })

  return (
    <Card withBorder padding="lg" radius="md">
      <Stack gap={4} mb="md">
        <Title order={4}>Distribusi Parameter PSA</Title>
        <Text size="sm" c="dimmed">
          Pilih distribusi ketidakpastian untuk tiap parameter yang disampel. Isi SE/SD sebagai angka
          atau persen dari nilai dasar (mis. 10%) agar kedua parameter distribusi dihitung otomatis,
          atau isi kedua parameter secara langsung (mis. alpha 60 dan beta 140). Parameter berstatus
          Tetap tidak disampel.
        </Text>
      </Stack>

      {mismatched.length > 0 && (
        <Alert color="orange" variant="light" mb="md" p="xs">
          <Text size="xs">
            {mismatched.length} parameter memiliki mean distribusi yang berbeda lebih dari 5% dari
            nilai dasarnya, biasanya karena nilai dasar diubah setelah distribusi diatur. PSA
            menyampel di sekitar mean distribusi, bukan nilai dasar; isi ulang SE/SD pada baris
            tersebut agar distribusinya mengikuti nilai dasar yang sekarang.
          </Text>
        </Alert>
      )}

      {sampled.length === 0 ? (
        <Text size="sm" c="dimmed">
          Belum ada parameter yang dapat disampel. Isi parameter di tab Analisis Ekonomi terlebih
          dahulu.
        </Text>
      ) : (
        <Table.ScrollContainer minWidth={1040}>
          <Table verticalSpacing="xs">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Parameter</Table.Th>
                <Table.Th>Nilai dasar</Table.Th>
                <Table.Th>Distribusi</Table.Th>
                <Table.Th>SE / SD</Table.Th>
                <Table.Th>Parameter 1</Table.Th>
                <Table.Th>Parameter 2</Table.Th>
                <Table.Th>Mean distribusi</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {sampled.map((p) => {
                const draft = draftOf(p)
                const base = Number(p.value)
                const isFixed = draft.distribution === 'fixed'
                // A workbook import can store text outside the choices (e.g. "Beta"),
                // so the lookups below must survive a value the type does not admit.
                const [name1, name2] = DISTRIBUTION_PARAM_NAMES[draft.distribution] ?? ['', '']
                const hint = uncertaintyHint(draft, base)
                const readback = uncertaintyReadback(draft, base)
                const allowed = allowedDistributions(p.param_type)
                // A stored choice outside the allowed set must stay visible.
                const options = allowed.includes(draft.distribution)
                  ? allowed
                  : [...allowed, draft.distribution]
                const rowErrors = errors[p.id] ?? {}
                const mean = distributionMean(draft)
                const isMismatch = mean !== null && meanMismatch(base, mean)

                return (
                  <Table.Tr key={p.id}>
                    <Table.Td>
                      <Text size="sm">{PARAM_KEY_LABEL[p.key] ?? p.key}</Text>
                      <Text size="xs" c="dimmed">
                        {ALTERNATIVE_LABEL[p.alternative]}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" ff="monospace">
                        {formatNumber(base)}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Select
                        size="xs"
                        w={190}
                        aria-label={`Distribusi ${PARAM_KEY_LABEL[p.key] ?? p.key} ${ALTERNATIVE_LABEL[p.alternative]}`}
                        disabled={!canEdit}
                        allowDeselect={false}
                        data={options.map((d) => ({ value: d, label: DISTRIBUTION_LABEL[d] ?? d }))}
                        value={draft.distribution}
                        onChange={(v) => changeDistribution(p, (v ?? 'fixed') as PSADistribution)}
                        error={[...(rowErrors.distribution ?? []), ...(rowErrors.id ?? [])].join(' ') || undefined}
                      />
                    </Table.Td>
                    <Table.Td>
                      <TextInput
                        size="xs"
                        w={130}
                        aria-label="SE atau SD"
                        placeholder={isFixed ? '' : 'mis. 10%'}
                        disabled={!canEdit || isFixed}
                        value={draft.uncertainty}
                        onChange={(e) => changeUncertainty(p, e.currentTarget.value)}
                        error={hint ?? undefined}
                      />
                      {hint === null && readback !== null && (
                        <Text size="xs" c="dimmed" mt={2}>
                          {readback}
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <TextInput
                        size="xs"
                        w={170}
                        aria-label={name1 || 'Parameter 1'}
                        leftSection={
                          <Text size="xs" c="dimmed">
                            {name1}
                          </Text>
                        }
                        leftSectionWidth={52}
                        disabled={!canEdit || isFixed}
                        value={draft.p1}
                        onChange={(e) => changeParam(p, 'p1', e.currentTarget.value)}
                        error={rowErrors.dist_param1?.join(' ')}
                      />
                    </Table.Td>
                    <Table.Td>
                      <TextInput
                        size="xs"
                        w={170}
                        aria-label={name2 || 'Parameter 2'}
                        leftSection={
                          <Text size="xs" c="dimmed">
                            {name2}
                          </Text>
                        }
                        leftSectionWidth={52}
                        disabled={!canEdit || isFixed}
                        value={draft.p2}
                        onChange={(e) => changeParam(p, 'p2', e.currentTarget.value)}
                        error={rowErrors.dist_param2?.join(' ')}
                      />
                    </Table.Td>
                    <Table.Td>
                      {mean === null ? (
                        <Text size="sm" c="dimmed">
                          -
                        </Text>
                      ) : (
                        <>
                          <Text size="sm" ff="monospace" c={isMismatch ? 'orange' : undefined}>
                            {formatNumber(mean)}
                          </Text>
                          {isMismatch && (
                            <Text size="xs" c="orange">
                              berbeda dari nilai dasar
                            </Text>
                          )}
                        </>
                      )}
                    </Table.Td>
                  </Table.Tr>
                )
              })}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}

      {canEdit && sampled.length > 0 && (
        <Group justify="flex-end" mt="md">
          {isDirty && (
            <Text size="xs" c="orange">
              Ada perubahan distribusi yang belum disimpan.
            </Text>
          )}
          <Button
            leftSection={<IconDeviceFloppy size={16} />}
            variant="default"
            loading={save.isPending}
            disabled={!isDirty}
            onClick={() => save.mutate(sampled.map((p) => toPayload(p.id, draftOf(p))))}
          >
            Simpan Distribusi
          </Button>
        </Group>
      )}
    </Card>
  )
}
