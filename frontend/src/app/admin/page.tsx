'use client'

import { useState, useEffect, useCallback } from 'react'
import { ArrowLeft, Plus, Trash2, Pencil, X, Check, Palette, Box, Cpu, Tag, Search, LayoutGrid, Save, RotateCcw } from 'lucide-react'
import { fetchSkuMappings, fetchColours, fetchMemorialTypes, fetchProcessors, fetchLayouts, fetchLayoutDefaults, saveLayout, deleteLayout, layoutPreviewUrl, deleteSkuMapping, updateSkuMapping, importSkuCsv } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Colour = { id: number; name: string; hex_code: string | null; is_bw: boolean }
type MemorialType = { id: number; name: string; dimensions_mm: Record<string, number> | null; sort_order: number; is_active: boolean }
type Processor = { id: number; key: string; display_name: string; description: string | null; is_active: boolean }
type DecorationType = { id: number; name: string }
type Theme = { id: number; name: string }
type SkuMapping = {
  id: number; sku: string
  colour: Colour; memorial_type: MemorialType
  decoration_type: DecorationType | null; theme: Theme | null; processor: Processor
}

type Tab = 'skus' | 'colours' | 'types' | 'processors' | 'layouts'

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'skus', label: 'SKU Mappings', icon: <Tag className="w-4 h-4" /> },
  { key: 'colours', label: 'Colours', icon: <Palette className="w-4 h-4" /> },
  { key: 'types', label: 'Memorial Types', icon: <Box className="w-4 h-4" /> },
  { key: 'processors', label: 'Processors', icon: <Cpu className="w-4 h-4" /> },
  { key: 'layouts', label: 'Layouts', icon: <LayoutGrid className="w-4 h-4" /> },
]

type LayoutValues = {
  line1_y_mm: number; line2_y_mm: number; line3_y_mm: number;
  line1_size_pt: number; line2_size_pt: number; line3_size_pt: number;
  text_x_frac: number; font_family: string; text_fill: string;
  max_chars_line3: number; line3_max_rows: number;
  [key: string]: any;
}

