const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchJobs() {
  const res = await fetch(`${API_URL}/api/jobs/`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch jobs')
  return res.json()
}

export async function fetchJob(jobId: number) {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch job')
  return res.json()
}

export async function uploadOrderFiles(files: File[]) {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  const res = await fetch(`${API_URL}/api/jobs/upload-multi?enrich=true`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function generateSvgs(jobId: number) {
  const res = await fetch(`${API_URL}/api/generate/${jobId}`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Generation failed')
  }
  return res.json()
}

export async function deleteJob(jobId: number) {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
}

export async function fetchSkuMappings() {
  const res = await fetch(`${API_URL}/api/skus/`)
  if (!res.ok) throw new Error('Failed to fetch SKU mappings')
  return res.json()
}

export async function fetchColours() {
  const res = await fetch(`${API_URL}/api/skus/colours`)
  if (!res.ok) throw new Error('Failed to fetch colours')
  return res.json()
}

export async function fetchMemorialTypes() {
  const res = await fetch(`${API_URL}/api/skus/memorial-types`)
  if (!res.ok) throw new Error('Failed to fetch memorial types')
  return res.json()
}

export async function fetchProcessors() {
  const res = await fetch(`${API_URL}/api/skus/processors`)
  if (!res.ok) throw new Error('Failed to fetch processors')
  return res.json()
}

export async function resetJob(jobId: number) {
  const res = await fetch(`${API_URL}/api/generate/reset/${jobId}`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Reset failed')
  }
  return res.json()
}

export async function updateJobItem(itemId: number, fields: { graphic?: string; line_1?: string; line_2?: string; line_3?: string }) {
  const res = await fetch(`${API_URL}/api/jobs/items/${itemId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Update failed')
  }
  return res.json()
}

export function svgPreviewUrl(itemId: number) {
  return `${API_URL}/api/generate/svg/${itemId}`
}

export function svgDownloadUrl(itemId: number) {
  return `${API_URL}/api/generate/svg/${itemId}`
}

export function csvDownloadUrl(itemId: number) {
  return `${API_URL}/api/generate/csv/${itemId}`
}

export function downloadAllUrl(jobId: number) {
  return `${API_URL}/api/generate/download/${jobId}`
}

export async function deleteSkuMapping(mappingId: number) {
  const res = await fetch(`${API_URL}/api/skus/${mappingId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
}

export async function updateSkuMapping(mappingId: number, data: Record<string, any>) {
  const res = await fetch(`${API_URL}/api/skus/${mappingId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Update failed')
  }
  return res.json()
}

export async function importSkuCsv(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_URL}/api/skus/import-csv`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Import failed')
  }
  return res.json()
}

export async function fetchDecorationTypes() {
  const res = await fetch(`${API_URL}/api/skus/decoration-types`)
  if (!res.ok) throw new Error('Failed to fetch decoration types')
  return res.json()
}

export async function fetchThemes() {
  const res = await fetch(`${API_URL}/api/skus/themes`)
  if (!res.ok) throw new Error('Failed to fetch themes')
  return res.json()
}

// ── Cell Layouts ──

export async function fetchLayouts() {
  const res = await fetch(`${API_URL}/api/layouts/`)
  if (!res.ok) throw new Error('Failed to fetch layouts')
  return res.json()
}

export async function fetchLayout(processorKey: string) {
  const res = await fetch(`${API_URL}/api/layouts/${processorKey}`)
  if (!res.ok) throw new Error('Layout not found')
  return res.json()
}

export async function fetchLayoutDefaults(processorKey: string) {
  const res = await fetch(`${API_URL}/api/layouts/defaults/${processorKey}`)
  if (!res.ok) throw new Error('Failed to fetch defaults')
  return res.json()
}

export async function saveLayout(
  processorKey: string,
  data: Record<string, any>,
  isNew: boolean,
  layoutId?: number,
  sku?: string | null,
) {
  const url = isNew
    ? `${API_URL}/api/layouts/`
    : `${API_URL}/api/layouts/${layoutId}`
  const method = isNew ? 'POST' : 'PUT'
  const body = isNew
    ? { processor_key: processorKey, ...(sku ? { sku } : {}), ...data }
    : data
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Save failed')
  }
  return res.json()
}

export async function deleteLayout(layoutId: number) {
  const res = await fetch(`${API_URL}/api/layouts/${layoutId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
}

export async function submitBugReport(report: {
  subject: string
  description: string
  page?: string
  job_id?: number | null
  item_id?: number | null
  steps_to_reproduce?: string
  reporter?: string
}) {
  const res = await fetch(`${API_URL}/api/bugreport/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(report),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to submit bug report')
  }
  return res.json()
}

export function layoutPreviewUrl(processorKey: string, params: Record<string, any>) {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') {
      qs.set(k, String(v))
    }
  }
  return `${API_URL}/api/layouts/preview/${processorKey}?${qs.toString()}`
}
