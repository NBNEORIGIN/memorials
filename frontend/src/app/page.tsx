'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { Upload, Play, Trash2, FileText, CheckCircle, AlertCircle, Clock, Download, ChevronDown, ChevronUp, Settings } from 'lucide-react'
import { uploadOrderFile, generateSvgs, fetchJobs, deleteJob, svgPreviewUrl, downloadAllUrl } from '@/lib/api'

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

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [activeJob, setActiveJob] = useState<Job | null>(null)
  const [uploading, setUploading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [enrich, setEnrich] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchJobs().then(setJobs).catch(() => {})
  }, [])

  const handleUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setError(null)
    setUploading(true)
    try {
      let lastJob: Job | null = null
      for (let i = 0; i < files.length; i++) {
        const job = await uploadOrderFile(files[i], enrich)
        lastJob = job
      }
      if (lastJob) {
        setActiveJob(lastJob)
      }
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

  const readyCount = activeJob?.items.filter(i => i.status === 'ready').length || 0
  const completeCount = activeJob?.items.filter(i => i.status === 'complete').length || 0
  const errorCount = activeJob?.items.filter(i => i.status === 'error' || i.status === 'unmatched').length || 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">NBNE Memorials</h1>
              <p className="text-xs text-gray-500">Order Processing & SVG Generation</p>
            </div>
          </div>
          <a href="/admin" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700">
            <Settings className="w-4 h-4" />
            Admin
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">

          {/* Left sidebar — Jobs list */}
          <div className="col-span-3">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">Recent Jobs</h2>
            <div className="space-y-2">
              {jobs.length === 0 && (
                <p className="text-sm text-gray-400 py-4 text-center">No jobs yet</p>
              )}
              {jobs.map(job => (
                <button
                  key={job.id}
                  onClick={() => setActiveJob(job)}
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

          {/* Main content */}
          <div className="col-span-9 space-y-6">

            {/* Drop zone */}
            <div
              onDragEnter={(e) => { e.preventDefault(); setDragActive(true) }}
              onDragLeave={(e) => { e.preventDefault(); setDragActive(false) }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
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
              <Upload className={`w-10 h-10 mx-auto mb-3 ${dragActive ? 'text-indigo-500' : 'text-gray-400'}`} />
              <p className="text-sm font-medium text-gray-700">
                {uploading ? 'Uploading & processing...' : 'Drop Amazon order .txt files here'}
              </p>
              <p className="text-xs text-gray-400 mt-1">or click to browse</p>
            </div>
            <div className="flex items-center gap-2 -mt-3">
              <input type="checkbox" id="enrich" checked={enrich} onChange={e => { e.stopPropagation(); setEnrich(e.target.checked) }}
                className="rounded border-gray-300" />
              <label htmlFor="enrich" className="text-xs text-gray-500 select-none cursor-pointer" onClick={e => e.stopPropagation()}>
                Download personalisation data (graphics, text lines, photos from Amazon ZIPs)
              </label>
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
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-base font-semibold text-gray-900">
                        {activeJob.filename || `Job #${activeJob.id}`}
                      </h2>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {activeJob.item_count} items &middot; {activeJob.source} &middot; {new Date(activeJob.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-blue-600">{readyCount} ready</span>
                        <span className="text-green-600">{completeCount} done</span>
                        {errorCount > 0 && <span className="text-red-600">{errorCount} errors</span>}
                      </div>
                      <button
                        onClick={handleGenerate}
                        disabled={generating || readyCount === 0}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        {generating ? 'Generating...' : 'Generate SVGs'}
                      </button>
                      {completeCount > 0 && (
                        <a
                          href={downloadAllUrl(activeJob.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
                        >
                          <Download className="w-4 h-4" />
                          Download ZIP
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Items table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100">
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">#</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Status</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">SKU</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Type</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Colour</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Deco</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Graphic</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Line 1</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Line 2</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Processor</th>
                          <th className="text-left py-2 px-2 text-xs font-medium text-gray-400 uppercase">Preview</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeJob.items.map((item, idx) => (
                          <tr
                            key={item.id}
                            className={`border-b border-gray-50 hover:bg-gray-50 ${
                              item.status === 'error' || item.status === 'unmatched' ? 'bg-red-50/50' : ''
                            }`}
                          >
                            <td className="py-2 px-2 text-gray-400">{idx + 1}</td>
                            <td className="py-2 px-2">
                              <div className="flex items-center gap-1">
                                {STATUS_ICON[item.status] || STATUS_ICON.pending}
                                <span className="text-xs">{item.status}</span>
                              </div>
                            </td>
                            <td className="py-2 px-2 font-mono text-xs text-gray-700">{item.sku}</td>
                            <td className="py-2 px-2 text-gray-600">{item.memorial_type || '—'}</td>
                            <td className="py-2 px-2 text-gray-600">{item.colour || '—'}</td>
                            <td className="py-2 px-2 text-gray-600">{item.decoration_type || '—'}</td>
                            <td className="py-2 px-2 text-gray-600 truncate max-w-[120px]">{item.graphic || '—'}</td>
                            <td className="py-2 px-2 text-gray-600 truncate max-w-[100px]">{item.line_1 || '—'}</td>
                            <td className="py-2 px-2 text-gray-600 truncate max-w-[100px]">{item.line_2 || '—'}</td>
                            <td className="py-2 px-2">
                              {item.processor_key ? (
                                <span className="text-xs px-1.5 py-0.5 bg-gray-100 rounded text-gray-600 font-mono">
                                  {item.processor_key}
                                </span>
                              ) : (
                                <span className="text-xs text-red-500">{item.error || 'none'}</span>
                              )}
                            </td>
                            <td className="py-2 px-2">
                              {item.status === 'complete' && item.svg_path ? (
                                <a href={svgPreviewUrl(item.id)} target="_blank" rel="noopener noreferrer"
                                  className="inline-block w-16 h-10 rounded border border-gray-200 overflow-hidden hover:border-indigo-400 transition-colors bg-white">
                                  <img src={svgPreviewUrl(item.id)} alt="SVG" className="w-full h-full object-contain" />
                                </a>
                              ) : item.status === 'error' ? (
                                <span className="text-xs text-red-400" title={item.error || ''}>✕</span>
                              ) : (
                                <span className="text-xs text-gray-300">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
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
    </div>
  )
}
