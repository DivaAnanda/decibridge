/**
 * Works the training case (DeciBridge_Demo_Training_Package.xlsx) through all
 * nine menus in the browser and saves the screenshots used by the manual book.
 *
 * It needs an EMPTY database, because it creates the case from scratch:
 * see docs/panduan/docker-compose.manual.yml. Then, from frontend/:
 *
 *   node e2e/capture-manual.mjs                 all phases
 *   node e2e/capture-manual.mjs ekonomi bia     only these, on the existing case
 *
 * Every value typed here is the package's; the script is the record of exactly
 * what was entered to produce the figures in the manual.
 */
import { chromium } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const BASE = process.env.MANUAL_BASE_URL ?? 'http://localhost:5173'
const OUT = path.resolve(HERE, '../../docs/panduan/screenshots')
const CASE_ID = 'DB_DEMO_HF_001'
const PASSWORD = 'TestPass123!'
const USERS = {
  hta: 'hta@test.local',
  sekre: 'sekre@test.local',
  kft: 'kft1@test.local',
  ketua: 'ketua@test.local',
  adminit: 'adminit@test.local',
}

fs.mkdirSync(OUT, { recursive: true })

// What the dashboard computed, kept beside the screenshots so the manual's
// tables quote the run that produced the pictures instead of retyped numbers.
const RESULTS_FILE = path.resolve(OUT, '../results.json')
const results = fs.existsSync(RESULTS_FILE)
  ? JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf8'))
  : {}

const pick = (source, keys) => Object.fromEntries(keys.map((k) => [k, source[k]]))

const SUMMARY = {
  deterministic: (r) =>
    pick(r, [
      'total_cost_intervention', 'total_cost_comparator', 'total_qaly_intervention',
      'total_qaly_comparator', 'incremental_cost', 'incremental_qaly', 'icer',
      'nmb_intervention', 'nmb_comparator', 'inb', 'decision_code',
    ]),
  bia: (r) => ({
    ...pick(r, ['cumulative_net_impact', 'pct_of_total_baseline', 'severity', 'budget_score']),
    per_year: r.per_year.map((y) =>
      pick(y, ['year', 'patients_intervention', 'net_budget_impact', 'pct_of_annual_baseline']),
    ),
  }),
  psa: (r) =>
    pick(r, [
      'n_simulations', 'random_seed', 'prob_cost_effective_base',
      'mean_incremental_cost', 'mean_incremental_qaly',
    ]),
  recommendation: (r) =>
    pick(r, [
      'traffic_light', 'composite_score', 'evidence_strength_score', 'ce_score',
      'budget_score', 'cba_score', 'cba_criteria_count', 'cba_satisfied_count',
    ]),
}

async function record(stage, kind, response) {
  results[stage] = { ...results[stage], [kind]: SUMMARY[kind](await response.json()) }
}

let browser
const pages = {}

async function pageFor(role) {
  if (pages[role]) return pages[role]
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.5,
    locale: 'id-ID',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(15_000)
  await page.goto(`${BASE}/login`)
  await page.getByLabel(/email/i).fill(USERS[role])
  await page.getByLabel(/sandi/i).fill(PASSWORD)
  await page.getByRole('button', { name: 'Masuk' }).click()
  await page.getByText(/Selamat datang/i).waitFor()
  pages[role] = page
  return page
}

/** Toasts sit over the top-right corner; hide them unless they are the subject. */
async function toasts(page, visible) {
  await page.evaluate((show) => {
    let style = document.getElementById('manual-hide-toasts')
    if (show) {
      style?.remove()
      return
    }
    if (!style) {
      style = document.createElement('style')
      style.id = 'manual-hide-toasts'
      // The header and sidebar are position:fixed, so they would be painted
      // across the middle of any card taller than the viewport.
      style.textContent =
        '.mantine-Notifications-root{display:none!important}' +
        '.mantine-AppShell-header,.mantine-AppShell-navbar{position:absolute!important}'
      document.head.appendChild(style)
    }
  }, visible)
}

async function shot(page, name, target) {
  const file = path.join(OUT, `${name}.png`)
  await page.evaluate(() => document.activeElement?.blur())
  await page.waitForTimeout(350)
  if (target === 'full') await page.screenshot({ path: file, fullPage: true })
  else if (target) await target.screenshot({ path: file })
  else await page.screenshot({ path: file })
  console.log('  saved', path.basename(file))
}

async function openCase(page, tab) {
  await page.goto(`${BASE}/cases/${CASE_ID}`)
  await page.getByRole('tab', { name: 'Ringkasan' }).waitFor()
  await toasts(page, false)
  if (tab) await page.getByRole('tab', { name: tab, exact: true }).click()
  await page.waitForTimeout(600)
}

