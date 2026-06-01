import { useState } from 'react'
import {
  Alert,
  Button,
  Checkbox,
  Group,
  Modal,
  PasswordInput,
  Stack,
  Text,
  Textarea,
  Title,
} from '@mantine/core'
import { IconAlertTriangle, IconShieldCheck } from '@tabler/icons-react'

import type { ApprovalDecision } from './types'
import { DECISION_LABEL_ID } from './types'

interface Props {
  opened: boolean
  decision: ApprovalDecision
  recommendationId: number | null
  onClose: () => void
  onSubmit: (payload: {
    decision: ApprovalDecision
    confirmation_acknowledged: boolean
    password: string
    reason: string
    recommendation_id: number
  }) => void
  isSubmitting: boolean
}

export function SignatureModal({
  opened,
  decision,
  recommendationId,
  onClose,
  onSubmit,
  isSubmitting,
}: Props): JSX.Element {
  const [confirmed, setConfirmed] = useState(false)
  const [password, setPassword] = useState('')
  const [reason, setReason] = useState('')

  const needsReason = decision === 'rejected' || decision === 'revision_requested'
  const canSubmit =
    confirmed && password.length > 0 && recommendationId !== null && (!needsReason || reason.trim().length > 0)

  const reset = (): void => {
    setConfirmed(false)
    setPassword('')
    setReason('')
  }

  const handleSubmit = (): void => {
    if (!canSubmit || recommendationId === null) return
    onSubmit({
      decision,
      confirmation_acknowledged: confirmed,
      password,
      reason,
      recommendation_id: recommendationId,
    })
  }

  const handleClose = (): void => {
    if (isSubmitting) return
    reset()
    onClose()
  }

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={
        <Group gap="xs">
          <IconShieldCheck size={20} />
          <Title order={5}>Tanda Tangan Sign-Off — {DECISION_LABEL_ID[decision]}</Title>
        </Group>
      }
      size="lg"
      centered
      closeOnClickOutside={false}
    >
      <Stack gap="md">
        <Alert color="yellow" icon={<IconAlertTriangle size={16} />} variant="light">
          Tindakan ini akan dicatat permanen di audit trail dengan email, sandi-verifikasi
          server, alamat IP, dan stempel waktu Anda. Tidak dapat dibatalkan setelah dikirim.
        </Alert>

        {recommendationId === null && (
          <Alert color="red" variant="light">
            Tidak ada rekomendasi terkomputasi. Tutup modal ini, jalankan "Hitung Rekomendasi"
            terlebih dahulu di tab Rekomendasi, lalu coba kembali.
          </Alert>
        )}

        {needsReason && (
          <Textarea
            label="Alasan"
            placeholder="Wajib diisi untuk penolakan atau permintaan revisi..."
            required
            autosize
            minRows={3}
            value={reason}
            onChange={(e) => setReason(e.currentTarget.value)}
          />
        )}

        <Checkbox
          label={
            <Text size="sm">
              Saya konfirmasi bahwa saya telah meninjau dossier kasus secara menyeluruh dan
              mengambil keputusan ini sebagai Ketua KFT.
            </Text>
          }
          checked={confirmed}
          onChange={(e) => setConfirmed(e.currentTarget.checked)}
        />

        <PasswordInput
          label="Sandi Anda"
          placeholder="Ketik ulang sandi untuk verifikasi"
          description="Server akan memverifikasi sandi Anda sebelum tanda tangan dibuat"
          required
          value={password}
          onChange={(e) => setPassword(e.currentTarget.value)}
          autoComplete="current-password"
        />

        <Group justify="flex-end" mt="sm">
          <Button variant="default" onClick={handleClose} disabled={isSubmitting}>
            Batal
          </Button>
          <Button
            color={decision === 'approved' ? 'teal' : decision === 'rejected' ? 'red' : 'orange'}
            onClick={handleSubmit}
            loading={isSubmitting}
            disabled={!canSubmit}
          >
            {decision === 'approved'
              ? 'Setujui & Tanda Tangan'
              : decision === 'rejected'
                ? 'Tolak & Tanda Tangan'
                : 'Minta Revisi & Tanda Tangan'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
