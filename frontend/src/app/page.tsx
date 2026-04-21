'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { Upload, Play, Trash2, FileText, CheckCircle, AlertCircle, Clock, Download, Settings, Pencil, Check, X, ChevronDown, ChevronUp, Bug, Send, Crosshair, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, RotateCcw } from 'lucide-react'
import { uploadOrderFiles, generateSvgs, fetchJobs, fetchJob, deleteJob, resetJob, updateJobItem, svgPreviewUrl, svgDownloadUrl, csvDownloadUrl, submitBugReport, fetchCalibration, saveCalibration } from '@/lib/api'

type JobItem = {
  id: number
  order_id: string | null
  order_item_id: string | null
  sku: string
  quantity: number
  colour: string | null
  memorial_type: string | null
  decoration_type: string | null
  theme: string | null
  processor_key: string | null
  graphic: string | null
  line_1: string | null
  line_2: string | null
  line_3: string | null
  image_path: string | null
  svg_path: string | null
  status: string
  error: string | null
}

type Job = {
  id: number
  source: string
  status: string
  filename: string | null
  item_count: number
  created_at: string
  completed_at: string | null
  items: JobItem[]
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  ready: <Clock className="w-4 h-4 text-blue-500" />,
  complete: <CheckCircle className="w-4 h-4 text-green-500" />,
  error: <AlertCircle className="w-4 h-4 text-red-500" />,
  unmatched: <AlertCircle className="w-4 h-4 text-amber-500" />,
  pending: <Clock className="w-4 h-4 text-gray-400" />,
}

const JOB_STATUS_STYLES: Record<string, string> = {
  parsed: 'bg-blue-100 text-blue-700',
  processing: 'bg-yellow-100 text-yellow-700',
  complete: 'bg-green-100 text-green-700',
  partial: 'bg-amber-100 text-amber-700',
  failed: 'bg-red-100 text-red-700',
  pending: 'bg-gray-100 text-gray-600',
}