function card(page, heading) {
  return page.locator('.mantine-Card-root', {
    has: page.getByRole('heading', { name: heading, exact: true }),
  }).last()
}

/**
 * Runs a UI action and waits for the API call it triggers, failing loudly if the
 * server refuses it: a screenshot of a step that silently did not save would
 * put a wrong picture in the manual.
 */
async function api(page, method, urlPart, action) {
  const [response] = await Promise.all([
    page.waitForResponse(
      (r) => r.request().method() === method && r.url().includes(urlPart),
      { timeout: 90_000 },
    ),
    action(),
  ])
  if (!response.ok()) {
    throw new Error(`${method} ${urlPart} -> ${response.status()} ${await response.text()}`)
  }
  await page.waitForTimeout(500)
  return response
}

async function choose(page, input, option) {
  await input.click()
  const exact = typeof option === 'string'
  await page.getByRole('option', { name: option, exact }).locator('visible=true').click()
}

// ── Menu 1: Ringkasan ─────────────────────────────────────────────────────

async function login() {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.5,
    locale: 'id-ID',
  })
  const page = await context.newPage()
  await page.goto(`${BASE}/login`)
  await page.getByLabel(/email/i).fill(USERS.hta)
  await page.getByLabel(/sandi/i).fill(PASSWORD)
  await shot(page, '01-login')
  await context.close()

  const hta = await pageFor('hta')
  await toasts(hta, false)
  await shot(hta, '02-beranda')
}

async function ringkasan() {
  const page = await pageFor('hta')
  await page.goto(`${BASE}/cases/new`)
  await toasts(page, false)
  await page.getByLabel('ID Kasus').fill(CASE_ID)
  await page.getByLabel('Judul Kasus').fill('Demo ARNI vs Ramipril pada HFrEF')
  await shot(page, '03-kasus-identitas')
  await page.getByRole('button', { name: 'Lanjut' }).click()

  await page.getByLabel('Intervensi (Teknologi)').fill('Sacubitril/valsartan (ARNI)')
  await page.getByLabel('Komparator').fill('Ramipril (ACEI)')
  await page.getByLabel('Indikasi').fill('Heart failure with reduced ejection fraction (HFrEF)')
  await page.getByLabel('Populasi').fill('Dewasa ≥18 tahun, HFrEF LVEF ≤40%, NYHA II–IV, stabil')
  await page.getByLabel('Setting').fill('Formularium rumah sakit; rawat jalan HFrEF')
  await shot(page, '04-kasus-klinis')
  await page.getByRole('button', { name: 'Lanjut' }).click()

  await page
    .getByLabel('Pertanyaan klinis')
    .fill('Apakah ARNI diadopsi dibanding ramipril untuk pasien HFrEF eligible?')
  await page.getByLabel('Populasi (P)').fill('Dewasa ≥18 tahun, HFrEF LVEF ≤40%, NYHA II–IV, stabil')
  await page.getByLabel('Intervensi (I)').fill('Sacubitril/valsartan (ARNI)')
  await page.getByLabel('Komparator (C)').fill('Ramipril (ACEI)')
  await page.getByLabel('Outcome (O)').fill('QALY; rehospitalisasi HF')
  await shot(page, '05-kasus-pico')
  await page.getByRole('button', { name: 'Lanjut' }).click()
  await page.getByRole('button', { name: 'Simpan Kasus' }).click()

  await page.getByRole('tab', { name: 'Ringkasan' }).waitFor()
  await toasts(page, false)
  await shot(page, '06-ringkasan', 'full')
}

// ── Menu 2: Analisis Ekonomi ──────────────────────────────────────────────

