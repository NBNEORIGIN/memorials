const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchJobs() {
  const res = await fetch(`${API_URL}/api/jobs/`)
  if (!res.ok) throw new Error('Failed to fetch jobs')
  return res.json()
}

export async function fetchJob(jobId: number) {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`)
  if (!res.ok) throw new Error('Failed to fetch job')
  return res.json()
}

export async function uploadOrderFile(file: File, enrich: boolean = true) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_URL}/api/jobs/upload?enrich=${enrich}`, {
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
