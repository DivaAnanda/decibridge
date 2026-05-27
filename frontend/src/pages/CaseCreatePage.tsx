import { useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  Anchor,
  Box,
  Button,
  Card,
  Checkbox,
  Group,
  Select,
  Stack,
  Stepper,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconArrowLeft } from '@tabler/icons-react'

import { createCase } from '../api/cases'
import type { CaseCreateInput, CasePerspective } from '../cases/types'

const PERSPECTIVE_OPTIONS: { value: CasePerspective; label: string }[] = [
  { value: 'hospital', label: 'Rumah Sakit' },
  { value: 'payer_bpjs', label: 'BPJS / Pembayar' },
  { value: 'societal', label: 'Masyarakat' },
]

const CASE_ID_RE = /^[A-Z][A-Z0-9_]{2,63}$/

export function CaseCreatePage() {
  const navigate = useNavigate()
  const [active, setActive] = useState(0)
  const [includeQuestion, setIncludeQuestion] = useState(true)

  const form = useForm<CaseCreateInput & {
    decision_question: NonNullable<CaseCreateInput['decision_question']>
  }>({
    initialValues: {
      case_id: '',
      case_title: '',
      technology: '',
      comparator: '',
      indication: '',
      population: '',
      setting: '',
      perspective: 'hospital',
      decision_question: {
        question_text: '',
        pico_population: '',
        pico_intervention: '',
        pico_comparator: '',
        pico_outcome: '',
      },
    },
    validate: (values) => {
      const errors: Record<string, string> = {}
      if (active === 0) {
        if (!CASE_ID_RE.test(values.case_id))
          errors.case_id = 'Format: UPPER_SNAKE_CASE, contoh HF_ARNI_ACEI_001'
        if (!values.case_title.trim()) errors.case_title = 'Judul wajib diisi'
      }
      if (active === 1) {
        if (!values.technology.trim()) errors.technology = 'Intervensi wajib diisi'
        if (!values.comparator.trim()) errors.comparator = 'Komparator wajib diisi'
        if (!values.indication.trim()) errors.indication = 'Indikasi wajib diisi'
      }
      if (active === 2 && includeQuestion) {
        if (!values.decision_question.question_text.trim())
          errors['decision_question.question_text'] = 'Pertanyaan wajib diisi'
      }
      return errors
    },
  })

  const mutation = useMutation({
    mutationFn: (payload: CaseCreateInput) => createCase(payload),
    onSuccess: (data) => {
      notifications.show({ color: 'teal', message: `Kasus ${data.case_id} berhasil dibuat.` })
      navigate(`/cases/${data.case_id}`, { replace: true })
    },
    onError: (err: { response?: { data?: Record<string, unknown> } }) => {
      const data = err.response?.data ?? {}
      const message = Object.entries(data)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : String(v)}`)
        .join('\n') || 'Terjadi kesalahan.'
      notifications.show({ color: 'red', title: 'Gagal membuat kasus', message })
    },
  })

  const nextStep = () => {
    const validation = form.validate()
    if (validation.hasErrors) return
    setActive((s) => Math.min(s + 1, 3))
  }
  const prevStep = () => setActive((s) => Math.max(s - 1, 0))

  const submit = () => {
    const values = form.values
    const payload: CaseCreateInput = {
      case_id: values.case_id,
      case_title: values.case_title,
      technology: values.technology,
      comparator: values.comparator,
      indication: values.indication,
      population: values.population,
      setting: values.setting,
      perspective: values.perspective,
    }
    if (includeQuestion && values.decision_question.question_text.trim()) {
      payload.decision_question = values.decision_question
    }
    mutation.mutate(payload)
  }

  return (
    <Stack gap="md">
      <Anchor component={RouterLink} to="/cases" size="sm">
        <Group gap={4}>
          <IconArrowLeft size={14} />
          Kembali ke daftar kasus
        </Group>
      </Anchor>

      <Title order={2}>Buat Kasus Baru</Title>
      <Text c="dimmed" size="sm">
        Lengkapi metadata kasus. Detail klinis lengkap dapat ditambahkan melalui unggah Excel
        case pack pada Sprint berikutnya.
      </Text>

      <Card withBorder padding="lg" radius="md">
        <Stepper active={active} onStepClick={setActive}>
          <Stepper.Step label="Identitas" description="ID & judul">
            <Stack gap="md" mt="md">
              <TextInput
                label="ID Kasus"
                placeholder="HF_ARNI_ACEI_001"
                description="Format: UPPER_SNAKE_CASE, 3-64 karakter"
                required
                ff="monospace"
                {...form.getInputProps('case_id')}
              />
              <TextInput
                label="Judul Kasus"
                placeholder="ARNI vs ACEI pada pasien HFrEF"
                required
                {...form.getInputProps('case_title')}
              />
            </Stack>
          </Stepper.Step>

          <Stepper.Step label="Klinis" description="Intervensi & populasi">
            <Stack gap="md" mt="md">
              <TextInput label="Intervensi (Teknologi)" placeholder="Sacubitril/valsartan" required {...form.getInputProps('technology')} />
              <TextInput label="Komparator" placeholder="ACE inhibitor" required {...form.getInputProps('comparator')} />
              <TextInput label="Indikasi" placeholder="Heart failure with reduced ejection fraction" required {...form.getInputProps('indication')} />
              <Textarea label="Populasi" placeholder="Pasien HFrEF rawat jalan/rawat inap..." autosize minRows={2} {...form.getInputProps('population')} />
              <TextInput label="Setting" placeholder="KFT Rumah Sakit" {...form.getInputProps('setting')} />
              <Select
                label="Perspektif"
                data={PERSPECTIVE_OPTIONS}
                allowDeselect={false}
                {...form.getInputProps('perspective')}
              />
            </Stack>
          </Stepper.Step>

          <Stepper.Step label="PICO" description="Pertanyaan keputusan">
            <Stack gap="md" mt="md">
              <Checkbox
                label="Tambahkan pertanyaan PICO sekarang"
                checked={includeQuestion}
                onChange={(e) => setIncludeQuestion(e.currentTarget.checked)}
              />
              {includeQuestion && (
                <>
                  <Textarea
                    label="Pertanyaan klinis"
                    placeholder="Apakah ARNI lebih efektif daripada ACEI pada HFrEF?"
                    autosize
                    minRows={2}
                    required
                    {...form.getInputProps('decision_question.question_text')}
                  />
                  <TextInput label="Populasi (P)" {...form.getInputProps('decision_question.pico_population')} />
                  <TextInput label="Intervensi (I)" {...form.getInputProps('decision_question.pico_intervention')} />
                  <TextInput label="Komparator (C)" {...form.getInputProps('decision_question.pico_comparator')} />
                  <TextInput label="Outcome (O)" {...form.getInputProps('decision_question.pico_outcome')} />
                </>
              )}
            </Stack>
          </Stepper.Step>

          <Stepper.Completed>
            <Box mt="md">
              <Text size="sm" c="dimmed" mb="md">Tinjau ringkasan, lalu klik "Simpan Kasus".</Text>
              <Card withBorder padding="md" radius="sm">
                <Stack gap={4}>
                  <Text size="xs" c="dimmed" ff="monospace">{form.values.case_id}</Text>
                  <Text fw={600}>{form.values.case_title}</Text>
                  <Text size="sm" c="dimmed">
                    {form.values.technology} vs {form.values.comparator} — {form.values.indication}
                  </Text>
                </Stack>
              </Card>
            </Box>
          </Stepper.Completed>
        </Stepper>

        <Group justify="space-between" mt="xl">
          <Button variant="default" onClick={prevStep} disabled={active === 0}>
            Sebelumnya
          </Button>
          {active < 3 ? (
            <Button onClick={nextStep}>Lanjut</Button>
          ) : (
            <Button onClick={submit} loading={mutation.isPending} color="teal">
              Simpan Kasus
            </Button>
          )}
        </Group>
      </Card>
    </Stack>
  )
}