// Package sheet 03 (steps 11-23) then sheet 04 (steps 25-31), in that order.
// Drug cost is quoted per month in the package and stored per year here (x12).
const PARAMETERS = [
  ['Biaya obat per pasien per tahun', 'Intervensi', '', '14400000', 'IDR/pasien/tahun', 'SRC-DEMO-01 Farmasi demo'],
  ['Biaya obat per pasien per tahun', 'Komparator', '', '1200000', 'IDR/pasien/tahun', 'SRC-DEMO-01 Farmasi demo'],
  ['Probabilitas kejadian / rehospitalisasi', 'Intervensi', '', '0.30', 'proporsi/tahun', 'SRC-DEMO-02 RWE demo'],
  ['Probabilitas kejadian / rehospitalisasi', 'Komparator', '', '0.45', 'proporsi/tahun', 'SRC-DEMO-02 RWE demo'],
  ['Biaya per kejadian / rawat inap', 'Bersama', '', '6000000', 'IDR/event', 'SRC-DEMO-03 Billing demo'],
  ['Utility dasar', 'Intervensi', '', '0.78', 'utility 0-1', 'SRC-DEMO-04 Utility demo'],
  ['Utility dasar', 'Komparator', '', '0.74', 'utility 0-1', 'SRC-DEMO-04 Utility demo'],
  ['Disutility kejadian', 'Bersama', '', '0.10', 'decrement/event', 'SRC-DEMO-04 Utility demo'],
  ['Biaya tambahan lain', 'Intervensi', '', '300000', 'IDR/pasien/tahun', 'Monitoring demo'],
  ['Biaya tambahan lain', 'Komparator', '', '200000', 'IDR/pasien/tahun', 'Monitoring demo'],
  ['Jumlah populasi eligible', 'Bersama', 'Tahun 1', '200', 'pasien/tahun', 'SRC-DEMO-05 SIMRS demo'],
  ['Jumlah populasi eligible', 'Bersama', 'Tahun 2', '220', 'pasien/tahun', 'SRC-DEMO-05 SIMRS demo'],
  ['Jumlah populasi eligible', 'Bersama', 'Tahun 3', '240', 'pasien/tahun', 'SRC-DEMO-05 SIMRS demo'],
  ['Uptake', 'Bersama', 'Tahun 1', '0.20', 'proporsi', 'SRC-DEMO-06 Protokol latihan'],
  ['Uptake', 'Bersama', 'Tahun 2', '0.35', 'proporsi', 'SRC-DEMO-06 Protokol latihan'],
  ['Uptake', 'Bersama', 'Tahun 3', '0.50', 'proporsi', 'SRC-DEMO-06 Protokol latihan'],
]

async function ekonomi() {
  const page = await pageFor('hta')
  await openCase(page, 'Analisis Ekonomi')

  const model = card(page, 'Parameter Model Ekonomi')
  await page.getByLabel('Horizon CEA (tahun)').fill('1')
  await page.getByLabel('Horizon BIA (tahun)').fill('3')
  await page.getByLabel('Discount rate biaya').fill('0')
  await page.getByLabel('Discount rate QALY').fill('0')
  await page.getByLabel('WTP threshold (IDR/QALY)').fill('300000000')
  await page.getByLabel('Anggaran tahunan baseline (BIA)').fill('20000000000')
  await page
    .getByLabel('Catatan')
    .fill(
      'Kasus latihan, data sintetis (Paket Data Demo DeciBridge). Biaya obat pada paket ' +
        'dinyatakan per bulan; di sini diisi per tahun (x12).',
    )
  await shot(page, '07-ekonomi-model', model)
  await api(page, 'PUT', '/econ/model/', () =>
    page.getByRole('button', { name: 'Simpan Model' }).click(),
  )

  const registry = card(page, 'Registri Parameter')
  const add = async ([param, alternative, year, value, unit, source]) => {
    await choose(page, page.getByRole('textbox', { name: 'Parameter', exact: true }), param)
    await choose(page, page.getByRole('textbox', { name: 'Alternatif', exact: true }), alternative)
    await choose(page, page.getByRole('textbox', { name: 'Tahun', exact: true }), year || 'Semua tahun')
    await page.getByRole('button', { name: 'Tambah', exact: true }).click()
    const inputs = registry.locator('tbody tr').last().locator('input:not([type=hidden])')
    await inputs.nth(0).fill(value)
    await inputs.nth(1).fill(unit)
    await inputs.nth(3).fill(source)
  }

  await add(PARAMETERS[0])
  await shot(page, '08-ekonomi-tambah-parameter', registry)
  for (const row of PARAMETERS.slice(1)) await add(row)
  await shot(page, '09-ekonomi-registri', registry)

  await api(page, 'PUT', '/econ/parameters/', () =>
    page.getByRole('button', { name: 'Simpan Parameter' }).click(),
  )
  const computed = await api(page, 'POST', '/econ/compute/', () =>
    page.getByRole('button', { name: 'Hitung', exact: true }).click(),
  )
  await record('initial', 'deterministic', computed)
  await shot(page, '10-ekonomi-hasil', card(page, 'Hasil Deterministik (Cost-Utility)'))
}

// ── Menu 3: BIA ───────────────────────────────────────────────────────────

async function bia() {
  const page = await pageFor('hta')
  await openCase(page, 'BIA')
  const computed = await api(page, 'POST', '/econ/bia/compute/', () =>
    page.getByRole('button', { name: 'Hitung BIA' }).click(),
  )
  await record('initial', 'bia', computed)
  await page.waitForTimeout(800)
  await shot(page, '12-bia-hasil', 'full')
}

// ── Menu 4: PSA ───────────────────────────────────────────────────────────

