import React, { useState, useRef, useEffect, useCallback } from 'react'
import apiClient from '../api/client'

interface TableData {
  id: string
  table_number: string
  capacity: number
  section: string | null
  x: number
  y: number
  width: number
  height: number
  shape: 'rect' | 'circle'
}

interface DragState {
  tableId: string | null
  offsetX: number
  offsetY: number
}

const TABLE_SHAPES = [
  { shape: 'rect' as const, width: 80, height: 60, label: '4-Top' },
  { shape: 'rect' as const, width: 100, height: 70, label: '6-Top' },
  { shape: 'rect' as const, width: 60, height: 50, label: '2-Top' },
  { shape: 'circle' as const, width: 70, height: 70, label: 'Round' },
  { shape: 'rect' as const, width: 120, height: 60, label: 'Booth' },
  { shape: 'rect' as const, width: 160, height: 50, label: 'Bar' },
]

export default function FloorPlan() {
  const [tables, setTables] = useState<TableData[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [drag, setDrag] = useState<DragState | null>(null)
  const [editTable, setEditTable] = useState<TableData | null>(null)
  const canvasRef = useRef<HTMLDivElement>(null)

  useEffect(() => { loadTables() }, [])

  const loadTables = async () => {
    try {
      const res = await apiClient.get('/tables/')
      // Map tables with saved positions or defaults
      setTables(res.data.map((t: any, i: number) => ({
        id: t.id,
        table_number: t.table_number,
        capacity: t.capacity || 4,
        section: t.section,
        x: t.x || 50 + (i % 5) * 120,
        y: t.y || 50 + Math.floor(i / 5) * 100,
        width: t.capacity <= 2 ? 60 : t.capacity <= 4 ? 80 : 100,
        height: t.capacity <= 2 ? 50 : t.capacity <= 4 ? 60 : 70,
        shape: 'rect',
      })))
    } catch (err) {
      console.error('Failed to load tables', err)
    } finally {
      setLoading(false)
    }
  }

  const handleMouseDown = useCallback((e: React.MouseEvent, tableId: string) => {
    e.preventDefault()
    const table = tables.find(t => t.id === tableId)
    if (!table || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    setDrag({
      tableId,
      offsetX: e.clientX - rect.left - table.x,
      offsetY: e.clientY - rect.top - table.y,
    })
    setSelectedTable(tableId)
  }, [tables])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!drag || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    const x = Math.max(0, Math.min(e.clientX - rect.left - drag.offsetX, rect.width - 80))
    const y = Math.max(0, Math.min(e.clientY - rect.top - drag.offsetY, rect.height - 60))
    setTables(prev => prev.map(t =>
      t.id === drag.tableId ? { ...t, x: Math.round(x / 10) * 10, y: Math.round(y / 10) * 10 } : t
    ))
  }, [drag])

  const handleMouseUp = useCallback(() => {
    setDrag(null)
  }, [])

  const addTable = (shape: typeof TABLE_SHAPES[0]) => {
    const newTable: TableData = {
      id: `new-${Date.now()}`,
      table_number: `T${tables.length + 1}`,
      capacity: shape.label === '2-Top' ? 2 : shape.label === '6-Top' ? 6 : 4,
      section: null,
      x: 50,
      y: 50,
      width: shape.width,
      height: shape.height,
      shape: shape.shape,
    }
    setTables([...tables, newTable])
  }

  const deleteTable = (id: string) => {
    setTables(tables.filter(t => t.id !== id))
    setSelectedTable(null)
  }

  const savePositions = async () => {
    setSaving(true)
    try {
      // Save positions to backend (batch update)
      await Promise.all(tables.map(t =>
        apiClient.put(`/tables/${t.id}`, {
          x: t.x,
          y: t.y,
          table_number: t.table_number,
          section: t.section,
          capacity: t.capacity,
        }).catch(() => {})
      ))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="p-6 text-gray-500">Loading floor plan...</div>

  const selected = tables.find(t => t.id === selectedTable)

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Floor Plan Editor</h3>
        <div className="flex gap-2">
          <button onClick={savePositions} disabled={saving} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50 text-sm">
            {saving ? 'Saving...' : 'Save Layout'}
          </button>
        </div>
      </div>

      <div className="flex gap-4">
        {/* Table Palette */}
        <div className="w-48 bg-white rounded-lg shadow p-4">
          <h4 className="text-sm font-semibold mb-3 text-gray-600">Add Table</h4>
          <div className="space-y-2">
            {TABLE_SHAPES.map((shape, i) => (
              <button
                key={i}
                onClick={() => addTable(shape)}
                className="w-full p-2 bg-gray-50 rounded hover:bg-gray-100 text-sm text-left flex items-center gap-2"
              >
                <span className="text-lg">{shape.shape === 'circle' ? '⭕' : '⬜'}</span>
                <span>{shape.label}</span>
              </button>
            ))}
          </div>

          {/* Selected Table Properties */}
          {selected && (
            <div className="mt-6 pt-4 border-t">
              <h4 className="text-sm font-semibold mb-3 text-gray-600">Table Properties</h4>
              <div className="space-y-2">
                <div>
                  <label className="text-xs text-gray-500">Number</label>
                  <input
                    value={selected.table_number}
                    onChange={e => setTables(tables.map(t =>
                      t.id === selectedTable ? { ...t, table_number: e.target.value } : t
                    ))}
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Capacity</label>
                  <input
                    type="number"
                    value={selected.capacity}
                    onChange={e => setTables(tables.map(t =>
                      t.id === selectedTable ? { ...t, capacity: parseInt(e.target.value) || 4 } : t
                    ))}
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Section</label>
                  <input
                    value={selected.section || ''}
                    onChange={e => setTables(tables.map(t =>
                      t.id === selectedTable ? { ...t, section: e.target.value || null } : t
                    ))}
                    className="w-full px-2 py-1 border rounded text-sm"
                    placeholder="e.g. Main Hall"
                  />
                </div>
                <button
                  onClick={() => deleteTable(selectedTable)}
                  className="w-full mt-2 py-1 bg-red-50 text-red-600 rounded hover:bg-red-100 text-sm"
                >
                  Delete Table
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Canvas */}
        <div
          ref={canvasRef}
          className="flex-1 bg-white rounded-lg shadow relative overflow-hidden"
          style={{ height: 600, cursor: drag ? 'grabbing' : 'default' }}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {/* Grid */}
          <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }}>
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f0f0f0" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>

          {/* Tables */}
          {tables.map(table => (
            <div
              key={table.id}
              onMouseDown={e => handleMouseDown(e, table.id)}
              className={`absolute flex flex-col items-center justify-center text-center cursor-grab select-none transition-shadow ${
                selectedTable === table.id ? 'ring-2 ring-blue-500 shadow-lg' : 'hover:shadow-md'
              } ${table.shape === 'circle' ? 'rounded-full' : 'rounded-lg'}`}
              style={{
                left: table.x,
                top: table.y,
                width: table.width,
                height: table.height,
                backgroundColor: selectedTable === table.id ? '#EFF6FF' : '#F9FAFB',
                border: '2px solid #D1D5DB',
              }}
            >
              <span className="font-bold text-sm">{table.table_number}</span>
              <span className="text-xs text-gray-500">{table.capacity}p</span>
              {table.section && <span className="text-[10px] text-gray-400">{table.section}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