const SLIDER_FIELDS: { key: keyof LayoutValues; label: string; min: number; max: number; step: number; unit: string; color: string }[] = [
  { key: 'line1_y_mm', label: 'Line 1 Y', min: 0, max: 120, step: 0.5, unit: 'mm', color: '#3b82f6' },
  { key: 'line2_y_mm', label: 'Line 2 Y', min: 0, max: 120, step: 0.5, unit: 'mm', color: '#10b981' },
  { key: 'line3_y_mm', label: 'Line 3 Y', min: 0, max: 120, step: 0.5, unit: 'mm', color: '#f59e0b' },
  { key: 'line1_size_pt', label: 'Line 1 Size', min: 4, max: 60, step: 0.5, unit: 'pt', color: '#3b82f6' },
  { key: 'line2_size_pt', label: 'Line 2 Size', min: 4, max: 80, step: 0.5, unit: 'pt', color: '#10b981' },
  { key: 'line3_size_pt', label: 'Line 3 Size', min: 4, max: 40, step: 0.5, unit: 'pt', color: '#f59e0b' },
  { key: 'text_x_frac', label: 'Text X', min: 0, max: 1, step: 0.01, unit: '', color: '#8b5cf6' },
  { key: 'max_chars_line3', label: 'Max Chars L3', min: 10, max: 80, step: 1, unit: '', color: '#6b7280' },
  { key: 'line3_max_rows', label: 'Max Rows L3', min: 1, max: 10, step: 1, unit: '', color: '#6b7280' },
]

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('skus')
  const [skus, setSkus] = useState<SkuMapping[]>([])
  const [colours, setColours] = useState<Colour[]>([])
  const [types, setTypes] = useState<MemorialType[]>([])
  const [processors, setProcessors] = useState<Processor[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  // Layout editor state
  const [layouts, setLayouts] = useState<any[]>([])
  const [editingProcessor, setEditingProcessor] = useState<string | null>(null)
  const [layoutVals, setLayoutVals] = useState<LayoutValues | null>(null)
  const [layoutDefaults, setLayoutDefaults] = useState<any>(null)
  const [layoutIsNew, setLayoutIsNew] = useState(true)
  const [layoutSaving, setLayoutSaving] = useState(false)
  const [layoutMsg, setLayoutMsg] = useState<string | null>(null)
  const [previewKey, setPreviewKey] = useState(0)
  const [sampleLine1, setSampleLine1] = useState('In Loving Memory Of')
  const [sampleLine2, setSampleLine2] = useState('John Smith')
  const [sampleLine3, setSampleLine3] = useState('1950 - 2024\nForever in our hearts')

  // SKU management
  const [deletingSkuId, setDeletingSkuId] = useState<number | null>(null)
  const [editingSkuId, setEditingSkuId] = useState<number | null>(null)
  const [editSku, setEditSku] = useState<any>(null)
  const [csvImporting, setCsvImporting] = useState(false)
  const [csvResult, setCsvResult] = useState<any>(null)
  const csvInputRef = useCallback((node: HTMLInputElement | null) => { if (node) node.value = '' }, [])

  // Add colour form
  const [showAddColour, setShowAddColour] = useState(false)
  const [newColour, setNewColour] = useState({ name: '', hex_code: '#000000', is_bw: false })

  // Add type form
  const [showAddType, setShowAddType] = useState(false)
  const [newType, setNewType] = useState({ name: '', width: '', height: '' })

  // Add SKU form
  const [showAddSku, setShowAddSku] = useState(false)
  const [newSku, setNewSku] = useState({ sku: '', colour_id: 0, memorial_type_id: 0, processor_id: 0, decoration_type_id: 0, theme_id: 0 })

  useEffect(() => {
    loadAll()
    fetchLayouts().then(setLayouts).catch(() => {})
  }, [])

  async function loadAll() {
    setLoading(true)
    try {
      const [s, c, t, p] = await Promise.all([fetchSkuMappings(), fetchColours(), fetchMemorialTypes(), fetchProcessors()])
      setSkus(s); setColours(c); setTypes(t); setProcessors(p)
    } catch {}
    setLoading(false)
  }

  async function addColour() {
    const res = await fetch(`${API_URL}/api/skus/colours`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newColour),
    })
    if (res.ok) {
      setShowAddColour(false)
      setNewColour({ name: '', hex_code: '#000000', is_bw: false })
      const c = await fetchColours(); setColours(c)
    }
  }

  async function addSku() {
    if (!newSku.sku || !newSku.colour_id || !newSku.memorial_type_id || !newSku.processor_id) return
    const payload: any = { sku: newSku.sku, colour_id: newSku.colour_id, memorial_type_id: newSku.memorial_type_id, processor_id: newSku.processor_id }
    if (newSku.decoration_type_id) payload.decoration_type_id = newSku.decoration_type_id
    if (newSku.theme_id) payload.theme_id = newSku.theme_id
    const res = await fetch(`${API_URL}/api/skus/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (res.ok) {
      setShowAddSku(false)
      setNewSku({ sku: '', colour_id: 0, memorial_type_id: 0, processor_id: 0, decoration_type_id: 0, theme_id: 0 })
      const s = await fetchSkuMappings(); setSkus(s)
    }
  }

  async function addType() {
    const dims = newType.width && newType.height ? { width: parseInt(newType.width), height: parseInt(newType.height) } : null
    const res = await fetch(`${API_URL}/api/skus/memorial-types`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newType.name, dimensions_mm: dims }),
    })
    if (res.ok) {
      setShowAddType(false)
      setNewType({ name: '', width: '', height: '' })
      const t = await fetchMemorialTypes(); setTypes(t)
    }
  }

  const filteredSkus = skus.filter(s => {
    if (!search) return true
    const q = search.toLowerCase()
    return s.sku.toLowerCase().includes(q) ||
      s.colour.name.toLowerCase().includes(q) ||
      s.memorial_type.name.toLowerCase().includes(q) ||
      s.processor.key.toLowerCase().includes(q) ||
      (s.decoration_type?.name.toLowerCase().includes(q)) ||
      (s.theme?.name.toLowerCase().includes(q))
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600"><ArrowLeft className="w-5 h-5" /></a>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Admin Panel</h1>
              <p className="text-xs text-gray-500">Manage SKUs, colours, types & processors</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span>{skus.length} SKUs</span>
            <span>&middot;</span>
            <span>{colours.length} colours</span>
            <span>&middot;</span>
            <span>{types.length} types</span>
            <span>&middot;</span>
            <span>{processors.length} processors</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-white rounded-lg border border-gray-200 p-1 w-fit">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors ${
                tab === t.key ? 'bg-indigo-600 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Loading...</div>
        ) : (
          <>
            {/* SKU Mappings Tab */}
            {tab === 'skus' && (
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <h2 className="font-semibold text-gray-800">SKU Mappings ({filteredSkus.length})</h2>
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="text" placeholder="Search SKUs..."
                        value={search} onChange={e => setSearch(e.target.value)}
                        className="pl-9 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-64"
                      />
                    </div>
                    <label className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                      <input type="file" accept=".csv" className="hidden" onChange={async (e) => {
                        const file = e.target.files?.[0]
                        if (!file) return
                        setCsvImporting(true); setCsvResult(null)
                        try {
                          const result = await importSkuCsv(file)
                          setCsvResult(result)
                          const s = await fetchSkuMappings(); setSkus(s)
                          await loadAll()
                        } catch (err: any) { setCsvResult({ error: err.message }) }
                        setCsvImporting(false)
                        e.target.value = ''
                      }} />
                      {csvImporting ? 'Importing...' : 'Import CSV'}
                    </label>
                    <button onClick={() => setShowAddSku(!showAddSku)} className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                      <Plus className="w-4 h-4" /> Add SKU
                    </button>
                  </div>
                </div>

                {csvResult && (
                  <div className={`px-5 py-3 border-b border-gray-100 flex items-center justify-between ${csvResult.error ? 'bg-red-50' : 'bg-green-50'}`}>
                    <p className={`text-sm ${csvResult.error ? 'text-red-700' : 'text-green-700'}`}>
                      {csvResult.error
                        ? `Import failed: ${csvResult.error}`
                        : `Imported ${csvResult.created} new SKUs (${csvResult.skipped} skipped)${csvResult.errors?.length ? ` · ${csvResult.errors.length} errors` : ''}`}
                    </p>
                    <button onClick={() => setCsvResult(null)} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
                  </div>
                )}

                {showAddSku && (
                  <div className="px-5 py-4 border-b border-gray-100 bg-gray-50/50">
                    <div className="flex flex-wrap items-end gap-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">SKU</label>
                        <input type="text" value={newSku.sku} onChange={e => setNewSku({ ...newSku, sku: e.target.value })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-44 font-mono" placeholder="e.g. OD045004_1" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Colour</label>
                        <select value={newSku.colour_id} onChange={e => setNewSku({ ...newSku, colour_id: Number(e.target.value) })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                          <option value={0}>Select...</option>
                          {colours.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
                        <select value={newSku.memorial_type_id} onChange={e => setNewSku({ ...newSku, memorial_type_id: Number(e.target.value) })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                          <option value={0}>Select...</option>
                          {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Processor</label>
                        <select value={newSku.processor_id} onChange={e => setNewSku({ ...newSku, processor_id: Number(e.target.value) })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                          <option value={0}>Select...</option>
                          {processors.map(p => <option key={p.id} value={p.id}>{p.display_name}</option>)}
                        </select>
                      </div>
                      <button onClick={addSku} disabled={!newSku.sku || !newSku.colour_id || !newSku.memorial_type_id || !newSku.processor_id}
                        className="flex items-center gap-1.5 px-4 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
                        <Check className="w-4 h-4" /> Save
                      </button>
                      <button onClick={() => setShowAddSku(false)} className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
                    </div>
                  </div>
                )}

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50/50">
                        <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase">SKU</th>
                        <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase">Colour</th>
                        <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase">Type</th>
                        <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase">Decoration</th>
                        <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase">Theme</th>
                        <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase">Processor</th>
                        <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase w-16"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSkus.map(s => (
                        <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-2 px-4 font-mono text-xs text-gray-800">{s.sku}</td>
                          <td className="py-2 px-4">
                            <div className="flex items-center gap-2">
                              {s.colour.hex_code && (
                                <span className="w-3 h-3 rounded-full border border-gray-200" style={{ backgroundColor: s.colour.hex_code }} />
                              )}
                              <span className="text-gray-700">{s.colour.name}</span>
                            </div>
                          </td>
                          <td className="py-2 px-4 text-gray-700">{s.memorial_type.name}</td>
                          <td className="py-2 px-4 text-gray-600">{s.decoration_type?.name || '—'}</td>
                          <td className="py-2 px-4 text-gray-600">{s.theme?.name || '—'}</td>
                          <td className="py-2 px-4">
                            <span className="text-xs px-2 py-0.5 bg-gray-100 rounded font-mono text-gray-600">
                              {s.processor.key}
                            </span>
                          </td>
                          <td className="py-2 px-4">
                            {deletingSkuId === s.id ? (
                              <div className="flex items-center gap-1">
                                <button onClick={async () => {
                                  try {
                                    await deleteSkuMapping(s.id)
                                    const updated = await fetchSkuMappings(); setSkus(updated)
                                  } catch {}
                                  setDeletingSkuId(null)
                                }} className="text-xs text-red-600 font-medium hover:text-red-700">Confirm</button>
                                <button onClick={() => setDeletingSkuId(null)} className="text-xs text-gray-400 hover:text-gray-600">Cancel</button>
                              </div>
                            ) : (
                              <button onClick={() => setDeletingSkuId(s.id)} className="text-gray-300 hover:text-red-500 transition-colors">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Colours Tab */}
            {tab === 'colours' && (
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <h2 className="font-semibold text-gray-800">Colours ({colours.length})</h2>
                  <button onClick={() => setShowAddColour(!showAddColour)} className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                    <Plus className="w-4 h-4" /> Add Colour
                  </button>
                </div>

                {showAddColour && (
                  <div className="px-5 py-4 border-b border-gray-100 bg-gray-50/50">
                    <div className="flex items-end gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
                        <input type="text" value={newColour.name} onChange={e => setNewColour({ ...newColour, name: e.target.value })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-40" placeholder="e.g. Bronze" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Hex</label>
                        <div className="flex items-center gap-2">
                          <input type="color" value={newColour.hex_code} onChange={e => setNewColour({ ...newColour, hex_code: e.target.value })}
                            className="w-8 h-8 rounded border border-gray-200 cursor-pointer" />
                          <input type="text" value={newColour.hex_code} onChange={e => setNewColour({ ...newColour, hex_code: e.target.value })}
                            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-24 font-mono" />
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="is_bw" checked={newColour.is_bw} onChange={e => setNewColour({ ...newColour, is_bw: e.target.checked })}
                          className="rounded border-gray-300" />
                        <label htmlFor="is_bw" className="text-sm text-gray-600">B&W</label>
                      </div>
                      <button onClick={addColour} disabled={!newColour.name} className="flex items-center gap-1.5 px-4 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
                        <Check className="w-4 h-4" /> Save
                      </button>
                      <button onClick={() => setShowAddColour(false)} className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 p-5">
                  {colours.map(c => (
                    <div key={c.id} className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
                      <span className="w-8 h-8 rounded-lg border border-gray-200 flex-shrink-0" style={{ backgroundColor: c.hex_code || '#ccc' }} />
                      <div>
                        <p className="text-sm font-medium text-gray-800">{c.name}</p>
                        <p className="text-xs text-gray-400 font-mono">{c.hex_code || 'no hex'} {c.is_bw ? '· B&W' : ''}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Memorial Types Tab */}
            {tab === 'types' && (
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <h2 className="font-semibold text-gray-800">Memorial Types ({types.length})</h2>
                  <button onClick={() => setShowAddType(!showAddType)} className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                    <Plus className="w-4 h-4" /> Add Type
                  </button>
                </div>

                {showAddType && (
                  <div className="px-5 py-4 border-b border-gray-100 bg-gray-50/50">
                    <div className="flex items-end gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
                        <input type="text" value={newType.name} onChange={e => setNewType({ ...newType, name: e.target.value })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-48" placeholder="e.g. Extra Large Stake" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Width (mm)</label>
                        <input type="number" value={newType.width} onChange={e => setNewType({ ...newType, width: e.target.value })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-24" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Height (mm)</label>
                        <input type="number" value={newType.height} onChange={e => setNewType({ ...newType, height: e.target.value })}
                          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-24" />
                      </div>
                      <button onClick={addType} disabled={!newType.name} className="flex items-center gap-1.5 px-4 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
                        <Check className="w-4 h-4" /> Save
                      </button>
                      <button onClick={() => setShowAddType(false)} className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
                    </div>
                  </div>
                )}

                <div className="divide-y divide-gray-100">
                  {types.map(t => (
                    <div key={t.id} className="flex items-center justify-between px-5 py-3 hover:bg-gray-50">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{t.name}</p>
                        {t.dimensions_mm && (
                          <p className="text-xs text-gray-400">{t.dimensions_mm.width}mm × {t.dimensions_mm.height}mm</p>
                        )}
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {t.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Layouts Tab */}
            {tab === 'layouts' && (
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="px-5 py-4 border-b border-gray-100">
                  <h2 className="font-semibold text-gray-800">Layout Editor</h2>
                  <p className="text-xs text-gray-400 mt-0.5">Adjust text positions, font sizes, and spacing per processor. Changes apply to all future SVG generation.</p>
                </div>

                <div className="grid grid-cols-12 divide-x divide-gray-100">
                  {/* Processor list */}
                  <div className="col-span-3 max-h-[600px] overflow-y-auto">
                    {processors.map(p => {
                      const hasLayout = layouts.some(l => l.processor_key === p.key)
                      return (
                        <button
                          key={p.id}
                          onClick={async () => {
                            setEditingProcessor(p.key)
                            setLayoutMsg(null)
                            try {
                              const defaults = await fetchLayoutDefaults(p.key)
                              setLayoutDefaults(defaults)
                              const existing = layouts.find(l => l.processor_key === p.key)
                              if (existing) {
                                setLayoutIsNew(false)
                                setLayoutVals({
                                  line1_y_mm: existing.line1_y_mm ?? defaults.line1_y_mm,
                                  line2_y_mm: existing.line2_y_mm ?? defaults.line2_y_mm,
                                  line3_y_mm: existing.line3_y_mm ?? defaults.line3_y_mm,
                                  line1_size_pt: existing.line1_size_pt ?? defaults.line1_size_pt,
                                  line2_size_pt: existing.line2_size_pt ?? defaults.line2_size_pt,
                                  line3_size_pt: existing.line3_size_pt ?? defaults.line3_size_pt,
                                  text_x_frac: existing.text_x_frac ?? defaults.text_x_frac,
                                  font_family: existing.font_family ?? defaults.font_family,
                                  text_fill: existing.text_fill ?? defaults.text_fill,
                                  max_chars_line3: existing.max_chars_line3 ?? defaults.max_chars_line3,
                                  line3_max_rows: existing.line3_max_rows ?? defaults.line3_max_rows,
                                })
                              } else {
                                setLayoutIsNew(true)
                                setLayoutVals({
                                  line1_y_mm: defaults.line1_y_mm,
                                  line2_y_mm: defaults.line2_y_mm,
                                  line3_y_mm: defaults.line3_y_mm,
                                  line1_size_pt: defaults.line1_size_pt,
                                  line2_size_pt: defaults.line2_size_pt,
                                  line3_size_pt: defaults.line3_size_pt,
                                  text_x_frac: defaults.text_x_frac,
                                  font_family: defaults.font_family,
                                  text_fill: defaults.text_fill,
                                  max_chars_line3: defaults.max_chars_line3,
                                  line3_max_rows: defaults.line3_max_rows,
                                })
                              }
                              setPreviewKey(k => k + 1)
                            } catch {}
                          }}
                          className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                            editingProcessor === p.key ? 'bg-indigo-50 border-l-2 border-l-indigo-500' : ''
                          }`}
                        >
                          <p className="text-sm font-medium text-gray-800">{p.display_name}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <p className="text-xs text-gray-400 font-mono">{p.key}</p>
                            {hasLayout && <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded">customised</span>}
                          </div>
                        </button>
                      )
                    })}
                  </div>

                  {/* Editor */}
                  <div className="col-span-9 p-5">
                    {!editingProcessor && (
                      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
                        Select a processor from the list to edit its layout
                      </div>
                    )}

                    {editingProcessor && layoutVals && layoutDefaults && (
                      <div className="space-y-5">
                        {/* Preview + controls */}
                        <div className="grid grid-cols-2 gap-5">
                          {/* Live SVG preview */}
                          <div>
                            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Live Preview</h3>
                            <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50 p-2">
                              <img
                                key={previewKey}
                                src={layoutPreviewUrl(editingProcessor, {
                                  line1_y_mm: layoutVals.line1_y_mm,
                                  line2_y_mm: layoutVals.line2_y_mm,
                                  line3_y_mm: layoutVals.line3_y_mm,
                                  line1_size_pt: layoutVals.line1_size_pt,
                                  line2_size_pt: layoutVals.line2_size_pt,
                                  line3_size_pt: layoutVals.line3_size_pt,
                                  text_x_frac: layoutVals.text_x_frac,
                                  font_family: layoutVals.font_family,
                                  text_fill: layoutVals.text_fill,
                                  line1: sampleLine1,
                                  line2: sampleLine2,
                                  line3: sampleLine3,
                                })}
                                alt="Layout preview"
                                className="w-full h-auto"
                              />
                            </div>
                            <div className="mt-2 text-xs text-gray-400">
                              Cell: {layoutDefaults.cell_width_mm}×{layoutDefaults.cell_height_mm}mm &middot;
                              Grid: {layoutDefaults.grid_cols}×{layoutDefaults.grid_rows} &middot;
                              Page: {layoutDefaults.page_width_mm}×{layoutDefaults.page_height_mm}mm
                            </div>
                            {/* Sample text inputs */}
                            <div className="mt-3 space-y-1.5">
                              <input type="text" value={sampleLine1} onChange={e => { setSampleLine1(e.target.value); setPreviewKey(k => k + 1) }}
                                className="w-full text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                                placeholder="Sample Line 1" />
                              <input type="text" value={sampleLine2} onChange={e => { setSampleLine2(e.target.value); setPreviewKey(k => k + 1) }}
                                className="w-full text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                                placeholder="Sample Line 2" />
                              <input type="text" value={sampleLine3} onChange={e => { setSampleLine3(e.target.value); setPreviewKey(k => k + 1) }}
                                className="w-full text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                                placeholder="Sample Line 3" />
                            </div>
                          </div>

                          {/* Sliders */}
                          <div className="space-y-3">
                            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide">Parameters</h3>
                            {SLIDER_FIELDS.map(f => (
                              <div key={f.key} className="space-y-0.5">
                                <div className="flex items-center justify-between">
                                  <label className="text-xs font-medium text-gray-600 flex items-center gap-1.5">
                                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: f.color }} />
                                    {f.label}
                                  </label>
                                  <div className="flex items-center gap-1">
                                    <input
                                      type="number"
                                      value={layoutVals[f.key]}
                                      onChange={e => {
                                        const v = parseFloat(e.target.value) || 0
                                        setLayoutVals({ ...layoutVals, [f.key]: v })
                                        setPreviewKey(k => k + 1)
                                      }}
                                      step={f.step}
                                      className="w-16 text-xs text-right border border-gray-200 rounded px-1.5 py-0.5 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-400"
                                    />
                                    {f.unit && <span className="text-[10px] text-gray-400">{f.unit}</span>}
                                  </div>
                                </div>
                                <input
                                  type="range"
                                  min={f.min} max={f.max} step={f.step}
                                  value={layoutVals[f.key]}
                                  onChange={e => {
                                    setLayoutVals({ ...layoutVals, [f.key]: parseFloat(e.target.value) })
                                    setPreviewKey(k => k + 1)
                                  }}
                                  className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-gray-200"
                                  style={{ accentColor: f.color }}
                                />
                              </div>
                            ))}

                            {/* Font family */}
                            <div className="space-y-0.5">
                              <label className="text-xs font-medium text-gray-600">Font Family</label>
                              <select
                                value={layoutVals.font_family}
                                onChange={e => {
                                  setLayoutVals({ ...layoutVals, font_family: e.target.value })
                                  setPreviewKey(k => k + 1)
                                }}
                                className="w-full text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                              >
                                {['Georgia', 'Times New Roman', 'Garamond', 'Palatino', 'Arial', 'Helvetica', 'Verdana', 'Trebuchet MS'].map(f => (
                                  <option key={f} value={f}>{f}</option>
                                ))}
                              </select>
                            </div>

                            {/* Text colour */}
                            <div className="space-y-0.5">
                              <label className="text-xs font-medium text-gray-600">Text Colour</label>
                              <div className="flex items-center gap-2">
                                <input type="color" value={layoutVals.text_fill === 'black' ? '#000000' : layoutVals.text_fill}
                                  onChange={e => {
                                    setLayoutVals({ ...layoutVals, text_fill: e.target.value })
                                    setPreviewKey(k => k + 1)
                                  }}
                                  className="w-7 h-7 rounded border border-gray-200 cursor-pointer" />
                                <input type="text" value={layoutVals.text_fill}
                                  onChange={e => {
                                    setLayoutVals({ ...layoutVals, text_fill: e.target.value })
                                    setPreviewKey(k => k + 1)
                                  }}
                                  className="w-24 text-xs border border-gray-200 rounded px-2 py-1 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-400" />
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center gap-3 pt-3 border-t border-gray-100">
                          <button
                            onClick={async () => {
                              setLayoutSaving(true)
                              setLayoutMsg(null)
                              try {
                                await saveLayout(editingProcessor, layoutVals, layoutIsNew)
                                setLayoutIsNew(false)
                                const updated = await fetchLayouts()
                                setLayouts(updated)
                                setLayoutMsg('Saved!')
                                setTimeout(() => setLayoutMsg(null), 2000)
                              } catch (e: any) {
                                setLayoutMsg(e.message || 'Save failed')
                              }
                              setLayoutSaving(false)
                            }}
                            disabled={layoutSaving}
                            className="flex items-center gap-1.5 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                          >
                            <Save className="w-4 h-4" />
                            {layoutSaving ? 'Saving...' : 'Save Layout'}
                          </button>

                          <button
                            onClick={() => {
                              if (layoutDefaults) {
                                setLayoutVals({
                                  line1_y_mm: layoutDefaults.line1_y_mm,
                                  line2_y_mm: layoutDefaults.line2_y_mm,
                                  line3_y_mm: layoutDefaults.line3_y_mm,
                                  line1_size_pt: layoutDefaults.line1_size_pt,
                                  line2_size_pt: layoutDefaults.line2_size_pt,
                                  line3_size_pt: layoutDefaults.line3_size_pt,
                                  text_x_frac: layoutDefaults.text_x_frac,
                                  font_family: layoutDefaults.font_family,
                                  text_fill: layoutDefaults.text_fill,
                                  max_chars_line3: layoutDefaults.max_chars_line3,
                                  line3_max_rows: layoutDefaults.line3_max_rows,
                                })
                                setPreviewKey(k => k + 1)
                              }
                            }}
                            className="flex items-center gap-1.5 px-4 py-2 text-sm border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                          >
                            <RotateCcw className="w-4 h-4" />
                            Reset to Defaults
                          </button>

                          {!layoutIsNew && (
                            <button
                              onClick={async () => {
                                try {
                                  await deleteLayout(editingProcessor)
                                  setLayoutIsNew(true)
                                  const updated = await fetchLayouts()
                                  setLayouts(updated)
                                  setLayoutMsg('Custom layout deleted — using defaults')
                                  setTimeout(() => setLayoutMsg(null), 2000)
                                } catch {}
                              }}
                              className="flex items-center gap-1.5 px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                              Delete Custom Layout
                            </button>
                          )}

                          {layoutMsg && (
                            <span className={`text-sm ${layoutMsg.includes('failed') ? 'text-red-600' : 'text-green-600'}`}>{layoutMsg}</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Processors Tab */}
            {tab === 'processors' && (
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="px-5 py-4 border-b border-gray-100">
                  <h2 className="font-semibold text-gray-800">Processors ({processors.length})</h2>
                  <p className="text-xs text-gray-400 mt-0.5">SVG generation processors registered in the backend</p>
                </div>
                <div className="divide-y divide-gray-100">
                  {processors.map(p => (
                    <div key={p.id} className="flex items-center justify-between px-5 py-3 hover:bg-gray-50">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{p.display_name}</p>
                        <p className="text-xs text-gray-400 font-mono">{p.key}</p>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded ${p.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                        {p.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