// Package sheet 05, in the order the screen lists the rows.
const DISTRIBUTIONS = [
  { dist: 'Gamma', uncertainty: '10%' }, // drug cost, intervention
  { dist: 'Gamma', uncertainty: '10%' }, // drug cost, comparator
  { dist: 'Beta', p1: '60', p2: '140' }, // probability, intervention
  { dist: 'Beta', p1: '90', p2: '110' }, // probability, comparator
  { dist: 'Gamma', uncertainty: '10%' }, // event cost
  { dist: 'Gamma', uncertainty: '10%' }, // other cost, intervention
  { dist: 'Gamma', uncertainty: '10%' }, // other cost, comparator
  { dist: 'Beta', uncertainty: '0,06' }, // utility, intervention
  { dist: 'Beta', uncertainty: '0,06' }, // utility, comparator
  { dist: 'Beta', uncertainty: '0,03' }, // disutility
]

async function setDistributions(page) {
  const editor = card(page, 'Distribusi Parameter PSA')
  const rows = editor.locator('tbody tr')
  for (const [i, spec] of DISTRIBUTIONS.entries()) {
    const inputs = rows.nth(i).locator('input:not([type=hidden])')
    await choose(page, inputs.nth(0), spec.dist)
    if (spec.uncertainty) {
      await inputs.nth(1).fill(spec.uncertainty)
    } else {
      await inputs.nth(2).fill(spec.p1)
      await inputs.nth(3).fill(spec.p2)
    }
  }
  return editor
}

async function runPSA(page) {
  await page.getByLabel('Iterasi').fill('5000')
  await page.getByLabel('Seed').fill('42')
  const computed = await api(page, 'POST', '/econ/psa/compute/', () =>
    page.getByRole('button', { name: 'Hitung PSA' }).click(),
  )
  await page.waitForTimeout(1200)
  return computed
}

async function psa() {
  const page = await pageFor('hta')
  await openCase(page, 'PSA')
  await shot(page, '13-psa-awal', card(page, 'Distribusi Parameter PSA'))

  const editor = await setDistributions(page)
  await shot(page, '14-psa-distribusi', editor)
  await api(page, 'PUT', '/econ/psa/distributions/', () =>
    page.getByRole('button', { name: 'Simpan Distribusi' }).click(),
  )

  await page.getByLabel('Iterasi').fill('5000')
  await page.getByLabel('Seed').fill('42')
  await shot(page, '15-psa-jalankan', card(page, 'Jalankan PSA'))
  await record('initial', 'psa', await runPSA(page))
  await page.evaluate(() => window.scrollTo(0, 0))
  await shot(page, '16-psa-hasil')
}

// ── Menu 5: EtD ───────────────────────────────────────────────────────────

// Package sheet 12 (source register).
const REFERENCES = [
  ['SRC-DEMO-01 Farmasi demo (sintetis, 2026)', 'Harga ARNI dan ramipril. Harga latihan saja; bukan harga aktual RS/e-catalogue.'],
  ['SRC-DEMO-02 RWE demo (sintetis, 2026)', 'Probabilitas rehospitalisasi 0,30 vs 0,45 per tahun. Bukan data pasien nyata.'],
  ['SRC-DEMO-03 Billing demo (sintetis, 2026)', 'Biaya rehospitalisasi Rp6.000.000/event. Bukan tarif aktual.'],
  ['SRC-DEMO-04 Utility demo (sintetis, 2026)', 'Utility 0,78 dan 0,74; disutility 0,10. Bukan EQ-5D aktual.'],
  ['SRC-DEMO-05 SIMRS demo (sintetis, 2026)', 'Eligible population 200/220/240 pasien/tahun. Bukan volume nyata RS.'],
  ['SRC-DEMO-06 Protokol latihan (asumsi, 2026)', 'Perspektif, horizon, WTP, uptake, seed. Ditentukan untuk tujuan pembelajaran.'],
]

// Package sheet 06. The dashboard asks each domain as a yes/no question on a
// five-point scale, so each package judgement is mapped to the nearest option;
// the mapping is tabulated in the manual. Certainty is "Sedang" throughout,
// the package's one certainty judgement (Moderate). References are attached
// where the package marks local data as used.
const APPRAISALS = [
  ['1. Masalah (Problem)', 'Ya', ['SRC-DEMO-02'],
    'HFrEF dan rehospitalisasi merupakan masalah klinis/biaya yang penting dalam kasus latihan.'],
  ['2. Efek yang Diinginkan', 'Mungkin ya', ['SRC-DEMO-02', 'SRC-DEMO-04'],
    'Intervensi menurunkan event dan meningkatkan QALY dibanding komparator.'],
  ['3. Efek yang Tidak Diinginkan', 'Mungkin ya', [],
    'Risiko dalam latihan dianggap dapat dikelola dengan pemantauan.'],
  ['4. Kepastian Bukti', 'Mungkin ya', ['SRC-DEMO-02'],
    'Masih ada ketidakpastian/residual confounding walaupun arah manfaat favorable.'],
  ['5. Nilai & Preferensi', 'Mungkin ya', [],
    'Outcome dianggap penting bagi pasien, namun variasi preferensi dapat terjadi.'],
  ['6. Penggunaan Sumber Daya', 'Tidak pasti', ['SRC-DEMO-01', 'SRC-DEMO-03'],
    'Value for money favorable pada WTP demo, tetapi affordability meningkat.'],
  ['7. Ekuitas', 'Tidak pasti', [],
    'Jika diadopsi tanpa kriteria, akses dapat dipengaruhi keterbatasan anggaran.'],
  ['8. Kelayakan Implementasi', 'Mungkin ya', [],
    'Implementasi mungkin dilakukan dengan restriction dan monitoring.'],
  ['9. Penerimaan oleh Pemangku Kepentingan', 'Mungkin ya', [],
    'Penerimaan mungkin berbeda antar stakeholder karena biaya.'],
]

