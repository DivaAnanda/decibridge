import { Alert, List, Text } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'

import { INTEGRITY_FLAG_LABEL, type CaseDetail } from './types'

interface Props {
  caseDetail: CaseDetail
}

export function IntegrityAlert({ caseDetail }: Props): JSX.Element | null {
  if (!caseDetail.integrity_flag) return null

  const reasons = caseDetail.integrity_notes
    .split(';')
    .map((r) => r.trim())
    .filter(Boolean)

  return (
    <Alert
      color="red"
      variant="light"
      icon={<IconAlertTriangle size={18} />}
      title={`Integritas kasus: ${INTEGRITY_FLAG_LABEL[caseDetail.integrity_flag]}`}
    >
      <Text size="sm">
        Kasus ini dikunci sebelum aturan kelengkapan dossier diberlakukan, sehingga
        keputusannya dibangun di atas komponen yang belum lengkap. Kasus tetap disimpan
        sebagai rujukan dan bahan regression test, tetapi <strong>tidak boleh diperlakukan
        sebagai arsip keputusan yang sah</strong> dan tidak dapat diarsipkan atau
        diterbitkan ulang sebelum diperbaiki.
      </Text>
      {reasons.length > 0 && (
        <List size="sm" mt="xs">
          {reasons.map((r) => (
            <List.Item key={r}>{r}</List.Item>
          ))}
        </List>
      )}
    </Alert>
  )
}
