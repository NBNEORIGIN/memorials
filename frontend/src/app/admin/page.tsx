'use client'

import { useState, useEffect, useCallback } from 'react'
import { ArrowLeft, Plus, Trash2, Pencil, X, Check, Palette, Box, Cpu, Tag, Search } from 'lucide-react'
import { fetchSkuMappings, fetchColours, fetchMemorialTypes, fetchProcessors } from '@/lib/api'

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

type Tab = 'skus' | 'colours' | 'types' | 'processors'

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'skus', label: 'SKU Mappings', icon: <Tag className="w-4 h-4" /> },
  { key: 'colours', label: 'Colours', icon: <Palette className="w-4 h-4" /> },
  { key: 'types', label: 'Memorial Types', icon: <Box className="w-4 h-4" /> },
  { key: 'processors', label: 'Processors', icon: <Cpu className="w-4 h-4" /> },
]

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('skus')
  const [skus, setSkus] = useState<SkuMapping[]>([])
  const [colours, setColours] = useState<Colour[]>([])
  const [types, setTypes] = useState<MemorialType[]>([])
  const [processors, setProcessors] = useState<Processor[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

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
                    <button onClick={() => setShowAddSku(!showAddSku)} className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                      <Plus className="w-4 h-4" /> Add SKU
                    </button>
                  </div>
                </div>

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