async function etd() {
  const hta = await pageFor('hta')
  await openCase(hta, 'EtD (9 domain)')
  for (const [i, [citation, summary]] of REFERENCES.entries()) {
    await hta.getByRole('button', { name: 'Tambah Referensi' }).click()
    const dialog = hta.getByRole('dialog')
    await choose(hta, dialog.getByRole('textbox', { name: 'Jenis' }), 'Protokol institusi')
    await dialog.getByLabel('Sitasi (format bebas)').fill(citation)
    await dialog.getByLabel('Tahun').fill('2026')
    await dialog.getByLabel('Ringkasan bukti').fill(summary)
    if (i === 0) await shot(hta, '17-etd-referensi-form', dialog)
    await api(hta, 'POST', '/references/', () =>
      dialog.getByRole('button', { name: 'Tambah', exact: true }).click(),
    )
  }
  await shot(hta, '18-etd-referensi', card(hta, 'Referensi Bukti'))

  const kft = await pageFor('kft')
  await openCase(kft, 'EtD (9 domain)')
  const domains = card(kft, '9 Domain GRADE EtD')
  for (const [i, [tab, judgement, refs, narrative]] of APPRAISALS.entries()) {
    await domains.getByRole('tab', { name: tab, exact: false }).click()
    const panel = domains.getByRole('tabpanel')
    await panel.getByRole('radio', { name: judgement, exact: true }).check()
    await choose(kft, panel.getByTestId('certainty-select'), 'Sedang')
    for (const ref of refs) {
      await panel.getByRole('textbox', { name: 'Referensi pendukung' }).click()
      await kft.getByRole('option', { name: new RegExp(`^${ref}`) }).locator('visible=true').click()
    }
    await kft.keyboard.press('Escape')
    await panel.getByLabel('Pertimbangan (narasi)').fill(narrative)
    if (i === 0) await shot(kft, '19-etd-domain-1', domains)
    if (i === 5) await shot(kft, '20-etd-domain-6', domains)
    await api(kft, 'POST', '/etd/appraisals/', () =>
      panel.getByRole('button', { name: 'Simpan Penilaian Saya' }).click(),
    )
  }
  await kft.evaluate(() => window.scrollTo(0, 0))
  await kft.waitForTimeout(800)
  await shot(kft, '21-etd-ringkasan', card(kft, 'Ringkasan EtD'))
}

// ── Menu 6: Rekomendasi ───────────────────────────────────────────────────

// Package sheet 07: the access criteria behind "Adopt with criteria-based access".
const CRITERIA = [
  ['Eligibilitas: HFrEF terkonfirmasi', 'Diagnosis HFrEF dikonfirmasi (LVEF ≤40%, NYHA II–IV); memenuhi kriteria klinis lokal.'],
  ['Prescriber: inisiasi oleh spesialis', 'Inisiasi oleh spesialis terkait.'],
  ['Monitoring: tekanan darah, fungsi ginjal, K+', 'Tekanan darah, fungsi ginjal dan kalium dimonitor; review tolerabilitas.'],
  ['Stop/reassess', 'Reassess bila intoleransi/masalah keselamatan atau tidak lagi memenuhi kriteria.'],
]

async function rekomendasi() {
  const sekre = await pageFor('sekre')
  await openCase(sekre, 'Rekomendasi')
  for (const [i, [name, description]] of CRITERIA.entries()) {
    await sekre.getByRole('button', { name: 'Tambah Kriteria' }).click()
    const dialog = sekre.getByRole('dialog')
    await dialog.getByLabel('Nama kriteria').fill(name)
    await dialog.getByLabel('Deskripsi').fill(description)
    // "Terpenuhi" is left unticked: the package lists monitoring and workflow
    // as still to be defined (sheet 06, "Action needed"), so these are
    // conditions of the adoption, not arrangements already in place.
    if (i === 0) await shot(sekre, '24-rekomendasi-kriteria-form', dialog)
    await api(sekre, 'POST', '/cba/', () =>
      dialog.getByRole('button', { name: 'Tambah', exact: true }).click(),
    )
  }
  await shot(sekre, '25-rekomendasi-kriteria', card(sekre, 'Kriteria Akses (CBA)'))

  const hta = await pageFor('hta')
  await openCase(hta, 'Rekomendasi')
  const computed = await api(hta, 'POST', '/recommendation/compute/', () =>
    hta.getByRole('button', { name: 'Hitung Rekomendasi' }).click(),
  )
  await record('initial', 'recommendation', computed)
  await hta.waitForTimeout(800)
  await hta.evaluate(() => window.scrollTo(0, 0))
  await shot(hta, '26-rekomendasi-hasil', card(hta, 'Rekomendasi Akhir'))
}