function EditableCell({ value, onSave, multiline = false }: {
  value: string
  onSave: (v: string) => Promise<void>
  multiline?: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const [saving, setSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null)

  useEffect(() => { setDraft(value) }, [value])
  useEffect(() => { if (editing) inputRef.current?.focus() }, [editing])

  const save = async () => {
    if (draft === value) { setEditing(false); return }
    setSaving(true)
    try {
      await onSave(draft)
      setEditing(false)
    } catch (_e) { setDraft(value) }
    setSaving(false)
  }

  const cancel = () => { setDraft(value); setEditing(false) }

  if (!editing) {
    return (
      <div
        className="group flex items-center gap-1 cursor-pointer min-h-[28px]"
        onClick={() => setEditing(true)}
        title="Click to edit"
      >
        <span className={`text-xs ${value ? 'text-gray-700' : 'text-gray-300'}`}>
          {value || '—'}
        </span>
        <Pencil className="w-3 h-3 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
      </div>
    )
  }

  if (multiline) {
    return (
      <div className="flex flex-col gap-1">
        <textarea
          ref={inputRef as any}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => { if (e.key === 'Escape') cancel() }}
          rows={3}
          className="w-full text-xs border border-indigo-300 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400 resize-none"
          disabled={saving}
        />
        <div className="flex gap-1">
          <button onClick={save} disabled={saving} className="text-green-600 hover:text-green-700"><Check className="w-3.5 h-3.5" /></button>
          <button onClick={cancel} className="text-gray-400 hover:text-gray-600"><X className="w-3.5 h-3.5" /></button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      <input
        ref={inputRef as any}
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') save(); if (e.key === 'Escape') cancel() }}
        className="w-full text-xs border border-indigo-300 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        disabled={saving}
      />
      <button onClick={save} disabled={saving} className="text-green-600 hover:text-green-700"><Check className="w-3.5 h-3.5" /></button>
      <button onClick={cancel} className="text-gray-400 hover:text-gray-600"><X className="w-3.5 h-3.5" /></button>
    </div>
  )
}

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [activeJob, setActiveJob] = useState<Job | null>(null)
  const [uploading, setUploading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedRow, setExpandedRow] = useState<number | null>(null)
  const [bugModalOpen, setBugModalOpen] = useState(false)
  const [bugSending, setBugSending] = useState(false)
  const [bugSent, setBugSent] = useState(false)
  const [calibModalOpen, setCalibModalOpen] = useState(false)
  const [calibX, setCalibX] = useState(0)
  const [calibY, setCalibY] = useState(0)
  const [calibStep, setCalibStep] = useState(0.5)
  const [calibSaving, setCalibSaving] = useState(false)
  const [calibSaved, setCalibSaved] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchJobs().then(setJobs).catch(() => {})
  }, [])

  useEffect(() => {
    if (calibModalOpen) {
      fetchCalibration()
        .then(c => { setCalibX(c.x_mm); setCalibY(c.y_mm); setCalibSaved(false) })
        .catch(() => {})
    }
  }, [calibModalOpen])

  const handleUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setError(null)
    setUploading(true)
    try {
      const fileArray = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.txt'))
      if (fileArray.length === 0) { setError('No .txt files selected'); setUploading(false); return }
      const job = await uploadOrderFiles(fileArray)
      setActiveJob(job)
      const updatedJobs = await fetchJobs()
      setJobs(updatedJobs)
    } catch (e: any) {
      setError(e.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [])

  const handleGenerate = useCallback(async () => {
    if (!activeJob) return
    setError(null)
    setGenerating(true)
    try {
      const result = await generateSvgs(activeJob.id)
      setActiveJob(result)
      const updatedJobs = await fetchJobs()
      setJobs(updatedJobs)
    } catch (e: any) {
      setError(e.message || 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }, [activeJob])

  const handleReset = useCallback(async () => {
    if (!activeJob) return
    setError(null)
    try {
      const result = await resetJob(activeJob.id)
      setActiveJob(result)
      const updatedJobs = await fetchJobs()
      setJobs(updatedJobs)
    } catch (e: any) {
      setError(e.message || 'Reset failed')
    }
  }, [activeJob])

  const handleDelete = useCallback(async (jobId: number) => {
    try {
      await deleteJob(jobId)
      if (activeJob?.id === jobId) setActiveJob(null)
      const updatedJobs = await fetchJobs()
      setJobs(updatedJobs)
    } catch {}
  }, [activeJob])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    handleUpload(e.dataTransfer.files)
  }, [handleUpload])

  const handleItemUpdate = useCallback(async (itemId: number, field: string, value: string) => {
    await updateJobItem(itemId, { [field]: value })
    if (activeJob) {
      const refreshed = await fetchJob(activeJob.id)
      setActiveJob(refreshed)
    }
  }, [activeJob])

  const [statusFilter, setStatusFilter] = useState<string>('all')
  const readyCount = activeJob?.items.filter(i => i.status === 'ready').length || 0
  const completeCount = activeJob?.items.filter(i => i.status === 'complete').length || 0
  const errorCount = activeJob?.items.filter(i => i.status === 'error' || i.status === 'unmatched').length || 0
  const filteredItems = activeJob?.items.filter(i =>
    statusFilter === 'all' ? true : i.status === statusFilter
  ) || []

  // Compute unique print sheets
  const sheets = new Map<string, {id: number; path: string; items: JobItem[]}>()
  if (activeJob) {
    activeJob.items.forEach(item => {
      if (item.status === 'complete' && item.svg_path) {
        const existing = sheets.get(item.svg_path)
        if (existing) { existing.items.push(item) }
        else { sheets.set(item.svg_path, { id: item.id, path: item.svg_path, items: [item] }) }
      }
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-[1440px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-base">M</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 leading-tight">NBNE Memorials</h1>
              <p className="text-[11px] text-gray-400">Order Processing &amp; SVG Generation</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCalibModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              title="Print calibration — adjust global offset for all memorials"
            >
              <Crosshair className="w-4 h-4" />
              Calibration
            </button>
            <button
              onClick={() => { setBugModalOpen(true); setBugSent(false) }}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Report a bug"
            >
              <Bug className="w-4 h-4" />
              Report Bug
            </button>
            <a href="/memorials/admin" className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
              <Settings className="w-4 h-4" />
              Admin
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-[1440px] mx-auto px-6 py-6">
        <div className="flex gap-6">

          {/* Left sidebar — Jobs list */}
          <div className="w-64 flex-shrink-0">
            <div className="sticky top-6">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Recent Jobs</h2>
            <div className="space-y-1.5">
              {jobs.length === 0 && (
                <p className="text-sm text-gray-400 py-4 text-center">No jobs yet</p>
              )}
              {jobs.map(job => (
                <button
                  key={job.id}
                  onClick={() => fetchJob(job.id).then(setActiveJob).catch(() => {})}
                  className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors ${
                    activeJob?.id === job.id
                      ? 'border-indigo-300 bg-indigo-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 truncate">
                      {job.filename || `Job #${job.id}`}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDelete(job.id) }}
                      className="text-gray-300 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${JOB_STATUS_STYLES[job.status] || 'bg-gray-100 text-gray-600'}`}>
                      {job.status}
                    </span>
                    <span className="text-xs text-gray-400">{job.item_count} items</span>
                  </div>
                </button>
              ))}
            </div>
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0 space-y-5">

            {/* Drop zone */}
            <div
              onDragEnter={(e) => { e.preventDefault(); setDragActive(true) }}
              onDragLeave={(e) => { e.preventDefault(); setDragActive(false) }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                dragActive
                  ? 'border-indigo-400 bg-indigo-50'
                  : 'border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt"
                multiple
                className="hidden"
                onChange={(e) => handleUpload(e.target.files)}
              />
              <Upload className={`w-8 h-8 mx-auto mb-2 ${dragActive ? 'text-indigo-500' : 'text-gray-400'}`} />
              <p className="text-sm font-medium text-gray-700">
                {uploading ? 'Uploading & downloading personalisation data...' : 'Drop Amazon order .txt files here'}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">Drop multiple files from different accounts — they&apos;ll be merged into one job</p>
            </div>

            {/* Error banner */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Active job */}
            {activeJob && (
              <>
                {/* Job header + actions */}
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                  <div className="px-5 py-4 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-base font-bold text-gray-900">
                          {activeJob.filename || `Job #${activeJob.id}`}
                        </h2>
                        <p className="text-[11px] text-gray-400 mt-0.5">
                          {activeJob.item_count} items &middot; {activeJob.source} &middot; {new Date(activeJob.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={handleGenerate}
                          disabled={generating || readyCount === 0}
                          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                        >
                          <Play className="w-4 h-4" />
                          {generating ? 'Generating...' : 'Generate SVGs'}
                        </button>
                        {completeCount > 0 && (
                          <button
                            onClick={handleReset}
                            className="flex items-center gap-2 px-3 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            Re-generate
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Filter pills */}
                    <div className="flex gap-2 mt-3">
                      <button onClick={() => setStatusFilter('all')} className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${statusFilter === 'all' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                        All ({activeJob.items.length})
                      </button>
                      {readyCount > 0 && (
                        <button onClick={() => setStatusFilter('ready')} className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${statusFilter === 'ready' ? 'bg-blue-600 text-white' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}`}>
                          Ready ({readyCount})
                        </button>
                      )}
                      {completeCount > 0 && (
                        <button onClick={() => setStatusFilter('complete')} className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${statusFilter === 'complete' ? 'bg-green-600 text-white' : 'bg-green-50 text-green-700 hover:bg-green-100'}`}>
                          Complete ({completeCount})
                        </button>
                      )}
                      {errorCount > 0 && (
                        <button onClick={() => setStatusFilter('unmatched')} className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${statusFilter === 'unmatched' ? 'bg-amber-600 text-white' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'}`}>
                          Unmatched ({errorCount})
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Items table — editable */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50/80 border-b border-gray-200">
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide w-8">#</th>
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide w-24">Status</th>
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide">SKU</th>
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide">Type / Colour</th>
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide">Graphic</th>
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide">Line 1</th>
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide">Line 2</th>
                          <th className="text-left py-2.5 px-3 text-[11px] font-semibold text-gray-500 uppercase tracking-wide w-8"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredItems.map((item, idx) => (
                          <>
                            <tr
                              key={item.id}
                              className={`border-b border-gray-100 hover:bg-gray-50/50 transition-colors ${
                                item.status === 'error' || item.status === 'unmatched'
                                  ? 'bg-amber-50/40'
                                  : item.status === 'complete' ? 'bg-green-50/20' : ''
                              }`}
                            >
                              <td className="py-2.5 px-3 text-gray-400 text-xs font-mono">{idx + 1}</td>
                              <td className="py-2.5 px-3">
                                <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full ${
                                  item.status === 'complete' ? 'bg-green-100 text-green-700' :
                                  item.status === 'ready' ? 'bg-blue-100 text-blue-700' :
                                  item.status === 'unmatched' ? 'bg-amber-100 text-amber-700' :
                                  item.status === 'error' ? 'bg-red-100 text-red-700' :
                                  'bg-gray-100 text-gray-600'
                                }`}>
                                  {STATUS_ICON[item.status] || STATUS_ICON.pending}
                                  {item.status}
                                </span>
                              </td>
                              <td className="py-2.5 px-3">
                                <span className="font-mono text-xs text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded">{item.sku}</span>
                              </td>
                              <td className="py-2.5 px-3">
                                <div className="text-xs text-gray-700">{item.memorial_type || '—'}</div>
                                {item.colour && <div className="text-[11px] text-gray-400 mt-0.5">{item.colour}</div>}
                              </td>
                              <td className="py-2.5 px-3 max-w-[140px]">
                                <EditableCell
                                  value={item.graphic || ''}
                                  onSave={v => handleItemUpdate(item.id, 'graphic', v)}
                                />
                              </td>
                              <td className="py-2.5 px-3 max-w-[160px]">
                                <EditableCell
                                  value={item.line_1 || ''}
                                  onSave={v => handleItemUpdate(item.id, 'line_1', v)}
                                />
                              </td>
                              <td className="py-2.5 px-3 max-w-[160px]">
                                <EditableCell
                                  value={item.line_2 || ''}
                                  onSave={v => handleItemUpdate(item.id, 'line_2', v)}
                                />
                              </td>
                              <td className="py-2.5 px-3">
                                <button
                                  onClick={() => setExpandedRow(expandedRow === item.id ? null : item.id)}
                                  className="text-gray-300 hover:text-gray-600 transition-colors"
                                >
                                  {expandedRow === item.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                </button>
                              </td>
                            </tr>
                            {expandedRow === item.id && (
                              <tr key={`${item.id}-expanded`} className="bg-gray-50/70 border-b border-gray-100">
                                <td colSpan={8} className="px-5 py-4">
                                  <div className="grid grid-cols-3 gap-6 text-xs">
                                    <div>
                                      <label className="text-gray-400 font-semibold uppercase text-[10px] tracking-wide">Line 3</label>
                                      <div className="mt-1">
                                        <EditableCell
                                          value={item.line_3 || ''}
                                          onSave={v => handleItemUpdate(item.id, 'line_3', v)}
                                          multiline
                                        />
                                      </div>
                                    </div>
                                    <div>
                                      <label className="text-gray-400 font-semibold uppercase text-[10px] tracking-wide">Processor</label>
                                      <p className="text-xs font-mono text-gray-600 mt-1">{item.processor_key || '—'}</p>
                                      {item.error && (
                                        <p className="text-xs text-red-600 mt-1.5 bg-red-50 rounded px-2 py-1">{item.error}</p>
                                      )}
                                    </div>
                                    <div>
                                      <label className="text-gray-400 font-semibold uppercase text-[10px] tracking-wide">Order</label>
                                      <p className="text-xs text-gray-600 mt-1">{item.order_id || '—'}</p>
                                      <p className="text-[11px] text-gray-400">{item.order_item_id || '—'}</p>
                                      <label className="text-gray-400 font-semibold uppercase text-[10px] tracking-wide mt-2 block">Decoration</label>
                                      <p className="text-xs text-gray-600 mt-0.5">{item.decoration_type || '—'}</p>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Print sheets — direct download per sheet */}
                {sheets.size > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-bold text-gray-800">Print Sheets ({sheets.size})</h3>
                      <span className="text-[11px] text-gray-400">Click image to open full size</span>
                    </div>
                    <div className="space-y-4">
                      {Array.from(sheets.values()).map(sheet => {
                        const fname = sheet.path.split(/[\\/]/).pop() || 'sheet.svg'
                        return (
                          <div key={sheet.path} className="border border-gray-200 rounded-xl overflow-hidden bg-gray-50 shadow-sm">
                            <a href={svgPreviewUrl(sheet.id)} target="_blank" rel="noopener noreferrer" className="block hover:opacity-95 transition-opacity">
                              <img src={svgPreviewUrl(sheet.id)} alt="Print sheet" className="w-full h-auto" />
                            </a>
                            <div className="px-4 py-3 border-t border-gray-200 bg-white flex items-center justify-between">
                              <div>
                                <p className="text-xs font-mono text-gray-600">{fname}</p>
                                <p className="text-[11px] text-gray-400 mt-0.5">{sheet.items.length} item{sheet.items.length !== 1 ? 's' : ''} on this sheet</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <a
                                  href={csvDownloadUrl(sheet.id)}
                                  download={fname.replace('.svg', '.csv')}
                                  className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 text-gray-600 text-xs font-medium rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                  <FileText className="w-3.5 h-3.5" />
                                  CSV
                                </a>
                                <a
                                  href={svgDownloadUrl(sheet.id)}
                                  download={fname}
                                  className="flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white text-xs font-semibold rounded-lg hover:bg-green-700 transition-colors shadow-sm"
                                >
                                  <Download className="w-4 h-4" />
                                  Download SVG
                                </a>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Empty state */}
            {!activeJob && jobs.length === 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-700 mb-1">No orders yet</h3>
                <p className="text-sm text-gray-400">Drop an Amazon order .txt file above to get started</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Calibration Modal */}
      {calibModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setCalibModalOpen(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-indigo-50">
              <div className="flex items-center gap-2">
                <Crosshair className="w-5 h-5 text-indigo-600" />
                <h2 className="text-base font-bold text-gray-900">Print Calibration</h2>
              </div>
              <button onClick={() => setCalibModalOpen(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="px-6 py-5 space-y-5">
              <p className="text-xs text-gray-500 leading-relaxed">
                Global offset applied to all memorial designs. Use this to compensate for
                printer/cutter alignment. Negative X shifts left; positive X shifts right.
                Negative Y shifts up; positive Y shifts down. Takes effect on next generate.
              </p>

              {/* Crosshair controls */}
              <div className="flex items-center justify-center py-3">
                <div className="grid grid-cols-3 grid-rows-3 gap-2 w-48">
                  <div />
                  <button
                    type="button"
                    onClick={() => setCalibY(y => +(y - calibStep).toFixed(2))}
                    className="w-14 h-14 flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
                    title={`Up ${calibStep}mm`}
                  >
                    <ArrowUp className="w-5 h-5 text-gray-600" />
                  </button>
                  <div />
                  <button
                    type="button"
                    onClick={() => setCalibX(x => +(x - calibStep).toFixed(2))}
                    className="w-14 h-14 flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
                    title={`Left ${calibStep}mm`}
                  >
                    <ArrowLeft className="w-5 h-5 text-gray-600" />
                  </button>
                  <div className="w-14 h-14 flex items-center justify-center bg-indigo-600 rounded-lg text-white">
                    <Crosshair className="w-5 h-5" />
                  </div>
                  <button
                    type="button"
                    onClick={() => setCalibX(x => +(x + calibStep).toFixed(2))}
                    className="w-14 h-14 flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
                    title={`Right ${calibStep}mm`}
                  >
                    <ArrowRight className="w-5 h-5 text-gray-600" />
                  </button>
                  <div />
                  <button
                    type="button"
                    onClick={() => setCalibY(y => +(y + calibStep).toFixed(2))}
                    className="w-14 h-14 flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
                    title={`Down ${calibStep}mm`}
                  >
                    <ArrowDown className="w-5 h-5 text-gray-600" />
                  </button>
                  <div />
                </div>
              </div>

              {/* Numeric inputs */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">X offset (mm)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={calibX}
                    onChange={e => setCalibX(parseFloat(e.target.value) || 0)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Y offset (mm)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={calibY}
                    onChange={e => setCalibY(parseFloat(e.target.value) || 0)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Step size (mm)</label>
                <select
                  value={calibStep}
                  onChange={e => setCalibStep(parseFloat(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  <option value={0.1}>0.1mm (fine)</option>
                  <option value={0.5}>0.5mm (default)</option>
                  <option value={1.0}>1.0mm</option>
                  <option value={2.0}>2.0mm (coarse)</option>
                </select>
              </div>

              {calibSaved && (
                <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg">
                  <CheckCircle className="w-4 h-4" />
                  Saved. Takes effect on next generate.
                </div>
              )}

              <div className="flex justify-between gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => { setCalibX(0); setCalibY(0) }}
                  className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Reset to 0,0"
                >
                  <RotateCcw className="w-4 h-4" />
                  Reset
                </button>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setCalibModalOpen(false)}
                    className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Close
                  </button>
                  <button
                    type="button"
                    disabled={calibSaving}
                    onClick={async () => {
                      setCalibSaving(true)
                      setCalibSaved(false)
                      try {
                        await saveCalibration({ x_mm: calibX, y_mm: calibY })
                        setCalibSaved(true)
                      } catch (err: any) {
                        alert(err.message || 'Failed to save')
                      } finally {
                        setCalibSaving(false)
                      }
                    }}
                    className="flex items-center gap-2 px-5 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
                  >
                    <Check className="w-4 h-4" />
                    {calibSaving ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bug Report Modal */}
      {bugModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setBugModalOpen(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-red-50">
              <div className="flex items-center gap-2">
                <Bug className="w-5 h-5 text-red-500" />
                <h2 className="text-base font-bold text-gray-900">Report a Bug</h2>
              </div>
              <button onClick={() => setBugModalOpen(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            {bugSent ? (
              <div className="px-6 py-10 text-center">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                <h3 className="text-lg font-semibold text-gray-900">Bug Report Sent</h3>
                <p className="text-sm text-gray-500 mt-1">Emailed to Toby, Jo &amp; Gabby. We&apos;ll look into it.</p>
                <button onClick={() => setBugModalOpen(false)} className="mt-5 px-5 py-2 bg-gray-800 text-white text-sm font-medium rounded-lg hover:bg-gray-900 transition-colors">Close</button>
              </div>
            ) : (
              <form
                className="px-6 py-5 space-y-4"
                onSubmit={async (e) => {
                  e.preventDefault()
                  const form = e.target as HTMLFormElement
                  const data = new FormData(form)
                  setBugSending(true)
                  try {
                    await submitBugReport({
                      subject: data.get('subject') as string,
                      description: data.get('description') as string,
                      steps_to_reproduce: data.get('steps') as string,
                      reporter: data.get('reporter') as string,
                      page: window.location.href,
                      job_id: activeJob?.id ?? null,
                    })
                    setBugSent(true)
                  } catch (err: any) {
                    alert(err.message || 'Failed to send')
                  } finally {
                    setBugSending(false)
                  }
                }}
              >
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Your Name</label>
                  <input name="reporter" required className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-red-400" placeholder="e.g. Jo" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Subject</label>
                  <input name="subject" required className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-red-400" placeholder="Brief description of the issue" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">What went wrong?</label>
                  <textarea name="description" required rows={4} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-red-400 resize-none" placeholder="Describe the bug in detail — what did you expect to happen vs what actually happened?" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Steps to reproduce <span className="font-normal text-gray-400">(optional)</span></label>
                  <textarea name="steps" rows={3} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-red-400 resize-none" placeholder="1. Upload file X&#10;2. Click Generate&#10;3. See error..." />
                </div>
                {activeJob && (
                  <p className="text-xs text-gray-400">Active job #{activeJob.id} ({activeJob.filename}) will be included in the report.</p>
                )}
                <div className="flex justify-end gap-2 pt-2">
                  <button type="button" onClick={() => setBugModalOpen(false)} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">Cancel</button>
                  <button type="submit" disabled={bugSending} className="flex items-center gap-2 px-5 py-2 bg-red-600 text-white text-sm font-semibold rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors shadow-sm">
                    <Send className="w-4 h-4" />
                    {bugSending ? 'Sending...' : 'Send Report'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