// Package steps 50 and 53: the decision type and its integrated rationale,
// recorded by the KFT beside the system's colour (round 5 item 3).
const FINAL_DECISION = 'Adopsi dengan kriteria akses (Adopt with criteria-based access)'
const FINAL_REASON =
  'Manfaat klinis dan cost-effectiveness deterministik mendukung, tetapi hasil PSA tidak ' +
  'pasti dan dampak anggaran meningkat. Adopsi dibatasi pada pasien yang memenuhi kriteria akses.'
const FINAL_REASON_REVISED =
  'Harga kontrak baru memperbaiki ICER dan dampak anggaran, tetapi ketidakpastian PSA dan ' +
  'dampak anggaran tetap bermakna. Keputusan tetap adopsi dengan kriteria akses.'

async function recordFinalDecision(page, reason, formShot) {
  const decision = card(page, 'Keputusan Final KFT')
  await choose(page, decision.getByPlaceholder('Pilih keputusan'), FINAL_DECISION)
  await decision.getByRole('textbox', { name: /^Alasan/ }).fill(reason)
  if (formShot) await shot(page, formShot, decision)
  await api(page, 'POST', '/final-decisions/', () =>
    decision.getByRole('button', { name: /Simpan Keputusan Final|Catat Keputusan Baru/ }).click(),
  )
  await page.waitForTimeout(800)
  return decision
}

async function keputusanFinal() {
  const kft = await pageFor('kft')
  await openCase(kft, 'Rekomendasi')
  const decision = await recordFinalDecision(kft, FINAL_REASON, '26b-rekomendasi-keputusan-form')
  await decision.scrollIntoViewIfNeeded()
  await shot(kft, '26c-rekomendasi-keputusan-final', decision)
}

// ── Menu 7: Sign-Off ──────────────────────────────────────────────────────

async function transition(page, label, reason) {
  await page.getByRole('button', { name: 'Tindakan' }).click()
  const item = page.getByRole('menuitem', { name: label, exact: true })
  if (!reason) {
    await api(page, 'POST', '/transition/', () => item.click())
    return
  }
  await item.click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('textbox').fill(reason)
  return dialog
}

async function sign(page) {
  await page.getByRole('button', { name: 'Setujui dengan Sign-Off' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('checkbox').check()
  await dialog.getByLabel('Sandi Anda').fill(PASSWORD)
  return dialog
}

async function signoff() {
  const hta = await pageFor('hta')
  await openCase(hta, 'Sign-Off')
  await shot(hta, '27-signoff-kelengkapan', 'full')
  await hta.evaluate(() => window.scrollTo(0, 0))
  await hta.getByRole('button', { name: 'Tindakan' }).click()
  await shot(hta, '28-signoff-ajukan')
  await hta.keyboard.press('Escape')
  await transition(hta, 'Ajukan untuk Tinjauan')

  const ketua = await pageFor('ketua')
  await openCase(ketua, 'Sign-Off')
  await shot(ketua, '29-signoff-ketua', 'full')
  const dialog = await sign(ketua)
  await shot(ketua, '30-signoff-tanda-tangan', dialog)
  await api(ketua, 'POST', '/approvals/sign/', () =>
    dialog.getByRole('button', { name: 'Setujui & Tanda Tangan' }).click(),
  )
  await ketua.waitForTimeout(800)
  await shot(ketua, '31-signoff-riwayat', card(ketua, 'Riwayat Tanda Tangan'))
}

// ── Menu 8: Brief ─────────────────────────────────────────────────────────

async function brief() {
  const hta = await pageFor('hta')
  await openCase(hta, 'Brief')
  await api(hta, 'POST', '/policy-briefs/', () =>
    hta.getByRole('button', { name: 'Terbitkan Ringkasan' }).click(),
  )
  await hta.waitForTimeout(1000)
  await shot(hta, '33-brief-terbit')
}

// ── Menu 9: Versi ─────────────────────────────────────────────────────────

const REVISION_REASON = 'Pembaruan harga kontrak demo'

async function versi() {
  const ketua = await pageFor('ketua')
  await openCase(ketua, 'Versi')
  await shot(ketua, '34-versi-awal')

  // Package step 55: after approval the decision is frozen. It is locked as v1.0.
  await ketua.evaluate(() => window.scrollTo(0, 0))
  await ketua.getByRole('button', { name: 'Tindakan' }).click()
  await shot(ketua, '45-versi-kunci')
  await ketua.keyboard.press('Escape')
  await transition(ketua, 'Kunci Keputusan')

  // Package steps 58-59: ARNI falls from Rp1.200.000 to Rp1.100.000 per month,
  // made as a new version with a recorded reason; v1.0 is left as it is.
  await openCase(ketua)
  const reasonDialog = await transition(ketua, 'Buat Revisi (Versi Baru)', REVISION_REASON)
  await shot(ketua, '35-versi-buat-revisi', reasonDialog)
  await api(ketua, 'POST', '/transition/', () =>
    reasonDialog.getByRole('button', { name: 'Lanjutkan' }).click(),
  )
  await ketua.waitForTimeout(800)
  await ketua.evaluate(() => window.scrollTo(0, 0))
  await shot(ketua, '35b-versi-revisi-berjalan')

  const hta = await pageFor('hta')
  await openCase(hta, 'Analisis Ekonomi')
  const registry = card(hta, 'Registri Parameter')
  const arni = registry
    .locator('tbody tr', { hasText: 'Biaya obat per pasien per tahun' })
    .filter({ hasText: 'Intervensi' })
  await arni.locator('input:not([type=hidden])').first().fill('13200000')
  await arni.scrollIntoViewIfNeeded()
  await shot(hta, '36-versi-harga-baru', arni)
  const [recomputed] = await Promise.all([
    hta.waitForResponse((r) => r.url().includes('/econ/compute/') && r.ok(), { timeout: 60_000 }),
    hta.getByRole('button', { name: 'Simpan & Hitung' }).click(),
  ])
  await record('revised', 'deterministic', recomputed)
  await hta.waitForTimeout(800)
  await hta.evaluate(() => window.scrollTo(0, 0))
  await shot(hta, '37-versi-hasil-baru', card(hta, 'Hasil Deterministik (Cost-Utility)'))

  await openCase(hta, 'BIA')
  const biaAgain = await api(hta, 'POST', '/econ/bia/compute/', () =>
    hta.getByRole('button', { name: 'Hitung BIA' }).click(),
  )
  await record('revised', 'bia', biaAgain)
  await hta.waitForTimeout(800)
  await shot(hta, '38-versi-bia-baru', card(hta, 'Dampak Anggaran (dengan cost offset)'))

  // The gamma for ARNI still has the old mean; the PSA tab says so.
  await openCase(hta, 'PSA')
  await hta.waitForTimeout(800)
  await shot(hta, '39-versi-psa-peringatan', 'full')
  const editor = card(hta, 'Distribusi Parameter PSA')
  await editor.locator('tbody tr').first().locator('input:not([type=hidden])').nth(1).fill('10%')
  await api(hta, 'PUT', '/econ/psa/distributions/', () =>
    hta.getByRole('button', { name: 'Simpan Distribusi' }).click(),
  )
  await record('revised', 'psa', await runPSA(hta))
  await hta.evaluate(() => window.scrollTo(0, 0))
  await shot(hta, '40-versi-psa-baru', card(hta, 'Analisis Sensitivitas Probabilistik (PSA)'))

  await openCase(hta, 'Rekomendasi')
  await hta.waitForTimeout(800)
  await shot(hta, '41-versi-rekomendasi-usang')
  const recoAgain = await api(hta, 'POST', '/recommendation/compute/', () =>
    hta.getByRole('button', { name: 'Hitung Rekomendasi' }).click(),
  )
  await record('revised', 'recommendation', recoAgain)
  await hta.waitForTimeout(800)
  await hta.evaluate(() => window.scrollTo(0, 0))
  await shot(hta, '42-versi-rekomendasi-baru', card(hta, 'Rekomendasi Akhir'))

  // The recommendation was recomputed for the new version, so the KFT records
  // its decision again; the v1.0 decision stays in the history.
  const kft = await pageFor('kft')
  await openCase(kft, 'Rekomendasi')
  const decision = await recordFinalDecision(kft, FINAL_REASON_REVISED)
  await decision.scrollIntoViewIfNeeded()
  await shot(kft, '42b-versi-keputusan-ulang', decision)

  await openCase(hta)
  await transition(hta, 'Ajukan untuk Tinjauan')

  await openCase(ketua, 'Sign-Off')
  const signDialog = await sign(ketua)
  await api(ketua, 'POST', '/approvals/sign/', () =>
    signDialog.getByRole('button', { name: 'Setujui & Tanda Tangan' }).click(),
  )
  await ketua.waitForTimeout(800)
  await shot(ketua, '43-versi-tanda-tangan-ulang', card(ketua, 'Riwayat Tanda Tangan'))

  await openCase(hta, 'Brief')
  await api(hta, 'POST', '/policy-briefs/', () =>
    hta.getByRole('button', { name: 'Buat Versi Baru' }).click(),
  )
  await hta.waitForTimeout(1000)
  await shot(hta, '44-versi-brief-v2', card(hta, 'Riwayat Versi'))

  await openCase(ketua)
  await transition(ketua, 'Kunci Keputusan')

  await openCase(ketua, 'Versi')
  await ketua.waitForTimeout(800)
  await shot(ketua, '46-versi-riwayat', 'full')
  await versiDetail()
}

/** Read-only: what a locked version shows. Safe to re-run on a locked case. */
async function versiDetail() {
  const ketua = await pageFor('ketua')
  await openCase(ketua, 'Versi')
  await ketua.getByRole('cell', { name: 'v1.1', exact: true }).click()
  const drawer = ketua.getByRole('dialog')
  await drawer.getByRole('tab', { name: 'Timeline Audit' }).waitFor()
  const reasonEntry = drawer.locator('.mantine-Card-root', { hasText: REVISION_REASON })
  await reasonEntry.scrollIntoViewIfNeeded()
  await shot(ketua, '47-versi-timeline', reasonEntry)
  await drawer.getByRole('tab', { name: 'Keadaan Data' }).click()
  // The drawer scrolls inside itself; a tall viewport shows all of it at once.
  await ketua.setViewportSize({ width: 1440, height: 3000 })
  await ketua.waitForTimeout(1200)
  await shot(ketua, '48-versi-keadaan-data', drawer)
  await ketua.setViewportSize({ width: 1440, height: 900 })
  await ketua.keyboard.press('Escape')

  await choose(ketua, ketua.getByRole('textbox', { name: 'Dari versi' }), /^v1\.0 /)
  await choose(ketua, ketua.getByRole('textbox', { name: 'Ke versi' }), /^v1\.1 /)
  await ketua.getByText('Tampilkan Diff').click()
  const diff = ketua.getByRole('dialog')
  await diff.getByText('Perbandingan Versi').waitFor()
  await ketua.setViewportSize({ width: 1440, height: 3000 })
  await ketua.waitForTimeout(1200)
  await shot(ketua, '49-versi-diff', diff)
  await ketua.setViewportSize({ width: 1440, height: 900 })
  await ketua.keyboard.press('Escape')

  const hta = await pageFor('hta')
  await openCase(hta, 'Analisis Ekonomi')
  await hta.waitForTimeout(600)
  await shot(hta, '50-versi-terkunci', card(hta, 'Parameter Model Ekonomi'))
}

/** Round 5 item 5: Admin IT sees the case as metadata only. */
async function adminit() {
  const admin = await pageFor('adminit')
  await admin.goto(`${BASE}/cases/${CASE_ID}`)
  await admin.getByText('Tampilan metadata').waitFor()
  await toasts(admin, false)
  await admin.waitForTimeout(600)
  await shot(admin, '51-admin-it-kasus')
}

// `inputs` captures nothing: it only rewrites results.json from the tables above.
const PHASES = {
  login, ringkasan, ekonomi, bia, psa, etd, rekomendasi, keputusanFinal, signoff, brief, versi,
  versiDetail, adminit,
  inputs: async () => {},
}

const requested = process.argv.slice(2)
// A full run locks v1.0, revises it into v1.1 and locks that, then shows the
// Admin IT view of the finished case.
const FULL_RUN = [
  'login', 'ringkasan', 'ekonomi', 'bia', 'psa', 'etd', 'rekomendasi', 'keputusanFinal',
  'signoff', 'brief', 'versi', 'adminit',
]
const order = requested.length ? requested : FULL_RUN

browser = await chromium.launch()
try {
  for (const name of order) {
    if (!PHASES[name]) throw new Error(`Unknown phase "${name}". Known: ${Object.keys(PHASES).join(', ')}`)
    console.log(name)
    await PHASES[name]()
  }
} finally {
  await browser.close()
}

// The manual's input tables are printed from these, so the document cannot
// drift from what was actually typed.
results.inputs = {
  parameters: PARAMETERS,
  distributions: DISTRIBUTIONS,
  references: REFERENCES,
  appraisals: APPRAISALS,
  criteria: CRITERIA,
  revision_reason: REVISION_REASON,
  final_decision: FINAL_DECISION,
  final_reason: FINAL_REASON,
  final_reason_revised: FINAL_REASON_REVISED,
}
results.build = process.env.MANUAL_BUILD_COMMIT ?? 'lokal'
results.case_id = CASE_ID
fs.writeFileSync(RESULTS_FILE, `${JSON.stringify(results, null, 2)}\n`)
